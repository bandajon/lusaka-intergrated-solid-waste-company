from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app, make_response
import os
import pandas as pd
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import json
import traceback
from .utils.db_manager import DatabaseManager
from .utils.plate_cleaner import clean_license_plate, batch_clean_plates
from .utils.company_unifier import CompanyUnifier

main_bp = Blueprint('main', __name__)
db_manager = DatabaseManager()

@main_bp.route('/')
def index():
    """Main dashboard page"""
    # Get table counts for the dashboard
    table_counts = db_manager.get_table_counts_dict()
    return render_template('index.html', table_counts=table_counts)

@main_bp.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handle file uploads"""
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser also submits an empty part
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            
            # Create upload folder if it doesn't exist
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            flash(f'File {filename} uploaded successfully!', 'success')
            
            # Redirect to appropriate page based on file type
            if filename.endswith('.csv'):
                return redirect(url_for('main.preview_data', filename=unique_filename))
            else:
                return redirect(url_for('main.index'))
    
    return render_template('upload.html')

@main_bp.route('/preview/<filename>')
def preview_data(filename):
    """Preview uploaded data"""
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    try:
        df = pd.read_csv(file_path)
        # Get only first 100 rows for preview
        preview_data = df.head(100).to_dict('records')
        columns = df.columns.tolist()
        
        # Basic stats
        row_count = len(df)
        tables = db_manager.list_tables()
        
        return render_template('preview.html', 
                               preview_data=preview_data, 
                               columns=columns,
                               row_count=row_count,
                               filename=filename,
                               tables=tables)
    except Exception as e:
        flash(f'Error previewing file: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/clean/plates/<filename>', methods=['GET', 'POST'])
def clean_plates(filename):
    """Clean vehicle license plates"""
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    if request.method == 'POST':
        try:
            # Run the plate cleaning process
            cleaned_df = batch_clean_plates(file_path)
            
            # Save the cleaned data
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"cleaned_plates_{timestamp}.csv"
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)
            cleaned_df.to_csv(output_path, index=False)
            
            flash(f'Successfully cleaned {len(cleaned_df)} license plates', 'success')
            return redirect(url_for('main.preview_data', filename=output_filename))
        
        except Exception as e:
            flash(f'Error cleaning license plates: {str(e)}', 'danger')
            return redirect(url_for('main.preview_data', filename=filename))
    
    # GET request - show cleaning interface
    try:
        df = pd.read_csv(file_path)
        has_license_plates = 'license_plate' in df.columns
        
        # If no license_plate column, notify the user
        if not has_license_plates:
            flash('This file does not have a license_plate column and cannot be processed', 'warning')
            return redirect(url_for('main.preview_data', filename=filename))
        
        # Display some examples of what would be cleaned
        sample_plates = df['license_plate'].dropna().head(10).tolist()
        cleaned_samples = []
        
        for plate in sample_plates:
            cleaned_samples.append({
                'original': plate,
                'cleaned': clean_license_plate(plate)
            })
        
        return render_template('clean_plates.html', 
                               filename=filename,
                               sample_count=len(df),
                               cleaned_samples=cleaned_samples)
        
    except Exception as e:
        flash(f'Error preparing cleaning interface: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/db/import', methods=['GET', 'POST'])
def db_import():
    """Import data to database"""
    if request.method == 'POST':
        # Get parameters
        filename = request.form.get('filename')
        table = request.form.get('table')
        
        if not filename or not table:
            flash('Missing required parameters', 'danger')
            return redirect(url_for('main.index'))
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        try:
            # Import to the selected table
            result = db_manager.import_table(table, file_path)
            
            if result:
                flash(f'Successfully imported data to {table} table', 'success')
            else:
                flash(f'Error importing data to {table} table', 'danger')
                
            return redirect(url_for('main.index'))
        
        except Exception as e:
            flash(f'Error during import: {str(e)}', 'danger')
            return redirect(url_for('main.index'))
    
    # GET request - select file to import
    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)
    
    # Get list of CSV files in upload directory
    csv_files = [f for f in os.listdir(upload_dir) if f.endswith('.csv')]
    csv_files.sort(reverse=True)  # Most recent first
    
    # Get list of tables
    tables = db_manager.list_tables()
    
    return render_template('db_import.html', csv_files=csv_files, tables=tables)

@main_bp.route('/db/export/<table>')
def db_export(table):
    """Export data from database"""
    try:
        # Export the selected table
        filename = db_manager.export_table(table)
        
        if filename:
            flash(f'Successfully exported {table} table to {filename}', 'success')
            # Offer the file for download
            return send_file(filename, as_attachment=True)
        else:
            flash(f'Error exporting {table} table', 'danger')
            return redirect(url_for('main.index'))
    
    except Exception as e:
        flash(f'Error during export: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/db/truncate/<table>', methods=['POST'])
def db_truncate(table):
    """Truncate a database table"""
    try:
        # Confirm truncation
        confirmation = request.form.get('confirmation')
        if confirmation != 'CONFIRM':
            flash('Incorrect confirmation text provided. Table not truncated.', 'danger')
            return redirect(url_for('main.index'))
        
        # Truncate the selected table
        result = db_manager.truncate_table(table)
        
        if result:
            flash(f'Successfully truncated {table} table', 'success')
        else:
            flash(f'Error truncating {table} table', 'danger')
            
        return redirect(url_for('main.index'))
    
    except Exception as e:
        flash(f'Error during truncation: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/db/view/<table>')
def db_view(table):
    """View data from a table"""
    try:
        # Get data from the table
        df = db_manager.get_table_data(table)
        
        if df is not None:
            # Convert to dict for template rendering
            data = df.head(1000).to_dict('records')  # Limit to 1000 rows for performance
            columns = df.columns.tolist()
            row_count = len(df)
            
            return render_template('table_view.html', 
                                   table=table,
                                   data=data, 
                                   columns=columns,
                                   row_count=row_count,
                                   total_rows=len(df))
        else:
            flash(f'Error viewing {table} table', 'danger')
            return redirect(url_for('main.index'))
    
    except Exception as e:
        flash(f'Error viewing table: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/db/stats')
def db_stats():
    """Database statistics"""
    try:
        # Get table counts
        table_counts = db_manager.get_table_counts_dict()
        
        # Get additional stats if available
        stats = {
            'total_records': sum(table_counts.values()),
            'tables': table_counts
        }
        
        return render_template('db_stats.html', stats=stats)
    
    except Exception as e:
        flash(f'Error getting database statistics: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/analytics')
def analytics_dashboard():
    """Redirect to the standalone analytics dashboard"""
    # Redirect to the standalone dashboard running on port 5006
    return redirect('http://localhost:5006/')

@main_bp.route('/companies/unify')
def company_unify():
    """Company unification tool main page"""
    try:
        unifier = CompanyUnifier()
        success = unifier.load_companies_from_db()
        
        if not success:
            flash('Unable to load companies from database', 'danger')
            return redirect(url_for('main.index'))
        
        # Find duplicate groups
        duplicate_groups = unifier.find_duplicate_groups()
        summary = unifier.get_duplicate_summary()
        
        return render_template('company_unify.html', 
                             duplicate_groups=duplicate_groups,
                             summary=summary)
    
    except Exception as e:
        flash(f'Error loading company unification tool: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/companies/unify/execute', methods=['POST'])
def execute_company_merge():
    """Execute company merge based on user decisions"""
    try:
        merge_decisions = request.json
        
        if not merge_decisions:
            return jsonify({'success': False, 'message': 'No merge decisions provided'})
        
        print(f"📋 Received merge decisions: {len(merge_decisions)} groups")
        print(f"📋 Decision data: {json.dumps(merge_decisions, indent=2)}")
        
        # Validate the merge decisions format
        for i, decision in enumerate(merge_decisions):
            required_fields = ['group_id', 'action', 'merge_to_id', 'merge_name']
            missing_fields = [field for field in required_fields if field not in decision]
            if missing_fields:
                return jsonify({
                    'success': False, 
                    'message': f'Missing required fields in decision {i+1}: {missing_fields}'
                })
        
        print("✅ Merge decisions validation passed")
        
        unifier = CompanyUnifier()
        print("✅ CompanyUnifier initialized")
        
        success, message = unifier.merge_companies(merge_decisions)
        print(f"📊 Merge result: success={success}, message={message}")
        
        return jsonify({'success': success, 'message': message})
    
    except Exception as e:
        error_msg = f'Error executing merge: {str(e)}'
        print(f"❌ Exception in execute_company_merge: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': error_msg})

@main_bp.route('/companies/search/<pattern>')
def search_companies_by_pattern(pattern):
    """Search for companies matching a pattern"""
    try:
        unifier = CompanyUnifier()
        unifier.load_companies_from_db()
        
        matching_companies = unifier.get_companies_by_pattern(pattern)
        
        return jsonify({
            'success': True,
            'pattern': pattern,
            'companies': matching_companies,
            'count': len(matching_companies)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error searching companies: {str(e)}'})

@main_bp.route('/health')
def health_check():
    """Simple health check endpoint"""
    try:
        # Test database connection
        db_status = 'unknown'
        try:
            table_counts = db_manager.get_table_counts_dict()
            db_status = 'connected' if table_counts else 'no_data'
        except Exception:
            db_status = 'disconnected'
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': db_status,
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@main_bp.route('/companies/unify/report')
def export_company_report():
    """Export company duplicate analysis report"""
    try:
        unifier = CompanyUnifier()
        unifier.load_companies_from_db()
        unifier.find_duplicate_groups()
        
        report_path = unifier.export_duplicate_report()
        
        if report_path:
            return send_file(report_path, as_attachment=True)
        else:
            flash('Error generating report', 'danger')
            return redirect(url_for('main.company_unify'))
    
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'danger')
        return redirect(url_for('main.company_unify'))

@main_bp.route('/companies/unify/test', methods=['GET', 'POST'])
def test_company_merge():
    """Test endpoint for company merge functionality"""
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'message': 'Company merge endpoint is working',
            'timestamp': datetime.now().isoformat()
        })
    
    elif request.method == 'POST':
        try:
            data = request.json or {}
            return jsonify({
                'success': True,
                'message': 'POST request received successfully',
                'received_data': data,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error processing POST: {str(e)}',
                'timestamp': datetime.now().isoformat()
            })
