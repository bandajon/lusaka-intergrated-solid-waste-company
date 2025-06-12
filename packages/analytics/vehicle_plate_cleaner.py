import pandas as pd
import re
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import json
from pathlib import Path
import logging
import numpy as np
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Vehicle:
    """Represents a vehicle entry with standardized fields"""
    id: str
    license_plate: str
    company_id: str
    tare_weight_kg: Optional[float] = None
    vehicle_model: Optional[str] = None
    vehicle_color: Optional[str] = None
    carrying_capacity_kg: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    cleaned_plate: Optional[str] = None
    
    def __post_init__(self):
        if self.cleaned_plate is None:
            self.cleaned_plate = clean_license_plate(self.license_plate)

@dataclass
class DuplicatePlateGroup:
    """Represents a group of vehicles with the same or similar license plates"""
    group_id: str
    main_vehicle: Vehicle
    similar_vehicles: List[Vehicle]
    suggested_merge: Optional[Vehicle] = None
    excluded_vehicles: Set[str] = field(default_factory=set)  # Vehicles to exclude from merge
    custom_plate: Optional[str] = None  # Custom license plate for the merged vehicle
    
    def get_all_vehicles(self) -> List[Vehicle]:
        """Get all vehicles in the group"""
        result = [self.main_vehicle]
        result.extend(self.similar_vehicles)
        return result
    
    def get_mergeable_vehicles(self) -> List[Vehicle]:
        """Get vehicles to be merged (excluding excluded ones)"""
        all_vehicles = self.get_all_vehicles()
        return [v for v in all_vehicles if v.id not in self.excluded_vehicles]
    
    def is_vehicle_excluded(self, vehicle_id: str) -> bool:
        """Check if a vehicle is excluded from merge"""
        return vehicle_id in self.excluded_vehicles
    
    def toggle_exclude(self, vehicle_id: str):
        """Toggle exclusion status of a vehicle"""
        if vehicle_id in self.excluded_vehicles:
            self.excluded_vehicles.remove(vehicle_id)
        else:
            self.excluded_vehicles.add(vehicle_id)
    
    def get_merge_plate(self) -> str:
        """Get the license plate to use for the merged vehicle"""
        if self.custom_plate:
            return self.custom_plate
        elif self.suggested_merge:
            return self.suggested_merge.cleaned_plate
        else:
            return self.get_mergeable_vehicles()[0].cleaned_plate if self.get_mergeable_vehicles() else ""


def clean_license_plate(plate: str) -> str:
    """Clean and standardize vehicle license plates according to Zambian standards
    
    Rules applied:
    1. Convert to string and remove ALL spaces immediately
    2. Convert to uppercase
    3. Remove special characters, dashes, etc.
    4. Ensure proper format for common patterns (GRZ, ABC1234, etc.)
    5. Handle special cases (CD for diplomatic, ZP for police, etc.)
    6. Strip decimal parts from plates with decimal points
    7. Reject plates that are only numbers
    """
    if not plate or pd.isna(plate):
        return ""
    
    # Convert to string and IMMEDIATELY remove all spaces
    plate = str(plate).replace(' ', '').strip().upper()
    
    # Check if the plate contains only digits or only letters (after stripping)
    if re.match(r'^\d+$', plate) or re.match(r'^\d+\.\d+$', plate):
        return ""  # Return empty string for plates that are just numbers
    
    if re.match(r'^[A-Z]+$', plate):
        return ""  # Return empty string for plates that are just letters
    
    # Handle plates with decimal points (like "BAD52.00")
    if '.' in plate:
        # Extract the part before the decimal
        parts = plate.split('.')
        plate = parts[0]
    
    # Remove dots, commas, slashes, etc.
    plate = re.sub(r'[^\w\-]', '', plate)
    
    # Remove underscores
    plate = plate.replace('_', '')
    
    # Format GRZ plates (government vehicles)
    if plate.startswith('GRZ'):
        # Just keep GRZ followed by the digits, no spaces or dashes
        grz_match = re.match(r'GRZ[-\s]*(\d+[A-Z]*)', plate)
        if grz_match:
            plate = f"GRZ{grz_match.group(1)}"
        # For cases with just GRZ, keep it as is
    
    # Try to extract letters and numbers wherever they appear
    # Look for different letter-number patterns
    
    # First try standard format of 2-3 letters followed by 3-4 digits
    std_match = re.match(r'([A-Z]{2,3})[-\s]*(\d{3,4})', plate)
    
    # If no match, try a more general pattern for any letters followed by any numbers
    if not std_match:
        std_match = re.match(r'([A-Z]+)[-\s]*(\d+)', plate)
    
    if std_match:
        letters = std_match.group(1)
        numbers = std_match.group(2)
        
        # Make sure we have 3 letters
        if len(letters) < 3:
            # Add leading letters as needed
            letters = 'A' * (3 - len(letters)) + letters
        elif len(letters) > 3:
            # Truncate to 3 letters if longer
            letters = letters[:3]
        
        # Make sure we have 4 digits
        if len(numbers) < 4:
            # Add leading zeros as needed
            numbers = '0' * (4 - len(numbers)) + numbers
        elif len(numbers) > 4:
            # Truncate to 4 digits if longer
            numbers = numbers[:4]
            
        plate = f"{letters}{numbers}"
    
    # Final check - don't return plates that are too short
    if len(plate) < 3:
        return ""
    
    # Return the cleaned plate
    return plate


def identify_duplicates(vehicles: List[Vehicle]) -> List[DuplicatePlateGroup]:
    """Identify duplicate license plates in the vehicles list"""
    logger.info("Finding duplicate license plates...")
    
    # Group vehicles by cleaned license plate
    plate_groups = {}
    for vehicle in vehicles:
        cleaned_plate = vehicle.cleaned_plate
        if cleaned_plate not in plate_groups:
            plate_groups[cleaned_plate] = []
        plate_groups[cleaned_plate].append(vehicle)
    
    # Create duplicate groups where more than one vehicle has the same cleaned plate
    duplicate_groups = []
    
    for cleaned_plate, group_vehicles in plate_groups.items():
        if len(group_vehicles) > 1 and cleaned_plate:  # Only consider non-empty plates
            group_id = f"group_{len(duplicate_groups)}"
            
            # Sort vehicles by:
            # 1. License plate matches cleaned plate exactly
            # 2. Tare weight is not null
            # 3. Original order as a tiebreaker
            sorted_vehicles = sorted(
                group_vehicles,
                key=lambda v: (
                    v.license_plate == v.cleaned_plate,  # Exact match first
                    v.tare_weight_kg is not None,       # Has tare weight
                    group_vehicles.index(v)             # Original order
                ),
                reverse=True
            )
            
            main_vehicle = sorted_vehicles[0]
            similar_vehicles = sorted_vehicles[1:]
            
            group = DuplicatePlateGroup(
                group_id=group_id,
                main_vehicle=main_vehicle,
                similar_vehicles=similar_vehicles,
                suggested_merge=main_vehicle
            )
            
            duplicate_groups.append(group)
    
    logger.info(f"Found {len(duplicate_groups)} duplicate license plate groups")
    return duplicate_groups


class LicensePlateReviewer:
    """Interactive reviewer for duplicate license plate decisions"""
    
    def __init__(self, vehicles: List[Vehicle], duplicate_groups: List[DuplicatePlateGroup]):
        self.vehicles = vehicles
        self.duplicate_groups = duplicate_groups
        self.current_index = 0
        self.vehicle_checkboxes = {}  # Store checkboxes for each vehicle
        self.plate_input = None  # Text input for custom plate
        self.decisions = {}  # Store decisions for each group
        self.create_interface()
    
    def create_interface(self):
        """Create the review UI"""
        # Output areas
        self.output_main = widgets.Output()
        self.output_checkboxes = widgets.Output()
        self.output_plate = widgets.Output()
        
        # Widgets
        self.progress = widgets.IntProgress(
            value=0, 
            max=len(self.duplicate_groups),
            description='Progress:'
        )
        
        self.group_info = widgets.HTML()
        
        # Navigation buttons
        self.prev_btn = widgets.Button(description='← Previous', disabled=True)
        self.next_btn = widgets.Button(description='Next →')
        
        # Decision buttons
        self.merge_btn = widgets.Button(description='Merge Vehicles', button_style='success')
        self.keep_separate_btn = widgets.Button(description='Keep Separate', button_style='warning')
        
        # Export button
        self.export_btn = widgets.Button(description='Export Decisions', disabled=True)
        
        # Connect event handlers
        self.prev_btn.on_click(self._go_previous)
        self.next_btn.on_click(self._go_next)
        self.merge_btn.on_click(lambda b: self._make_decision('merge'))
        self.keep_separate_btn.on_click(lambda b: self._make_decision('keep_separate'))
        self.export_btn.on_click(self._export_decisions)
        
        # Jump to specific group
        self.group_dropdown = widgets.Dropdown(
            options=[(f"Group {i+1}: {g.main_vehicle.cleaned_plate}", i) 
                     for i, g in enumerate(self.duplicate_groups)],
            description='Jump to:',
            layout=widgets.Layout(width='500px')
        )
        self.group_dropdown.observe(self._jump_to_group, names='value')
        
        # Layout
        nav_box = widgets.HBox([self.prev_btn, self.next_btn])
        action_box = widgets.HBox([self.merge_btn, self.keep_separate_btn])
        
        # Main container
        main_container = widgets.VBox([
            self.progress,
            self.group_info,
            self.group_dropdown,
            self.output_main,
            self.output_checkboxes,
            self.output_plate,
            nav_box,
            action_box,
            self.export_btn
        ])
        
        # Display
        display(main_container)
        
        # Show first group
        self._update_display()
    
    def _update_display(self):
        """Update the display with current group information"""
        if self.current_index >= len(self.duplicate_groups):
            self._complete_review()
            return
        
        group = self.duplicate_groups[self.current_index]
        
        # Update progress
        self.progress.value = self.current_index
        
        # Group info
        self.group_info.value = f"<h3>Group {self.current_index + 1} of {len(self.duplicate_groups)}</h3>"
        
        # Clear and update main output
        with self.output_main:
            clear_output()
            
            print(f"License Plate Group: {group.main_vehicle.cleaned_plate}")
            print("-" * 50)
            
            # Main vehicle
            print("Main Vehicle:")
            self._display_vehicle_info(group.main_vehicle)
            print()
            
            # Similar vehicles
            print("Similar Vehicles:")
            for i, vehicle in enumerate(group.similar_vehicles):
                self._display_vehicle_info(vehicle)
                print()
        
        # Create checkboxes for vehicle selection
        self._create_checkboxes(group)
        
        # Create plate input
        self._create_plate_input(group)
        
        # Update navigation buttons
        self.prev_btn.disabled = (self.current_index == 0)
        self.next_btn.disabled = (self.current_index >= len(self.duplicate_groups) - 1)
    
    def _display_vehicle_info(self, vehicle: Vehicle):
        """Display vehicle information"""
        print(f"  ID: {vehicle.id}")
        print(f"  License Plate: '{vehicle.license_plate}'")
        print(f"  Cleaned Plate: '{vehicle.cleaned_plate}'")
        print(f"  Company ID: {vehicle.company_id}")
        print(f"  Tare Weight: {vehicle.tare_weight_kg} kg")
    
    def _jump_to_group(self, change):
        """Jump to a specific group"""
        if change['name'] == 'value':
            self.current_index = change['new']
            self._update_display()
    
    def _create_checkboxes(self, group: DuplicatePlateGroup):
        """Create checkboxes for vehicle selection"""
        self.vehicle_checkboxes.clear()
        all_vehicles = group.get_all_vehicles()
        
        with self.output_checkboxes:
            clear_output()
            
            print("\nVehicles to include in merge (uncheck to exclude):")
            checkbox_container = widgets.VBox()
            
            for vehicle in all_vehicles:
                is_checked = not group.is_vehicle_excluded(vehicle.id)
                
                checkbox = widgets.Checkbox(
                    value=is_checked,
                    description=f"{vehicle.license_plate} ({vehicle.id})",
                    layout=widgets.Layout(width='auto')
                )
                
                # Connect to event handler
                def on_checkbox_change(change, vehicle_id=vehicle.id):
                    if change['new']:
                        # Check = include in merge
                        if vehicle_id in group.excluded_vehicles:
                            group.excluded_vehicles.remove(vehicle_id)
                    else:
                        # Uncheck = exclude from merge
                        group.excluded_vehicles.add(vehicle_id)
                    self._update_suggestion(group)
                
                checkbox.observe(on_checkbox_change, names='value')
                self.vehicle_checkboxes[vehicle.id] = checkbox
                
                # Style the checkbox based on suggested merge
                if vehicle.id == group.suggested_merge.id:
                    label = widgets.HTML(
                        value=f"<b>✓ {vehicle.license_plate} ({vehicle.id}) - Suggested</b>",
                        layout=widgets.Layout(width='auto')
                    )
                else:
                    label = widgets.HTML(
                        value=f"{vehicle.license_plate} ({vehicle.id})",
                        layout=widgets.Layout(width='auto')
                    )
                
                row = widgets.HBox([checkbox, label])
                checkbox_container.children += (row,)
            
            display(checkbox_container)
            self._update_suggestion(group)
    
    def _create_plate_input(self, group: DuplicatePlateGroup):
        """Create input field for custom license plate"""
        with self.output_plate:
            clear_output()
            
            print("\nStandardized license plate (optional):")
            
            # Create text input for license plate
            self.plate_input = widgets.Text(
                value=group.custom_plate or group.get_merge_plate(),
                description='License Plate:',
                layout=widgets.Layout(width='500px'),
                style={'description_width': 'initial'}
            )
            
            # Create clean button
            clean_btn = widgets.Button(
                description='Clean & Standardize',
                button_style='info',
                tooltip='Apply standard cleaning rules'
            )
            
            # Create reset button
            reset_btn = widgets.Button(
                description='Use Suggested',
                button_style='warning',
                tooltip='Reset to suggested license plate'
            )
            
            # Connect event handlers
            def on_plate_change(change):
                if change['new'].strip():
                    group.custom_plate = change['new'].strip()
                else:
                    group.custom_plate = None
                self._update_suggestion(group)
            
            def on_clean_click(b):
                plate = self.plate_input.value
                cleaned = clean_license_plate(plate)
                self.plate_input.value = cleaned
                group.custom_plate = cleaned
                self._update_suggestion(group)
            
            def on_reset_click(b):
                suggested_plate = group.suggested_merge.cleaned_plate
                self.plate_input.value = suggested_plate
                group.custom_plate = None
                self._update_suggestion(group)
            
            self.plate_input.observe(on_plate_change, names='value')
            clean_btn.on_click(on_clean_click)
            reset_btn.on_click(on_reset_click)
            
            # Layout
            plate_box = widgets.HBox([self.plate_input, clean_btn, reset_btn])
            display(plate_box)
    
    def _update_suggestion(self, group: DuplicatePlateGroup):
        """Update merge suggestion based on selection"""
        with self.output_checkboxes:
            # Don't clear_output to preserve checkboxes, just add/update the summary
            mergeable = group.get_mergeable_vehicles()
            
            if len(mergeable) < 2:
                print("\n⚠️ Warning: At least 2 vehicles must be selected for merge!")
            else:
                merge_plate = group.get_merge_plate()
                print(f"\n✓ {len(mergeable)} vehicles will be merged with plate: '{merge_plate}'")
                print("Vehicles to merge:")
                for v in mergeable:
                    marker = "→" if v.id == group.suggested_merge.id else "•"
                    print(f"  {marker} {v.license_plate} ({v.id})")
    
    def _go_previous(self, button):
        """Go to previous group"""
        if self.current_index > 0:
            self.current_index -= 1
            self._update_display()
    
    def _go_next(self, button):
        """Go to next group"""
        if self.current_index < len(self.duplicate_groups) - 1:
            self.current_index += 1
            self._update_display()
        else:
            self._complete_review()
    
    def _make_decision(self, action: str):
        """Record a decision for the current group"""
        group = self.duplicate_groups[self.current_index]
        
        decision = {
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'group': {
                'id': group.group_id,
                'main_vehicle': group.main_vehicle.id,
                'similar_vehicles': [v.id for v in group.similar_vehicles],
                'excluded_vehicles': list(group.excluded_vehicles),
                'custom_plate': group.custom_plate
            }
        }
        
        if action == 'merge':
            mergeable = group.get_mergeable_vehicles()
            if len(mergeable) < 2:
                print("Error: Cannot merge - at least 2 vehicles must be selected!")
                return
            
            decision['merge_to'] = group.suggested_merge.id
            decision['mergeable_vehicles'] = [v.id for v in mergeable]
            decision['merge_plate'] = group.get_merge_plate()
        
        self.decisions[group.group_id] = decision
        self._go_next(None)
    
    def _complete_review(self):
        """Complete the review process"""
        with self.output_main:
            clear_output()
            print("Review Complete!")
            print(f"Total groups reviewed: {len(self.decisions)}")
            print("Ready to export decisions")
        
        with self.output_checkboxes:
            clear_output()
        
        with self.output_plate:
            clear_output()
        
        self.export_btn.disabled = False
        
        # Hide navigation and decision buttons
        self.prev_btn.layout.visibility = 'hidden'
        self.next_btn.layout.visibility = 'hidden'
        self.merge_btn.layout.visibility = 'hidden'
        self.keep_separate_btn.layout.visibility = 'hidden'
    
    def _export_decisions(self, button):
        """Export decisions and create cleaned vehicle dataset"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Process decisions
        vehicles_to_remove = []
        merge_mapping = {}
        plate_changes = {}  # Track plate changes
        
        for decision in self.decisions.values():
            if decision['action'] == 'merge':
                merge_to = decision['merge_to']
                merge_plate = decision.get('merge_plate')
                
                # Only merge vehicles that are not excluded
                mergeable_ids = decision.get('mergeable_vehicles', [])
                
                for vehicle_id in mergeable_ids:
                    if vehicle_id != merge_to:
                        merge_mapping[vehicle_id] = merge_to
                        vehicles_to_remove.append(vehicle_id)
                
                # Track if plate changed
                if merge_plate:
                    plate_changes[merge_to] = merge_plate
        
        # Create cleaned dataset with updated plates and unique tare weights
        cleaned_vehicles = []
        current_time = datetime.now()
        
        # Create a lookup for original vehicle data by ID
        vehicle_lookup = {v.id: v for v in self.vehicles}
        
        for vehicle in self.vehicles:
            if vehicle.id not in vehicles_to_remove:
                # Use new plate if specified
                license_plate = plate_changes.get(vehicle.id, vehicle.license_plate)
                cleaned_plate = clean_license_plate(license_plate)
                
                # Create a complete vehicle record with the expected format
                cleaned_vehicles.append({
                    'vehicle_id': vehicle.id,
                    'license_plate': license_plate,
                    'company_id': vehicle.company_id,
                    'vehicle_model': vehicle.vehicle_model,
                    'vehicle_color': vehicle.vehicle_color,
                    'carrying_capacity_kg': vehicle.carrying_capacity_kg,
                    'tare_weight_kg': vehicle.tare_weight_kg,
                    'created_at': current_time,
                    'updated_at': current_time
                })
        
        cleaned_df = pd.DataFrame(cleaned_vehicles)
        
        # Save outputs
        output_dir = Path(f"vehicle_deduplication_{timestamp}")
        output_dir.mkdir(exist_ok=True)
        
        # Cleaned dataset
        cleaned_df.to_csv(output_dir / "cleaned_vehicles.csv", index=False)
        
        # Merge mapping
        with open(output_dir / "merge_mapping.json", 'w') as f:
            json.dump(merge_mapping, f, indent=2)
        
        # Plate changes
        with open(output_dir / "plate_changes.json", 'w') as f:
            json.dump(plate_changes, f, indent=2)
        
        # Full decisions
        with open(output_dir / "decisions.json", 'w') as f:
            json.dump(self.decisions, f, indent=2)
        
        # Summary report
        summary = {
            'timestamp': timestamp,
            'original_count': len(self.vehicles),
            'cleaned_count': len(cleaned_vehicles),
            'removed_count': len(vehicles_to_remove),
            'groups_reviewed': len(self.decisions),
            'merge_decisions': sum(1 for d in self.decisions.values() if d['action'] == 'merge'),
            'keep_separate_decisions': sum(1 for d in self.decisions.values() if d['action'] == 'keep_separate'),
            'excluded_vehicles': sum(len(d['group'].get('excluded_vehicles', [])) for d in self.decisions.values()),
            'plate_changes': len(plate_changes)
        }
        
        with open(output_dir / "summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Generate HTML report
        self._generate_html_report(output_dir, summary)
        
        # Update display
        with self.output_main:
            clear_output()
            print(f"Export Complete!")
            print(f"Output directory: {output_dir}")
            print(f"Original vehicles: {summary['original_count']}")
            print(f"Cleaned vehicles: {summary['cleaned_count']}")
            print(f"Removed duplicates: {summary['removed_count']}")
            print(f"Excluded from merge: {summary['excluded_vehicles']}")
            print(f"Plate changes: {summary['plate_changes']}")
            print(f"Reduction: {summary['removed_count']/summary['original_count']*100:.1f}%")
    
    def _generate_html_report(self, output_dir: Path, summary: dict):
        """Generate a comprehensive HTML report"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Vehicle License Plate Deduplication Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
                .stat-card {{ background-color: white; border: 1px solid #dee2e6; border-radius: 5px; padding: 20px; }}
                .stat-value {{ font-size: 2em; font-weight: bold; color: #007bff; }}
                .decisions {{ margin-top: 30px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #dee2e6; padding: 8px 12px; text-align: left; }}
                th {{ background-color: #f8f9fa; }}
                .merge {{ color: #28a745; }}
                .separate {{ color: #ffc107; }}
                .excluded {{ color: #dc3545; }}
                .plate-changed {{ background-color: #fff3cd; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Vehicle License Plate Deduplication Report</h1>
                    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <h3>Original Vehicles</h3>
                        <div class="stat-value">{summary['original_count']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>After Deduplication</h3>
                        <div class="stat-value">{summary['cleaned_count']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Duplicates Removed</h3>
                        <div class="stat-value">{summary['removed_count']}</div>
                        <div>({summary['removed_count']/summary['original_count']*100:.1f}%)</div>
                    </div>
                    <div class="stat-card">
                        <h3>Groups Reviewed</h3>
                        <div class="stat-value">{summary['groups_reviewed']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Excluded Vehicles</h3>
                        <div class="stat-value">{summary['excluded_vehicles']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Plate Format Changes</h3>
                        <div class="stat-value">{summary['plate_changes']}</div>
                    </div>
                </div>
                
                <div class="decisions">
                    <h2>Decision Summary</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Group ID</th>
                                <th>Action</th>
                                <th>Total Vehicles</th>
                                <th>Excluded</th>
                                <th>Merged</th>
                                <th>Merged To</th>
                                <th>Final Plate</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        # Add decision details
        for group_id, decision in self.decisions.items():
            action = decision['action']
            group = decision['group']
            
            total_vehicles = len(group['similar_vehicles']) + 1
            excluded_count = len(group.get('excluded_vehicles', []))
            merged_count = len(decision.get('mergeable_vehicles', [])) - 1 if action == 'merge' else 0
            merge_to = decision.get('merge_to', '-')
            merge_plate = decision.get('merge_plate', '')
            custom_plate = group.get('custom_plate', '')
            
            action_class = 'merge' if action == 'merge' else 'separate'
            plate_cell_class = 'plate-changed' if custom_plate else ''
            
            html_content += f"""
                            <tr>
                                <td>{group_id}</td>
                                <td class="{action_class}">{action}</td>
                                <td>{total_vehicles}</td>
                                <td class="excluded">{excluded_count}</td>
                                <td>{merged_count}</td>
                                <td>{merge_to}</td>
                                <td class="{plate_cell_class}">{merge_plate}</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(output_dir / "report.html", 'w') as f:
            f.write(html_content)


def load_vehicles_from_csv(file_path: str) -> List[Vehicle]:
    """Load vehicles from CSV file"""
    logger.info(f"Loading data from {file_path}")
    df = pd.read_csv(file_path)
    
    # Convert to Vehicle objects
    vehicles = []
    for _, row in df.iterrows():
        # Handle potential missing columns
        vehicle = Vehicle(
            id=row['vehicle_id'],
            license_plate=row['license_plate'],
            company_id=row['company_id'],
            tare_weight_kg=row.get('tare_weight_kg'),
            vehicle_model=row.get('vehicle_model'),
            vehicle_color=row.get('vehicle_color'),
            carrying_capacity_kg=row.get('carrying_capacity_kg'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )
        vehicles.append(vehicle)
    
    logger.info(f"Loaded {len(vehicles)} vehicles")
    return vehicles


def clean_all_plates(file_path: str) -> pd.DataFrame:
    """Simple function to clean all license plates in a CSV file without deduplication"""
    df = pd.read_csv(file_path)
    
    # Apply plate cleaning function
    df['cleaned_plate'] = df['license_plate'].apply(clean_license_plate)
    
    # Clear out company_id and tare_weight columns as requested
    df['company_id'] = None
    df['tare_weight_kg'] = None
    
    # Count before filtering
    total_count = len(df)
    
    # Identify rejected plates (empty cleaned_plate)
    rejected_plates = df[df['cleaned_plate'] == '']['license_plate'].tolist()
    
    # Remove rows with empty cleaned_plate (rejected plates)
    df = df[df['cleaned_plate'] != '']
    rejected_count = total_count - len(df)
    
    # Count standardized formats
    standard_formats = {
        'GRZ': df['cleaned_plate'].str.startswith('GRZ').sum(),
        'AAA####': len(df[df['cleaned_plate'].str.match(r'^[A-Z]{3}\d{4}$')]),
        'Special': len(df) - df['cleaned_plate'].str.startswith('GRZ').sum() - len(df[df['cleaned_plate'].str.match(r'^[A-Z]{3}\d{4}$')])
    }
    
    logger.info(f"License plate formats after cleaning:")
    for format_type, count in standard_formats.items():
        logger.info(f"  - {format_type}: {count} vehicles")
    logger.info(f"  - Rejected: {rejected_count} vehicles (just numbers or just letters)")
    
    if rejected_count > 0:
        logger.info(f"  - Rejected plates: {', '.join(rejected_plates[:10])}")
        if len(rejected_plates) > 10:
            logger.info(f"    ... and {len(rejected_plates) - 10} more")
    
    # Update the actual license_plate field with the cleaned version
    df['license_plate'] = df['cleaned_plate']
    
    # Drop the cleaned_plate column to maintain the same schema as the input
    df = df.drop(columns=['cleaned_plate'])
    
    return df


# Example usage functions
def run_license_plate_cleaner(file_path: str):
    """Run the full license plate cleaner with interactive review"""
    # Load vehicles from CSV
    vehicles = load_vehicles_from_csv(file_path)
    
    # Identify duplicate plates
    duplicate_groups = identify_duplicates(vehicles)
    
    # Create interactive reviewer
    reviewer = LicensePlateReviewer(vehicles, duplicate_groups)
    
    return reviewer


def batch_clean_plates(file_path: str):
    """Batch clean all license plates without interactive review"""
    # Load and clean plates
    cleaned_df = clean_all_plates(file_path)
    
    # Save to a new file
    output_path = f"batch_cleaned_plates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    cleaned_df.to_csv(output_path, index=False)
    
    logger.info(f"Cleaned plates saved to {output_path}")
    return cleaned_df