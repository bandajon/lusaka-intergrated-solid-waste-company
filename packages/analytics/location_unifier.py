import pandas as pd
import numpy as np
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Location:
    """Represents a location entry with standardized fields"""
    id: str
    name: str  # Original location name from the data
    cleaned_name: str = None
    count: int = 0  # Number of times this location appears in the data
    
    def __post_init__(self):
        if self.cleaned_name is None:
            self.cleaned_name = self.name.strip()

@dataclass
class SimilarityMatch:
    """Represents a similarity match between two locations"""
    location1: Location
    location2: Location
    score: float
    
    def __repr__(self):
        return f"'{self.location1.name}' <-> '{self.location2.name}' (score: {self.score:.3f})"

@dataclass
class DuplicateGroup:
    """Represents a group of potentially duplicate locations"""
    group_id: str
    main_location: Location
    similar_locations: List[SimilarityMatch]
    suggested_merge: Optional[Location] = None
    excluded_locations: Set[str] = field(default_factory=set)  # Locations to exclude from merge
    custom_merge_name: Optional[str] = None  # Custom name for merged location
    
    def get_all_locations(self) -> List[Location]:
        """Get all locations in the group"""
        result = [self.main_location]
        result.extend([match.location2 for match in self.similar_locations])
        return result
    
    def get_mergeable_locations(self) -> List[Location]:
        """Get locations to be merged (excluding excluded ones)"""
        all_locations = self.get_all_locations()
        return [l for l in all_locations if l.id not in self.excluded_locations]
    
    def is_location_excluded(self, location_id: str) -> bool:
        """Check if a location is excluded from merge"""
        return location_id in self.excluded_locations
    
    def toggle_exclude(self, location_id: str):
        """Toggle exclusion status of a location"""
        if location_id in self.excluded_locations:
            self.excluded_locations.remove(location_id)
        else:
            self.excluded_locations.add(location_id)
    
    def get_merge_name(self) -> str:
        """Get the name to use for the merged location"""
        if self.custom_merge_name:
            return self.custom_merge_name
        elif self.suggested_merge:
            return self.suggested_merge.name
        else:
            return self.get_mergeable_locations()[0].name if self.get_mergeable_locations() else ""

class LocationUnificationEngine:
    """High-performance location unification engine"""
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
        self.locations: List[Location] = []
        self.duplicate_groups: List[DuplicateGroup] = []
        self.decisions: Dict[str, Dict] = {}
        
    def extract_locations_from_weigh_events(self, file_path: str) -> List[Location]:
        """Extract unique locations from weigh events CSV file"""
        logger.info(f"Loading weigh events data from {file_path}")
        df = pd.read_csv(file_path, delimiter=',')
        
        # Extract locations from the Location column
        location_counts = {}
        
        for _, row in df.iterrows():
            # Skip rows with missing location
            if pd.isna(row.get('Location', '')):
                continue
                
            location = row['Location']
            # Skip recycle collections (marked with 'R')
            if isinstance(location, str) and location.strip().upper() == 'R':
                continue
                
            location = location.strip() if isinstance(location, str) else str(location)
            
            # Skip empty locations
            if not location:
                continue
                
            # Count occurrences
            if location in location_counts:
                location_counts[location] += 1
            else:
                location_counts[location] = 1
        
        # Create Location objects
        self.locations = []
        for loc_name, count in location_counts.items():
            location = Location(
                id=str(uuid.uuid4()),
                name=loc_name,
                count=count
            )
            self.locations.append(location)
        
        logger.info(f"Extracted {len(self.locations)} unique locations")
        return self.locations
    
    def load_csv(self, file_path: str) -> pd.DataFrame:
        """Load locations from a previously exported CSV file"""
        logger.info(f"Loading location data from {file_path}")
        df = pd.read_csv(file_path, delimiter=',')
        
        # Convert to Location objects
        self.locations = []
        for _, row in df.iterrows():
            location = Location(
                id=row['location_id'],
                name=row['name'],
                count=row.get('count', 0)
            )
            self.locations.append(location)
        
        logger.info(f"Loaded {len(self.locations)} locations")
        return df
    
    def calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two location names with enhanced matching"""
        # Normalize names
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()
        
        # Check if one is a prefix of another
        if n1.startswith(n2) or n2.startswith(n1):
            # Give higher similarity score for prefix matches
            # Calculate length ratio to adjust score
            min_len = min(len(n1), len(n2))
            max_len = max(len(n1), len(n2))
            length_ratio = min_len / max_len if max_len > 0 else 0
            prefix_similarity = 0.8 + (0.2 * length_ratio)  # Base 0.8 plus adjustment
        else:
            prefix_similarity = 0
        
        # Multiple similarity metrics
        seq_similarity = SequenceMatcher(None, n1, n2).ratio()
        fuzzy_ratio = fuzz.ratio(n1, n2) / 100
        token_sort_ratio = fuzz.token_sort_ratio(n1, n2) / 100
        token_set_ratio = fuzz.token_set_ratio(n1, n2) / 100
        
        # Weighted average with prefix consideration
        return max(
            (seq_similarity * 0.2) + (fuzzy_ratio * 0.2) + 
            (token_sort_ratio * 0.3) + (token_set_ratio * 0.3),
            prefix_similarity  # Ensure prefix matches get priority
        )
    
    def prefix_block_locations(self, locations, prefix_length=2):
        """Block locations by their name prefix for more efficient comparison"""
        blocks = {}
        for location in locations:
            # Get the first few characters as the block key
            prefix = location.cleaned_name[:prefix_length].lower() if len(location.cleaned_name) >= prefix_length else location.cleaned_name.lower()
            
            if prefix not in blocks:
                blocks[prefix] = []
            blocks[prefix].append(location)
        
        return blocks
    
    def find_duplicates_with_blocking(self, prefix_length=2):
        """Find duplicate location groups using blocking for efficiency"""
        logger.info(f"Finding duplicate groups with prefix blocking (length={prefix_length})...")
        
        self.duplicate_groups = []
        processed = set()
        
        # Create blocks
        blocks = self.prefix_block_locations(self.locations, prefix_length)
        
        # Process each block
        for block_key, block_locations in blocks.items():
            if len(block_locations) <= 1:
                continue  # Skip blocks with only one location
                
            for i, location1 in enumerate(block_locations):
                if location1.id in processed:
                    continue
                    
                similar_matches = []
                
                for j, location2 in enumerate(block_locations):
                    if i != j and location2.id not in processed:
                        similarity = self.calculate_similarity(location1.cleaned_name, location2.cleaned_name)
                        
                        if similarity > self.similarity_threshold:
                            match = SimilarityMatch(location1, location2, similarity)
                            similar_matches.append(match)
                            processed.add(location2.id)
                
                if similar_matches:
                    group_id = f"group_{len(self.duplicate_groups)}"
                    group = DuplicateGroup(
                        group_id=group_id,
                        main_location=location1,
                        similar_locations=similar_matches
                    )
                    group.suggested_merge = self._suggest_merge(group)
                    self.duplicate_groups.append(group)
                    processed.add(location1.id)
        
        logger.info(f"Found {len(self.duplicate_groups)} duplicate groups")
        return self.duplicate_groups
    
    def _suggest_merge(self, group: DuplicateGroup) -> Location:
        """Suggest the main location for merging based on frequency and name quality"""
        locations = group.get_all_locations()
        
        # First criteria: frequency (number of occurrences)
        most_frequent = max(locations, key=lambda loc: loc.count)
        
        # Second criteria: name quality (length, clarity)
        # For now, we'll just use the longest name as a heuristic for most descriptive
        longest_name = max(locations, key=lambda loc: len(loc.cleaned_name.strip()))
        
        # If the most frequent is also reasonably descriptive, use it
        if most_frequent.count > 2 * sum(loc.count for loc in locations if loc.id != most_frequent.id) / len(locations):
            return most_frequent
        else:
            # Otherwise use the longest (most descriptive) name
            return longest_name
    
    def export_decisions(self) -> dict:
        """Export the unification decisions"""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'groups': []
        }
        
        for group in self.duplicate_groups:
            if group.group_id in self.decisions:
                continue  # Skip groups that have been explicitly decided on
                
            mergeable = group.get_mergeable_locations()
            if len(mergeable) <= 1:
                continue  # Skip groups with only one location (not a merge)
                
            group_data = {
                'group_id': group.group_id,
                'merge_name': group.get_merge_name(),
                'locations': [
                    {
                        'id': loc.id,
                        'name': loc.name,
                        'count': loc.count,
                        'excluded': group.is_location_excluded(loc.id)
                    }
                    for loc in group.get_all_locations()
                ]
            }
            
            export_data['groups'].append(group_data)
            
        # Add explicit decisions
        export_data['decisions'] = self.decisions
            
        return export_data
        
    def save_decisions(self, output_path: str):
        """Save the unification decisions to a JSON file"""
        export_data = self.export_decisions()
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
            
        logger.info(f"Saved unification decisions to {output_path}")
    
    def export_unified_locations(self, output_path: str):
        """Export unified locations to a CSV file"""
        # Create a mapping of original location IDs to unified location names
        location_mapping = {}
        
        # Process each group
        for group in self.duplicate_groups:
            mergeable = group.get_mergeable_locations()
            if len(mergeable) <= 1:
                continue
                
            unified_name = group.get_merge_name()
            for loc in mergeable:
                location_mapping[loc.id] = unified_name
        
        # Create a list of unified locations
        unified_locations = []
        
        # Add locations that aren't part of any group
        processed_ids = set(location_mapping.keys())
        for loc in self.locations:
            if loc.id not in processed_ids:
                unified_locations.append({
                    'location_id': loc.id,
                    'original_name': loc.name,
                    'unified_name': loc.name,
                    'count': loc.count,
                    'is_unified': False
                })
        
        # Add unified locations
        for group in self.duplicate_groups:
            mergeable = group.get_mergeable_locations()
            if len(mergeable) <= 1:
                continue
                
            unified_name = group.get_merge_name()
            total_count = sum(loc.count for loc in mergeable)
            
            # Add the unified location
            unified_locations.append({
                'location_id': f"unified_{group.group_id}",
                'original_name': ', '.join(loc.name for loc in mergeable),
                'unified_name': unified_name,
                'count': total_count,
                'is_unified': True
            })
        
        # Create and save DataFrame
        df = pd.DataFrame(unified_locations)
        df.to_csv(output_path, index=False)
        
        logger.info(f"Exported {len(unified_locations)} unified locations to {output_path}")
        return df

class LocationUnificationReviewer:
    """Interactive interface for reviewing and deciding on location unification"""
    
    def __init__(self, engine: LocationUnificationEngine):
        self.engine = engine
        self.current_group_idx = 0
        self.output = widgets.Output()
        self.interface = None
    
    def create_interface(self):
        """Create the interactive interface for reviewing duplicates"""
        # Top controls
        self.group_dropdown = widgets.Dropdown(
            options=[(f"Group {i+1}: {group.main_location.name}", i) 
                    for i, group in enumerate(self.engine.duplicate_groups)],
            description='Select Group:',
            style={'description_width': 'initial'}
        )
        
        self.group_dropdown.observe(self._jump_to_group, names='value')
        
        self.search_input = widgets.Text(
            value='',
            placeholder='Search for location...',
            description='Search:',
            style={'description_width': 'initial'}
        )
        
        self.search_button = widgets.Button(
            description='Search',
            button_style='info',
            layout=widgets.Layout(width='100px')
        )
        
        self.search_button.on_click(self._search_locations)
        
        self.progress_text = widgets.HTML(
            value=f"Group 1 of {len(self.engine.duplicate_groups)}"
        )
        
        # Navigation buttons
        self.prev_button = widgets.Button(
            description='Previous',
            button_style='info',
            layout=widgets.Layout(width='100px')
        )
        
        self.next_button = widgets.Button(
            description='Next',
            button_style='info',
            layout=widgets.Layout(width='100px')
        )
        
        self.prev_button.on_click(self._go_previous)
        self.next_button.on_click(self._go_next)
        
        # Decision buttons
        self.merge_button = widgets.Button(
            description='Merge Selected',
            button_style='success',
            layout=widgets.Layout(width='150px')
        )
        
        self.skip_button = widgets.Button(
            description='Skip',
            button_style='warning',
            layout=widgets.Layout(width='100px')
        )
        
        self.merge_button.on_click(lambda b: self._make_decision('merge'))
        self.skip_button.on_click(lambda b: self._make_decision('skip'))
        
        # Export button
        self.export_button = widgets.Button(
            description='Export Decisions',
            button_style='primary',
            layout=widgets.Layout(width='150px')
        )
        
        self.export_button.on_click(self._export_decisions)
        
        # Complete review button
        self.complete_button = widgets.Button(
            description='Complete Review',
            button_style='danger',
            layout=widgets.Layout(width='150px')
        )
        
        self.complete_button.on_click(lambda b: self._complete_review())
        
        # Layout the interface
        top_controls = widgets.HBox([
            widgets.VBox([
                widgets.HBox([self.search_input, self.search_button]),
                self.group_dropdown
            ]),
            widgets.VBox([
                self.progress_text,
                widgets.HBox([self.prev_button, self.next_button])
            ])
        ])
        
        bottom_controls = widgets.HBox([
            self.merge_button,
            self.skip_button,
            self.export_button,
            self.complete_button
        ])
        
        self.interface = widgets.VBox([
            top_controls,
            self.output,
            bottom_controls
        ])
        
        # Update display
        self._update_display()
        
        return self.interface
    
    def _update_display(self):
        """Update the displayed group"""
        with self.output:
            clear_output(wait=True)
            
            if not self.engine.duplicate_groups:
                display(HTML("<h3>No duplicate groups found</h3>"))
                return
                
            if self.current_group_idx < 0 or self.current_group_idx >= len(self.engine.duplicate_groups):
                self.current_group_idx = 0
                
            group = self.engine.duplicate_groups[self.current_group_idx]
            
            # Update progress text
            self.progress_text.value = f"Group {self.current_group_idx + 1} of {len(self.engine.duplicate_groups)}"
            
            # Display group information
            display(HTML(f"<h3>Potential Duplicate Group {self.current_group_idx + 1}</h3>"))
            
            # Create checkboxes for each location
            checkboxes = self._create_checkboxes(group)
            
            # Create merge name input
            merge_name_input = self._create_merge_name_input(group)
            
            # Display locations with checkboxes
            locations_box = widgets.VBox([
                widgets.HTML("<h4>Locations in this group:</h4>"),
                *checkboxes,
                widgets.HTML("<h4>Unified Location Name:</h4>"),
                merge_name_input
            ])
            
            display(locations_box)
    
    def _display_location_info(self, location: Location):
        """Display detailed information about a location"""
        display(HTML(f"<h4>Location Details: {location.name}</h4>"))
        display(HTML(f"<p>ID: {location.id}<br>Occurrences: {location.count}</p>"))
    
    def _search_locations(self, button):
        """Search for locations by name"""
        search_term = self.search_input.value.lower()
        if not search_term:
            return
            
        # Search in all groups
        for i, group in enumerate(self.engine.duplicate_groups):
            for location in group.get_all_locations():
                if search_term in location.name.lower():
                    self.current_group_idx = i
                    self._update_display()
                    return
        
        # If not found
        with self.output:
            display(HTML(f"<p style='color:red'>No location found containing '{search_term}'</p>"))
    
    def _jump_to_group(self, change):
        """Jump to the selected group"""
        if change['type'] == 'change' and change['name'] == 'value':
            self.current_group_idx = change['new']
            self._update_display()
    
    def _create_checkboxes(self, group: DuplicateGroup):
        """Create checkboxes for each location in the group"""
        checkboxes = []
        
        # Main location
        main_location = group.main_location
        main_checkbox = widgets.Checkbox(
            value=not group.is_location_excluded(main_location.id),
            description=f"{main_location.name} ({main_location.count} occurrences)",
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='100%')
        )
        
        # Define callback for checkbox changes
        def on_checkbox_change(change, location_id=main_location.id):
            if change['type'] == 'change' and change['name'] == 'value':
                include = change['new']
                if include:
                    if location_id in group.excluded_locations:
                        group.excluded_locations.remove(location_id)
                else:
                    group.excluded_locations.add(location_id)
                self._update_suggestion(group)
                
        main_checkbox.observe(on_checkbox_change, names='value')
        checkboxes.append(main_checkbox)
        
        # Similar locations
        for match in group.similar_locations:
            location = match.location2
            checkbox = widgets.Checkbox(
                value=not group.is_location_excluded(location.id),
                description=f"{location.name} ({location.count} occurrences) - Similarity: {match.score:.2f}",
                style={'description_width': 'initial'},
                layout=widgets.Layout(width='100%')
            )
            
            # Define callback for this checkbox
            def on_match_checkbox_change(change, location_id=location.id):
                if change['type'] == 'change' and change['name'] == 'value':
                    include = change['new']
                    if include:
                        if location_id in group.excluded_locations:
                            group.excluded_locations.remove(location_id)
                    else:
                        group.excluded_locations.add(location_id)
                    self._update_suggestion(group)
            
            checkbox.observe(on_match_checkbox_change, names='value')
            checkboxes.append(checkbox)
            
        return checkboxes
    
    def _create_merge_name_input(self, group: DuplicateGroup):
        """Create an input field for the merged location name"""
        # Suggested name
        if group.suggested_merge:
            suggested_name = group.suggested_merge.name
        else:
            suggested_name = group.main_location.name
            
        # Current custom name or suggested name
        current_value = group.custom_merge_name if group.custom_merge_name else suggested_name
        
        # Create input widget
        name_input = widgets.Text(
            value=current_value,
            description='Name:',
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='80%')
        )
        
        # Reset button
        reset_button = widgets.Button(
            description='Reset to Suggestion',
            button_style='info',
            layout=widgets.Layout(width='150px')
        )
        
        # Define callbacks
        def on_name_change(change):
            if change['type'] == 'change' and change['name'] == 'value':
                new_name = change['new']
                if new_name != suggested_name:
                    group.custom_merge_name = new_name
                else:
                    group.custom_merge_name = None
        
        def on_reset_click(b):
            name_input.value = suggested_name
            group.custom_merge_name = None
            
        name_input.observe(on_name_change, names='value')
        reset_button.on_click(on_reset_click)
        
        return widgets.HBox([name_input, reset_button])
    
    def _update_suggestion(self, group: DuplicateGroup):
        """Update the suggested merge location based on exclusions"""
        # Only update if there are locations to merge
        mergeable = group.get_mergeable_locations()
        if mergeable:
            # Find the location with the most occurrences among mergeable
            group.suggested_merge = max(mergeable, key=lambda loc: loc.count)
    
    def _go_previous(self, button):
        """Go to the previous group"""
        if self.current_group_idx > 0:
            self.current_group_idx -= 1
            self._update_display()
    
    def _go_next(self, button):
        """Go to the next group"""
        if self.current_group_idx < len(self.engine.duplicate_groups) - 1:
            self.current_group_idx += 1
            self._update_display()
    
    def _make_decision(self, action: str):
        """Record a decision for the current group"""
        if not self.engine.duplicate_groups:
            return
            
        group = self.engine.duplicate_groups[self.current_group_idx]
        
        if action == 'merge':
            mergeable = group.get_mergeable_locations()
            if len(mergeable) <= 1:
                with self.output:
                    display(HTML("<p style='color:red'>Cannot merge: need at least 2 selected locations</p>"))
                return
                
            # Record the decision
            self.engine.decisions[group.group_id] = {
                'action': 'merge',
                'unified_name': group.get_merge_name(),
                'locations': [{'id': loc.id, 'name': loc.name} for loc in mergeable],
                'excluded': list(group.excluded_locations)
            }
            
            # Go to next group
            if self.current_group_idx < len(self.engine.duplicate_groups) - 1:
                self.current_group_idx += 1
                self._update_display()
            else:
                self._complete_review()
                
        elif action == 'skip':
            # Record skip decision
            self.engine.decisions[group.group_id] = {
                'action': 'skip'
            }
            
            # Go to next group
            if self.current_group_idx < len(self.engine.duplicate_groups) - 1:
                self.current_group_idx += 1
                self._update_display()
            else:
                self._complete_review()
    
    def _complete_review(self):
        """Complete the review process"""
        with self.output:
            clear_output(wait=True)
            
            # Calculate statistics
            total_groups = len(self.engine.duplicate_groups)
            decided_groups = len(self.engine.decisions)
            merge_decisions = sum(1 for d in self.engine.decisions.values() if d.get('action') == 'merge')
            skip_decisions = sum(1 for d in self.engine.decisions.values() if d.get('action') == 'skip')
            
            # Display summary
            display(HTML(f"""
            <h3>Review Completed</h3>
            <p>Total duplicate groups: {total_groups}<br>
            Groups with decisions: {decided_groups}<br>
            Merge decisions: {merge_decisions}<br>
            Skip decisions: {skip_decisions}</p>
            <p>Click 'Export Decisions' to save your work.</p>
            """))
    
    def _export_decisions(self, button):
        """Export the decisions to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("location_unification_results")
        output_dir.mkdir(exist_ok=True)
        
        # Export decisions to JSON
        decisions_file = output_dir / f"location_decisions_{timestamp}.json"
        self.engine.save_decisions(str(decisions_file))
        
        # Export unified locations to CSV
        locations_file = output_dir / f"unified_locations_{timestamp}.csv"
        self.engine.export_unified_locations(str(locations_file))
        
        # Show confirmation
        with self.output:
            display(HTML(f"""
            <h3>Export Completed</h3>
            <p>Exported decisions to: {decisions_file}</p>
            <p>Exported unified locations to: {locations_file}</p>
            """))

def run_location_unification(weigh_events_file: str, similarity_threshold: float = 0.7):
    """Run the location unification process with an interactive UI"""
    engine = LocationUnificationEngine(similarity_threshold=similarity_threshold)
    
    # Extract locations from weigh events
    engine.extract_locations_from_weigh_events(weigh_events_file)
    
    # Find potential duplicates
    engine.find_duplicates_with_blocking(prefix_length=2)
    
    # Create the review interface
    reviewer = LocationUnificationReviewer(engine)
    interface = reviewer.create_interface()
    
    # Display the interface
    display(interface)
    
    return engine, reviewer 