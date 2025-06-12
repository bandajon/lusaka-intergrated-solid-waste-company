import os
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import uuid
import json
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session

# Import the location unifier module
import location_unifier
from database.database_connection import get_db_engine, TABLES

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_location_unifier')

# Create static folders for downloads
static_dir = Path(__file__).parent / 'static'
static_dir.mkdir(exist_ok=True)
downloads_dir = static_dir / 'downloads'
downloads_dir.mkdir(exist_ok=True)

# Add context processor to provide 'now' variable to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Global variables to store state
engine = None
current_group_idx = 0
total_groups = 0
decisions = {}
unification_passes = 0
original_locations = []  # Keep track of original locations for multiple passes

@app.route('/')
def index():
    """Landing page with options to start unification or load existing data"""
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_unification():
    """Start the location unification process"""
    global engine, current_group_idx, total_groups, unification_passes, original_locations
    
    try:
        # Get the similarity threshold from the form
        threshold = float(request.form.get('threshold', 0.7))
        
        # Get the input file from the form
        input_file = request.form.get('input_file', 'JICA TEAM 2025.csv')
        
        # Check if this is a new unification or continuing
        if engine is None or unification_passes == 0:
            # Initialize the engine
            engine = location_unifier.LocationUnificationEngine(similarity_threshold=threshold)
            
            # Extract locations
            engine.extract_locations_from_weigh_events(input_file)
            
            # Store original locations for future passes
            original_locations = engine.locations.copy()
            
            # First pass
            unification_passes = 1
        else:
            # Continuing with another pass - keep existing decisions
            logger.info(f"Starting unification pass #{unification_passes + 1}")
            
            # Apply previous decisions to get updated locations
            updated_locations = apply_previous_decisions()
            
            # Create a new engine with the updated locations
            engine = location_unifier.LocationUnificationEngine(similarity_threshold=threshold)
            engine.locations = updated_locations
            
            # Increment pass counter
            unification_passes += 1
        
        # Find duplicates
        engine.find_duplicates_with_blocking(prefix_length=2)
        
        # Set initial state
        current_group_idx = 0
        total_groups = len(engine.duplicate_groups)
        
        flash(f"Pass #{unification_passes}: Loaded {len(engine.locations)} locations and found {total_groups} potential duplicate groups.", "success")
        
        if total_groups > 0:
            return redirect(url_for('review_group', group_id=0))
        else:
            flash("No more duplicate groups found! You can now write to the database or continue with a different threshold.", "warning")
            return redirect(url_for('complete_review'))
            
    except Exception as e:
        logger.error(f"Error starting unification: {e}")
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('index'))

def apply_previous_decisions():
    """Apply previously made decisions to create updated location list"""
    global engine
    
    if not engine or not engine.decisions:
        return original_locations.copy()
    
    # Create a mapping of location IDs to their unified names
    location_mapping = {}
    unified_locations = []
    
    # First pass to build the mapping
    for group_id, decision in engine.decisions.items():
        if decision.get('action') == 'merge':
            unified_name = decision.get('unified_name')
            for loc_info in decision.get('locations', []):
                location_mapping[loc_info['id']] = unified_name
    
    # Create updated locations list
    processed_ids = set(location_mapping.keys())
    location_counts = {}
    
    # Add locations that aren't part of any merge decision (unchanged)
    for loc in engine.locations:
        if loc.id not in processed_ids:
            # Keep as is
            unified_locations.append(loc)
        else:
            # Count occurrences for unified locations
            unified_name = location_mapping[loc.id]
            if unified_name in location_counts:
                location_counts[unified_name] += loc.count
            else:
                location_counts[unified_name] = loc.count
    
    # Create unified location objects
    for unified_name, count in location_counts.items():
        unified_loc = location_unifier.Location(
            id=str(uuid.uuid4()),
            name=unified_name,
            count=count
        )
        unified_locations.append(unified_loc)
    
    logger.info(f"Applied {len(engine.decisions)} decisions, resulting in {len(unified_locations)} locations")
    return unified_locations

@app.route('/review/<int:group_id>')
def review_group(group_id):
    """Review a specific duplicate group"""
    global engine, current_group_idx, total_groups
    
    if engine is None or total_groups == 0:
        flash("No unification process is active. Please start a new one.", "warning")
        return redirect(url_for('index'))
    
    # Ensure valid group index
    group_id = max(0, min(group_id, total_groups - 1))
    current_group_idx = group_id
    
    # Get the current group
    group = engine.duplicate_groups[group_id]
    
    # Get all locations in the group
    locations = []
    
    # Add main location
    main_location = {
        'id': group.main_location.id,
        'name': group.main_location.name,
        'count': group.main_location.count,
        'excluded': group.is_location_excluded(group.main_location.id),
        'is_main': True
    }
    locations.append(main_location)
    
    # Add similar locations
    for match in group.similar_locations:
        location = {
            'id': match.location2.id,
            'name': match.location2.name,
            'count': match.location2.count,
            'similarity': round(match.score, 2),
            'excluded': group.is_location_excluded(match.location2.id),
            'is_main': False
        }
        locations.append(location)
    
    # Get suggested merge name
    suggested_name = group.get_merge_name()
    
    # Check if this group has a decision already
    has_decision = group.group_id in engine.decisions
    decision_type = engine.decisions.get(group.group_id, {}).get('action', '') if has_decision else ''
    
    return render_template(
        'review.html',
        group_id=group_id,
        total_groups=total_groups,
        locations=locations,
        suggested_name=suggested_name,
        custom_name=group.custom_merge_name,
        has_decision=has_decision,
        decision_type=decision_type,
        pass_number=unification_passes
    )

@app.route('/toggle_exclude', methods=['POST'])
def toggle_exclude():
    """Toggle exclusion status of a location"""
    global engine, current_group_idx
    
    if engine is None:
        return jsonify({'success': False, 'error': 'No active session'})
    
    try:
        location_id = request.form.get('location_id')
        group_id = int(request.form.get('group_id', current_group_idx))
        
        # Ensure valid group index
        group_id = max(0, min(group_id, len(engine.duplicate_groups) - 1))
        
        # Get the group
        group = engine.duplicate_groups[group_id]
        
        # Toggle exclusion
        group.toggle_exclude(location_id)
        
        # Update suggested merge
        if group.get_mergeable_locations():
            group.suggested_merge = max(group.get_mergeable_locations(), key=lambda loc: loc.count)
        
        return jsonify({
            'success': True, 
            'excluded': group.is_location_excluded(location_id),
            'suggested_name': group.get_merge_name()
        })
        
    except Exception as e:
        logger.error(f"Error toggling exclusion: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/update_merge_name', methods=['POST'])
def update_merge_name():
    """Update the custom merge name for a group"""
    global engine, current_group_idx
    
    if engine is None:
        return jsonify({'success': False, 'error': 'No active session'})
    
    try:
        merge_name = request.form.get('merge_name')
        group_id = int(request.form.get('group_id', current_group_idx))
        
        # Ensure valid group index
        group_id = max(0, min(group_id, len(engine.duplicate_groups) - 1))
        
        # Get the group
        group = engine.duplicate_groups[group_id]
        
        # Update custom name
        if merge_name and merge_name.strip():
            group.custom_merge_name = merge_name.strip()
        else:
            group.custom_merge_name = None
        
        return jsonify({
            'success': True, 
            'merge_name': group.get_merge_name()
        })
        
    except Exception as e:
        logger.error(f"Error updating merge name: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/make_decision', methods=['POST'])
def make_decision():
    """Record a decision for the current group"""
    global engine, current_group_idx
    
    if engine is None:
        flash("No unification process is active. Please start a new one.", "warning")
        return redirect(url_for('index'))
    
    try:
        action = request.form.get('action')
        group_id = int(request.form.get('group_id', current_group_idx))
        next_url = request.form.get('next_url', '')
        
        # Ensure valid group index
        group_id = max(0, min(group_id, len(engine.duplicate_groups) - 1))
        
        # Get the group
        group = engine.duplicate_groups[group_id]
        
        if action == 'merge':
            # Check if we have enough locations to merge
            mergeable = group.get_mergeable_locations()
            if len(mergeable) <= 1:
                flash("Cannot merge: need at least 2 selected locations", "danger")
                return redirect(url_for('review_group', group_id=group_id))
                
            # Record the decision
            engine.decisions[group.group_id] = {
                'action': 'merge',
                'unified_name': group.get_merge_name(),
                'locations': [{'id': loc.id, 'name': loc.name} for loc in mergeable],
                'excluded': list(group.excluded_locations)
            }
            
            flash(f"Merged {len(mergeable)} locations as '{group.get_merge_name()}'", "success")
            
        elif action == 'skip':
            # Record skip decision
            engine.decisions[group.group_id] = {
                'action': 'skip'
            }
            
            flash("Skipped this group", "info")
        
        # Determine where to go next
        if next_url == 'next' and group_id < len(engine.duplicate_groups) - 1:
            return redirect(url_for('review_group', group_id=group_id + 1))
        elif next_url == 'prev' and group_id > 0:
            return redirect(url_for('review_group', group_id=group_id - 1))
        elif next_url == 'complete':
            return redirect(url_for('complete_review'))
        else:
            # Stay on the same page
            return redirect(url_for('review_group', group_id=group_id))
            
    except Exception as e:
        logger.error(f"Error making decision: {e}")
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('review_group', group_id=current_group_idx))

@app.route('/complete')
def complete_review():
    """Complete the review and show the summary"""
    global engine, unification_passes
    
    if engine is None:
        flash("No unification process is active. Please start a new one.", "warning")
        return redirect(url_for('index'))
    
    # Calculate statistics
    total_groups = len(engine.duplicate_groups)
    decided_groups = len(engine.decisions)
    merge_decisions = sum(1 for d in engine.decisions.values() if d.get('action') == 'merge')
    skip_decisions = sum(1 for d in engine.decisions.values() if d.get('action') == 'skip')
    
    # Apply decisions to get the current unified locations
    updated_locations = apply_previous_decisions()
    original_location_count = len(original_locations)
    unified_location_count = len(updated_locations)
    reduction = original_location_count - unified_location_count
    
    # Prepare data for rendering
    summary = {
        'total_groups': total_groups,
        'decided_groups': decided_groups,
        'merge_decisions': merge_decisions,
        'skip_decisions': skip_decisions,
        'undecided_groups': total_groups - decided_groups,
        'pass_number': unification_passes,
        'original_locations': original_location_count,
        'unified_locations': unified_location_count,
        'reduction': reduction,
        'reduction_percent': round((reduction / original_location_count * 100), 1) if original_location_count > 0 else 0
    }
    
    return render_template('complete.html', summary=summary)

@app.route('/continue', methods=['POST'])
def continue_unification():
    """Start another pass of unification with adjusted threshold"""
    global engine, unification_passes
    
    if engine is None:
        flash("No unification process is active. Please start a new one.", "warning")
        return redirect(url_for('index'))
    
    # Get new threshold from form
    threshold = float(request.form.get('threshold', 0.7))
    
    # Start a new round
    flash(f"Starting another unification pass with threshold {threshold}", "info")
    
    # Apply decisions from previous passes
    updated_locations = apply_previous_decisions()
    
    # Create new engine with adjusted threshold and updated locations
    new_engine = location_unifier.LocationUnificationEngine(similarity_threshold=threshold)
    new_engine.locations = updated_locations
    
    # Keep decisions from previous engine
    new_engine.decisions = engine.decisions.copy()
    
    # Update global engine
    engine = new_engine
    
    # Find duplicates
    engine.find_duplicates_with_blocking(prefix_length=2)
    
    # Update state
    current_group_idx = 0
    total_groups = len(engine.duplicate_groups)
    unification_passes += 1
    
    if total_groups > 0:
        flash(f"Pass #{unification_passes}: Found {total_groups} potential duplicate groups with threshold {threshold}.", "success")
        return redirect(url_for('review_group', group_id=0))
    else:
        flash("No more duplicate groups found! Your locations are fully unified.", "success")
        return redirect(url_for('complete_review'))

@app.route('/export', methods=['POST'])
def export_data():
    """Export the unified locations and decisions"""
    global engine
    
    if engine is None:
        flash("No unification process is active. Please start a new one.", "warning")
        return redirect(url_for('index'))
    
    try:
        # Create output directory within static folder for web access
        output_dir = downloads_dir
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export decisions to JSON
        decisions_file = output_dir / f"location_decisions_{timestamp}.json"
        engine.save_decisions(str(decisions_file))
        
        # Export unified locations to CSV
        locations_file = output_dir / f"unified_locations_{timestamp}.csv"
        engine.export_unified_locations(str(locations_file))
        
        # Store the filenames in session for download links
        session['decisions_file'] = f"location_decisions_{timestamp}.json"
        session['locations_file'] = f"unified_locations_{timestamp}.csv"
        session['timestamp'] = timestamp
        
        flash(f"Files exported successfully and ready for download", "success")
        return redirect(url_for('complete_review'))
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('complete_review'))

@app.route('/download/<filename>')
def download_file(filename):
    """Download a file from the downloads directory"""
    try:
        file_path = downloads_dir / filename
        if file_path.exists():
            return send_file(file_path, as_attachment=True)
        else:
            flash(f"File not found: {filename}", "danger")
            return redirect(url_for('complete_review'))
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('complete_review'))

@app.route('/write_to_database', methods=['POST'])
def write_to_database():
    """Write unified locations to the database"""
    global engine
    
    if engine is None:
        flash("No unification process is active. Please start a new one.", "warning")
        return redirect(url_for('index'))
    
    try:
        # Apply decisions to get final unified locations
        updated_locations = apply_previous_decisions()
        
        # Connect to database
        db_engine = get_db_engine()
        
        # First, check if locations table exists
        with db_engine.connect() as conn:
            # Check if locations table exists
            check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'locations'
            );
            """
            exists = conn.execute(text(check_query)).scalar()
            
            if not exists:
                # Create locations table if it doesn't exist
                create_table_query = """
                CREATE TABLE locations (
                    location_id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    count INTEGER DEFAULT 0,
                    is_unified BOOLEAN DEFAULT FALSE,
                    original_names TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                conn.execute(text(create_table_query))
                logger.info("Created locations table in database")
        
        # Prepare data for database
        locations_data = []
        for loc in updated_locations:
            # Check if this is a unified location (part of a merge decision)
            is_unified = False
            original_names = None
            
            # Look through decisions to check if this is a merged location
            for decision in engine.decisions.values():
                if decision.get('action') == 'merge' and decision.get('unified_name') == loc.name:
                    is_unified = True
                    original_names = ", ".join([l['name'] for l in decision.get('locations', [])])
                    break
            
            locations_data.append({
                'location_id': loc.id,
                'name': loc.name,
                'count': loc.count,
                'is_unified': is_unified,
                'original_names': original_names
            })
        
        # Create DataFrame for bulk insert
        df = pd.DataFrame(locations_data)
        
        # Write to database with duplicate handling
        with db_engine.connect() as conn:
            # Write to temp table first
            df.to_sql('locations_temp', db_engine, if_exists='replace', index=False)
            
            # Insert into locations table with conflict handling
            merge_query = """
            INSERT INTO locations (location_id, name, count, is_unified, original_names)
            SELECT location_id, name, count, is_unified, original_names
            FROM locations_temp
            ON CONFLICT (name) DO UPDATE SET
                count = EXCLUDED.count,
                is_unified = EXCLUDED.is_unified,
                original_names = EXCLUDED.original_names,
                updated_at = CURRENT_TIMESTAMP
            """
            conn.execute(text(merge_query))
            
            # Clean up temp table
            conn.execute(text("DROP TABLE locations_temp"))
        
        # Also export the data to a downloadable CSV file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_export_file = f"db_export_locations_{timestamp}.csv"
        db_file_path = downloads_dir / db_export_file
        df.to_csv(db_file_path, index=False)
        
        # Store the filename in session for download link
        session['db_export_file'] = db_export_file
        session['timestamp'] = timestamp
        
        flash(f"Successfully wrote {len(locations_data)} locations to the database without creating duplicates", "success")
        return redirect(url_for('complete_review'))
        
    except Exception as e:
        logger.error(f"Error writing to database: {e}")
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('complete_review'))

@app.route('/search', methods=['POST'])
def search_locations():
    """Search for locations by name"""
    global engine
    
    if engine is None:
        flash("No unification process is active. Please start a new one.", "warning")
        return redirect(url_for('index'))
    
    try:
        search_term = request.form.get('search_term', '').lower()
        
        if not search_term:
            flash("Please enter a search term", "warning")
            return redirect(url_for('review_group', group_id=current_group_idx))
        
        # Search in all groups
        for i, group in enumerate(engine.duplicate_groups):
            for location in group.get_all_locations():
                if search_term in location.name.lower():
                    flash(f"Found match in group {i+1}", "success")
                    return redirect(url_for('review_group', group_id=i))
        
        flash(f"No location found containing '{search_term}'", "warning")
        return redirect(url_for('review_group', group_id=current_group_idx))
        
    except Exception as e:
        logger.error(f"Error searching locations: {e}")
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('review_group', group_id=current_group_idx))

@app.route('/reset', methods=['POST'])
def reset_unification():
    """Reset the unification process and start over"""
    global engine, current_group_idx, total_groups, decisions, unification_passes, original_locations
    
    # Reset all state variables
    engine = None
    current_group_idx = 0
    total_groups = 0
    decisions = {}
    unification_passes = 0
    original_locations = []
    
    flash("Unification process has been reset. You can start a new unification.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Create the templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5016) 