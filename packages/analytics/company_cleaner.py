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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Company:
    """Represents a company entry with standardized fields"""
    id: str
    name: str
    type_code: int
    cleaned_name: str = None
    
    def __post_init__(self):
        if self.cleaned_name is None:
            self.cleaned_name = self.name.strip()

@dataclass
class SimilarityMatch:
    """Represents a similarity match between two companies"""
    company1: Company
    company2: Company
    score: float
    
    def __repr__(self):
        return f"'{self.company1.name}' <-> '{self.company2.name}' (score: {self.score:.3f})"

@dataclass
class DuplicateGroup:
    """Represents a group of potentially duplicate companies"""
    group_id: str
    main_company: Company
    similar_companies: List[SimilarityMatch]
    suggested_merge: Optional[Company] = None
    excluded_companies: Set[str] = field(default_factory=set)  # Companies to exclude from merge
    custom_merge_name: Optional[str] = None  # Custom name for merged company
    
    def get_all_companies(self) -> List[Company]:
        """Get all companies in the group"""
        result = [self.main_company]
        result.extend([match.company2 for match in self.similar_companies])
        return result
    
    def get_mergeable_companies(self) -> List[Company]:
        """Get companies to be merged (excluding excluded ones)"""
        all_companies = self.get_all_companies()
        return [c for c in all_companies if c.id not in self.excluded_companies]
    
    def is_company_excluded(self, company_id: str) -> bool:
        """Check if a company is excluded from merge"""
        return company_id in self.excluded_companies
    
    def toggle_exclude(self, company_id: str):
        """Toggle exclusion status of a company"""
        if company_id in self.excluded_companies:
            self.excluded_companies.remove(company_id)
        else:
            self.excluded_companies.add(company_id)
    
    def get_merge_name(self) -> str:
        """Get the name to use for the merged company"""
        if self.custom_merge_name:
            return self.custom_merge_name
        elif self.suggested_merge:
            return self.suggested_merge.name
        else:
            return self.get_mergeable_companies()[0].name if self.get_mergeable_companies() else ""

class CompanyDeduplicationEngine:
    """High-performance company deduplication engine"""
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
        self.companies: List[Company] = []
        self.duplicate_groups: List[DuplicateGroup] = []
        self.decisions: Dict[str, Dict] = {}
        
    def load_csv(self, file_path: str) -> pd.DataFrame:
        """Load companies from CSV file"""
        logger.info(f"Loading data from {file_path}")
        df = pd.read_csv(file_path, delimiter=',')
        
        # Convert to Company objects
        self.companies = []
        for _, row in df.iterrows():
            company = Company(
                id=row['company_id'],
                name=row['name'],
                type_code=row['type_code']
            )
            self.companies.append(company)
        
        logger.info(f"Loaded {len(self.companies)} companies")
        return df
    
    def calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two company names with enhanced prefix matching"""
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
        
        # Add a new token set ratio for better handling of word reordering
        token_set_ratio = fuzz.token_set_ratio(n1, n2) / 100
        
        # Weighted average with prefix consideration
        return max(
            (seq_similarity * 0.2) + (fuzzy_ratio * 0.2) + 
            (token_sort_ratio * 0.2) + (token_set_ratio * 0.2) + (prefix_similarity * 0.2),
            prefix_similarity  # Ensure prefix matches get priority
        )
    
    def prefix_block_companies(self, companies, prefix_length=2):
        """Block companies by their name prefix for more efficient comparison"""
        blocks = {}
        for company in companies:
            # Get the first few characters as the block key
            prefix = company.cleaned_name[:prefix_length].lower() if len(company.cleaned_name) >= prefix_length else company.cleaned_name.lower()
            
            if prefix not in blocks:
                blocks[prefix] = []
            blocks[prefix].append(company)
        
        return blocks
    
    def find_duplicates(self, use_cache: bool = True) -> List[DuplicateGroup]:
        """Find duplicate company groups"""
        logger.info("Finding duplicate groups...")
        
        processed = set()
        self.duplicate_groups = []
        
        for i, company1 in enumerate(self.companies):
            if company1.id in processed:
                continue
                
            similar_matches = []
            
            for j, company2 in enumerate(self.companies):
                if i != j and company2.id not in processed:
                    similarity = self.calculate_similarity(company1.cleaned_name, company2.cleaned_name)
                    
                    if similarity > self.similarity_threshold:
                        match = SimilarityMatch(company1, company2, similarity)
                        similar_matches.append(match)
                        processed.add(company2.id)
            
            if similar_matches:
                group_id = f"group_{i}"
                group = DuplicateGroup(
                    group_id=group_id,
                    main_company=company1,
                    similar_companies=similar_matches
                )
                group.suggested_merge = self._suggest_merge(group)
                self.duplicate_groups.append(group)
                processed.add(company1.id)
        
        logger.info(f"Found {len(self.duplicate_groups)} duplicate groups")
        return self.duplicate_groups
    
    def find_duplicates_with_blocking(self, prefix_length=2):
        """Find duplicate company groups using blocking for efficiency"""
        logger.info(f"Finding duplicate groups with prefix blocking (length={prefix_length})...")
        
        self.duplicate_groups = []
        processed = set()
        
        # Create blocks
        blocks = self.prefix_block_companies(self.companies, prefix_length)
        
        # Process each block
        for block_key, block_companies in blocks.items():
            if len(block_companies) <= 1:
                continue  # Skip blocks with only one company
                
            for i, company1 in enumerate(block_companies):
                if company1.id in processed:
                    continue
                    
                similar_matches = []
                
                for j, company2 in enumerate(block_companies):
                    if i != j and company2.id not in processed:
                        similarity = self.calculate_similarity(company1.cleaned_name, company2.cleaned_name)
                        
                        if similarity > self.similarity_threshold:
                            match = SimilarityMatch(company1, company2, similarity)
                            similar_matches.append(match)
                            processed.add(company2.id)
                
                if similar_matches:
                    group_id = f"group_{len(self.duplicate_groups)}"
                    group = DuplicateGroup(
                        group_id=group_id,
                        main_company=company1,
                        similar_companies=similar_matches
                    )
                    group.suggested_merge = self._suggest_merge(group)
                    self.duplicate_groups.append(group)
                    processed.add(company1.id)
        
        logger.info(f"Found {len(self.duplicate_groups)} duplicate groups")
        return self.duplicate_groups
    
    def find_prefix_duplicates(self, prefix_len=2, min_similarity=0.5):
        """Specialized method to find duplicates where one company is a prefix of another"""
        logger.info("Finding prefix-based duplicate groups...")
        
        # Group companies by their prefix
        prefix_groups = {}
        for company in self.companies:
            name = company.cleaned_name.upper()  # Uppercase for comparison
            if len(name) >= prefix_len:
                prefix = name[:prefix_len]
                if prefix not in prefix_groups:
                    prefix_groups[prefix] = []
                prefix_groups[prefix].append(company)
        
        # Find duplicates within each prefix group
        processed = set()
        prefix_duplicate_groups = []
        
        for prefix, companies in prefix_groups.items():
            if len(companies) <= 1:
                continue
                
            # Sort by name length (shortest first)
            companies.sort(key=lambda c: len(c.cleaned_name))
            
            for i, company1 in enumerate(companies):
                if company1.id in processed:
                    continue
                    
                similar_matches = []
                
                for j, company2 in enumerate(companies):
                    if i != j and company2.id not in processed:
                        # Check if shorter name is prefix of longer name
                        name1 = company1.cleaned_name.upper()
                        name2 = company2.cleaned_name.upper()
                        
                        # Check for initials vs. full name matching (e.g., "BL" vs "BL CONSTRUCTION")
                        is_prefix_match = name2.startswith(name1) or name1.startswith(name2)
                        
                        # Check for acronyms (e.g., "BL" as acronym for "Building Limited")
                        words1 = name1.split()
                        words2 = name2.split()
                        
                        # Try to detect if one name is an acronym of the other
                        is_acronym = False
                        if len(words1) == 1 and len(name1) <= 5:  # Potential acronym
                            acronym = ''.join(word[0] for word in words2 if word)
                            is_acronym = (name1 == acronym)
                        elif len(words2) == 1 and len(name2) <= 5:  # Potential acronym
                            acronym = ''.join(word[0] for word in words1 if word)
                            is_acronym = (name2 == acronym)
                        
                        if is_prefix_match or is_acronym:
                            # Calculate a similarity score
                            min_len = min(len(name1), len(name2))
                            max_len = max(len(name1), len(name2))
                            similarity = min_len / max_len if max_len > 0 else 0
                            
                            # Boost score for acronyms
                            if is_acronym:
                                similarity = max(similarity, 0.75)
                                
                            if similarity >= min_similarity:
                                match = SimilarityMatch(company1, company2, similarity)
                                similar_matches.append(match)
                                processed.add(company2.id)
                
                if similar_matches:
                    group_id = f"prefix_group_{len(prefix_duplicate_groups)}"
                    group = DuplicateGroup(
                        group_id=group_id,
                        main_company=company1,
                        similar_companies=similar_matches
                    )
                    group.suggested_merge = self._suggest_merge(group)
                    prefix_duplicate_groups.append(group)
                    processed.add(company1.id)
        
        # Add prefix duplicates to the main list
        self.duplicate_groups.extend(prefix_duplicate_groups)
        logger.info(f"Found {len(prefix_duplicate_groups)} prefix-based duplicate groups")
        return prefix_duplicate_groups
    
    def find_bl_type_duplicates(self):
        """Special method to find BL-type duplicates"""
        logger.info("Finding BL-type duplicate groups...")
        
        # First, find companies starting with BL
        bl_companies = [c for c in self.companies if c.cleaned_name.upper().startswith('BL')]
        logger.info(f"Found {len(bl_companies)} companies starting with 'BL'")
        
        if not bl_companies:
            logger.info("No BL-type companies found")
            return []
            
        # Group BL companies
        processed = set()
        bl_duplicate_groups = []
        
        # Sort by name length (shortest first)
        bl_companies.sort(key=lambda c: len(c.cleaned_name))
        
        for i, company1 in enumerate(bl_companies):
            if company1.id in processed:
                continue
                
            similar_matches = []
            
            for j, company2 in enumerate(bl_companies):
                if i != j and company2.id not in processed:
                    # Direct BL comparison logic with lower threshold
                    similarity = self.calculate_similarity(company1.cleaned_name, company2.cleaned_name)
                    
                    # Lower threshold specifically for BL companies
                    bl_threshold = 0.5  # Lower threshold for BL-type companies
                    
                    if similarity > bl_threshold:
                        match = SimilarityMatch(company1, company2, similarity)
                        similar_matches.append(match)
                        processed.add(company2.id)
            
            if similar_matches:
                group_id = f"bl_group_{len(bl_duplicate_groups)}"
                group = DuplicateGroup(
                    group_id=group_id,
                    main_company=company1,
                    similar_companies=similar_matches
                )
                group.suggested_merge = self._suggest_merge(group)
                bl_duplicate_groups.append(group)
                processed.add(company1.id)
        
        # Add BL duplicates to the main list
        self.duplicate_groups.extend(bl_duplicate_groups)
        logger.info(f"Found {len(bl_duplicate_groups)} BL-type duplicate groups")
        return bl_duplicate_groups
    
    def _suggest_merge(self, group: DuplicateGroup) -> Company:
        """Suggest which company to keep in a group"""
        all_companies = group.get_all_companies()
        
        # Prioritize companies with:
        # 1. No leading/trailing spaces
        # 2. Longer names (more complete information)
        # 3. Maintained order for ties
        
        ranked = sorted(
            all_companies,
            key=lambda c: (
                c.name == c.cleaned_name,  # No spaces
                len(c.cleaned_name),       # Longer names
                all_companies.index(c)     # Original order
            ),
            reverse=True
        )
        
        return ranked[0]
    
    def get_review_interface(self):
        """Create interactive review interface for decisions"""
        return DeduplicationReviewer(self)
    
    def find_all_duplicates(self, bl_specific=True):
        """Comprehensive method to find duplicates using multiple strategies"""
        logger.info("Starting comprehensive duplicate detection...")
        
        # First run standard duplicate detection 
        self.find_duplicates()
        
        # Then find prefix-based duplicates
        self.find_prefix_duplicates(prefix_len=2, min_similarity=0.5)
        
        # Specifically look for BL-type duplicates if requested
        if bl_specific:
            self.find_bl_type_duplicates()
        
        logger.info(f"Found a total of {len(self.duplicate_groups)} duplicate groups")
        return self.duplicate_groups

class DeduplicationReviewer:
    """Interactive reviewer for deduplication decisions"""
    
    def __init__(self, engine: CompanyDeduplicationEngine):
        self.engine = engine
        self.current_index = 0
        self.company_checkboxes = {}  # Store checkboxes for each company
        self.merge_name_input = None  # Text input for custom merge name
        self.create_interface()
    
    def create_interface(self):
        """Create the review UI"""
        # Output areas
        self.output_main = widgets.Output()
        self.output_checkboxes = widgets.Output()
        self.output_merge_name = widgets.Output()
        
        # Widgets
        self.progress = widgets.IntProgress(
            value=0, 
            max=len(self.engine.duplicate_groups),
            description='Progress:'
        )
        
        self.group_info = widgets.HTML()
        
        # Navigation buttons
        self.prev_btn = widgets.Button(description='← Previous', disabled=True)
        self.next_btn = widgets.Button(description='Next →')
        
        # Decision buttons
        self.merge_btn = widgets.Button(description='Merge Group', button_style='success')
        self.keep_separate_btn = widgets.Button(description='Keep Separate', button_style='warning')
        
        # Export button
        self.export_btn = widgets.Button(description='Export Decisions', disabled=True)
        
        # Connect event handlers
        self.prev_btn.on_click(self._go_previous)
        self.next_btn.on_click(self._go_next)
        self.merge_btn.on_click(lambda b: self._make_decision('merge'))
        self.keep_separate_btn.on_click(lambda b: self._make_decision('keep_separate'))
        self.export_btn.on_click(self._export_decisions)
        
        # Search functionality
        self.search_input = widgets.Text(
            placeholder='Search for company...',
            description='Search:',
            layout=widgets.Layout(width='500px')
        )
        self.search_btn = widgets.Button(description='Find')
        self.search_btn.on_click(self._search_companies)
        
        # Jump to specific group
        self.group_dropdown = widgets.Dropdown(
            options=[(f"Group {i+1}: {g.main_company.name}", i) 
                     for i, g in enumerate(self.engine.duplicate_groups)],
            description='Jump to:',
            layout=widgets.Layout(width='500px')
        )
        self.group_dropdown.observe(self._jump_to_group, names='value')
        
        # Layout
        search_box = widgets.HBox([self.search_input, self.search_btn])
        nav_box = widgets.HBox([self.prev_btn, self.next_btn])
        action_box = widgets.HBox([self.merge_btn, self.keep_separate_btn])
        
        # Main container
        main_container = widgets.VBox([
            self.progress,
            self.group_info,
            search_box,
            self.group_dropdown,
            self.output_main,
            self.output_checkboxes,
            self.output_merge_name,
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
        if self.current_index >= len(self.engine.duplicate_groups):
            self._complete_review()
            return
        
        group = self.engine.duplicate_groups[self.current_index]
        
        # Update progress
        self.progress.value = self.current_index
        
        # Group info
        self.group_info.value = f"<h3>Group {self.current_index + 1} of {len(self.engine.duplicate_groups)}</h3>"
        
        # Clear and update main output
        with self.output_main:
            clear_output()
            
            # Group type information (standard, prefix, BL-specific)
            group_type = "Standard"
            if "prefix_group" in group.group_id:
                group_type = "Prefix-based"
            elif "bl_group" in group.group_id:
                group_type = "BL-specific"
            
            print(f"Group Type: {group_type}")
            print("-" * 50)
            
            # Main company
            print("Main Company:")
            self._display_company_info(group.main_company)
            print()
            
            # Similar companies
            print("Similar Companies:")
            for i, match in enumerate(group.similar_companies):
                self._display_company_info(match.company2)
                print(f"  Similarity: {match.score:.1%}")
                print()
        
        # Create checkboxes for company selection
        self._create_checkboxes(group)
        
        # Create merge name input
        self._create_merge_name_input(group)
        
        # Update navigation buttons
        self.prev_btn.disabled = (self.current_index == 0)
        self.next_btn.disabled = (self.current_index >= len(self.engine.duplicate_groups) - 1)
    
    def _display_company_info(self, company: Company):
        """Display company information"""
        print(f"  ID: {company.id}")
        print(f"  Name: '{company.name}'")
        print(f"  Type: {company.type_code}")
        print(f"  Cleaned: '{company.cleaned_name}'")
    
    def _search_companies(self, button):
        """Search for companies by name or ID"""
        search_term = self.search_input.value.lower()
        if not search_term:
            return
            
        # Search in all groups
        for i, group in enumerate(self.engine.duplicate_groups):
            # Check main company
            if (search_term in group.main_company.name.lower() or 
                search_term in group.main_company.id.lower()):
                self.current_index = i
                self._update_display()
                return
                
            # Check similar companies
            for match in group.similar_companies:
                if (search_term in match.company2.name.lower() or 
                    search_term in match.company2.id.lower()):
                    self.current_index = i
                    self._update_display()
                    return
        
        # If no match found
        with self.output_main:
            clear_output()
            print(f"No company found matching '{search_term}'")
    
    def _jump_to_group(self, change):
        """Jump to a specific group"""
        if change['name'] == 'value':
            self.current_index = change['new']
            self._update_display()
    
    def _create_checkboxes(self, group: DuplicateGroup):
        """Create checkboxes for company selection"""
        self.company_checkboxes.clear()
        all_companies = group.get_all_companies()
        
        with self.output_checkboxes:
            clear_output()
            
            print("\nCompanies to include in merge (uncheck to exclude):")
            checkbox_container = widgets.VBox()
            
            for company in all_companies:
                is_checked = not group.is_company_excluded(company.id)
                
                checkbox = widgets.Checkbox(
                    value=is_checked,
                    description=f"{company.name} ({company.id})",
                    layout=widgets.Layout(width='auto')
                )
                
                # Connect to event handler
                def on_checkbox_change(change, company_id=company.id):
                    if change['new']:
                        # Check = include in merge
                        if company_id in group.excluded_companies:
                            group.excluded_companies.remove(company_id)
                    else:
                        # Uncheck = exclude from merge
                        group.excluded_companies.add(company_id)
                    self._update_suggestion(group)
                
                checkbox.observe(on_checkbox_change, names='value')
                self.company_checkboxes[company.id] = checkbox
                
                # Style the checkbox based on suggested merge
                if company.id == group.suggested_merge.id:
                    label = widgets.HTML(
                        value=f"<b>✓ {company.name} ({company.id}) - Suggested</b>",
                        layout=widgets.Layout(width='auto')
                    )
                else:
                    label = widgets.HTML(
                        value=f"{company.name} ({company.id})",
                        layout=widgets.Layout(width='auto')
                    )
                
                row = widgets.HBox([checkbox, label])
                checkbox_container.children += (row,)
            
            display(checkbox_container)
            self._update_suggestion(group)
    
    def _create_merge_name_input(self, group: DuplicateGroup):
        """Create input field for custom merge name"""
        with self.output_merge_name:
            clear_output()
            
            print("\nCustom merge name (optional):")
            
            # Create text input for merge name
            self.merge_name_input = widgets.Text(
                value=group.custom_merge_name or group.get_merge_name(),
                description='Merge Name:',
                layout=widgets.Layout(width='500px'),
                style={'description_width': 'initial'}
            )
            
            # Create reset button
            reset_btn = widgets.Button(
                description='Use Suggested',
                button_style='info',
                tooltip='Reset to suggested merge name'
            )
            
            # Connect event handlers
            def on_name_change(change):
                if change['new'].strip():
                    group.custom_merge_name = change['new'].strip()
                else:
                    group.custom_merge_name = None
                self._update_suggestion(group)
            
            def on_reset_click(b):
                self.merge_name_input.value = group.suggested_merge.name
                group.custom_merge_name = None
                self._update_suggestion(group)
            
            self.merge_name_input.observe(on_name_change, names='value')
            reset_btn.on_click(on_reset_click)
            
            # Layout
            name_box = widgets.HBox([self.merge_name_input, reset_btn])
            display(name_box)
    
    def _update_suggestion(self, group: DuplicateGroup):
        """Update merge suggestion based on selection"""
        with self.output_checkboxes:
            # Don't clear_output to preserve checkboxes, just add/update the summary
            mergeable = group.get_mergeable_companies()
            
            if len(mergeable) < 2:
                print("\n⚠️ Warning: At least 2 companies must be selected for merge!")
            else:
                merge_name = group.get_merge_name()
                print(f"\n✓ {len(mergeable)} companies will be merged to: '{merge_name}'")
                print("Companies to merge:")
                for c in mergeable:
                    marker = "→" if c.id == group.suggested_merge.id else "•"
                    print(f"  {marker} {c.name} ({c.id})")
    
    def _go_previous(self, button):
        """Go to previous group"""
        if self.current_index > 0:
            self.current_index -= 1
            self._update_display()
    
    def _go_next(self, button):
        """Go to next group"""
        if self.current_index < len(self.engine.duplicate_groups) - 1:
            self.current_index += 1
            self._update_display()
        else:
            self._complete_review()
    
    def _make_decision(self, action: str):
        """Record a decision for the current group"""
        group = self.engine.duplicate_groups[self.current_index]
        
        decision = {
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'group': {
                'id': group.group_id,
                'main_company': group.main_company.id,
                'similar_companies': [m.company2.id for m in group.similar_companies],
                'excluded_companies': list(group.excluded_companies),  # Save excluded companies
                'custom_merge_name': group.custom_merge_name  # Save custom name
            }
        }
        
        if action == 'merge':
            mergeable = group.get_mergeable_companies()
            if len(mergeable) < 2:
                print("Error: Cannot merge - at least 2 companies must be selected!")
                return
            
            decision['merge_to'] = group.suggested_merge.id
            decision['mergeable_companies'] = [c.id for c in mergeable]
            decision['merge_name'] = group.get_merge_name()  # Save the final merge name
        
        self.engine.decisions[group.group_id] = decision
        self._go_next(None)
    
    def _complete_review(self):
        """Complete the review process"""
        with self.output_main:
            clear_output()
            print("Review Complete!")
            print(f"Total groups reviewed: {len(self.engine.decisions)}")
            print("Ready to export decisions")
        
        with self.output_checkboxes:
            clear_output()
        
        with self.output_merge_name:
            clear_output()
        
        self.export_btn.disabled = False
        
        # Hide navigation and decision buttons
        self.prev_btn.layout.visibility = 'hidden'
        self.next_btn.layout.visibility = 'hidden'
        self.merge_btn.layout.visibility = 'hidden'
        self.keep_separate_btn.layout.visibility = 'hidden'
    
    def _export_decisions(self, button):
        """Export decisions and create cleaned dataset"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Process decisions
        companies_to_remove = []
        merge_mapping = {}
        name_changes = {}  # Track name changes
        
        for decision in self.engine.decisions.values():
            if decision['action'] == 'merge':
                merge_to = decision['merge_to']
                merge_name = decision.get('merge_name')
                
                # Only merge companies that are not excluded
                mergeable_ids = decision.get('mergeable_companies', [])
                
                for company_id in mergeable_ids:
                    if company_id != merge_to:
                        merge_mapping[company_id] = merge_to
                        companies_to_remove.append(company_id)
                
                # Track if name changed
                if merge_name:
                    name_changes[merge_to] = merge_name
        
        # Create cleaned dataset with updated names and matching the expected format
        cleaned_companies = []
        current_time = datetime.now()
        
        for company in self.engine.companies:
            if company.id not in companies_to_remove:
                # Use new name if specified
                name = name_changes.get(company.id, company.name)
                
                # Create a complete company record using the same format as extracted_companies.csv
                cleaned_companies.append({
                    'company_id': company.id,
                    'name': name,
                    'type_code': company.type_code,
                    'location': None,  # Matched fields from extracted_companies.csv
                    'pacra_status': None,
                    'zra_status': None,
                    'council_status': None,
                    'tpin': None,
                    'primary_contact_name': 'Contact Required',
                    'primary_contact_phone': 'Phone Required',
                    'primary_contact_email': None,
                    'created_at': current_time,
                    'updated_at': current_time
                })
        
        cleaned_df = pd.DataFrame(cleaned_companies)
        
        # Save outputs
        output_dir = Path(f"deduplication_output_{timestamp}")
        output_dir.mkdir(exist_ok=True)
        
        # Cleaned dataset - matches format of extracted_companies.csv
        cleaned_df.to_csv(output_dir / "cleaned_companies.csv", index=False)
        
        # Merge mapping
        with open(output_dir / "merge_mapping.json", 'w') as f:
            json.dump(merge_mapping, f, indent=2)
        
        # Name changes
        with open(output_dir / "name_changes.json", 'w') as f:
            json.dump(name_changes, f, indent=2)
        
        # Full decisions
        with open(output_dir / "decisions.json", 'w') as f:
            json.dump(self.engine.decisions, f, indent=2)
        
        # Summary report
        summary = {
            'timestamp': timestamp,
            'original_count': len(self.engine.companies),
            'cleaned_count': len(cleaned_companies),
            'removed_count': len(companies_to_remove),
            'groups_reviewed': len(self.engine.decisions),
            'merge_decisions': sum(1 for d in self.engine.decisions.values() if d['action'] == 'merge'),
            'keep_separate_decisions': sum(1 for d in self.engine.decisions.values() if d['action'] == 'keep_separate'),
            'excluded_companies': sum(len(d['group'].get('excluded_companies', [])) for d in self.engine.decisions.values()),
            'name_changes': len(name_changes)
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
            print(f"Original companies: {summary['original_count']}")
            print(f"Cleaned companies: {summary['cleaned_count']}")
            print(f"Removed companies: {summary['removed_count']}")
            print(f"Excluded from merge: {summary['excluded_companies']}")
            print(f"Name changes: {summary['name_changes']}")
            print(f"Reduction: {summary['removed_count']/summary['original_count']*100:.1f}%")
    
    def _generate_html_report(self, output_dir: Path, summary: dict):
        """Generate a comprehensive HTML report"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Company Deduplication Report</title>
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
                .name-changed {{ background-color: #fff3cd; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Company Deduplication Report</h1>
                    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <h3>Original Companies</h3>
                        <div class="stat-value">{summary['original_count']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>After Deduplication</h3>
                        <div class="stat-value">{summary['cleaned_count']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Reduction</h3>
                        <div class="stat-value">{summary['removed_count']}</div>
                        <div>({summary['removed_count']/summary['original_count']*100:.1f}%)</div>
                    </div>
                    <div class="stat-card">
                        <h3>Groups Reviewed</h3>
                        <div class="stat-value">{summary['groups_reviewed']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Excluded Companies</h3>
                        <div class="stat-value">{summary['excluded_companies']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Name Changes</h3>
                        <div class="stat-value">{summary['name_changes']}</div>
                    </div>
                </div>
                
                <div class="decisions">
                    <h2>Decision Summary</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Group ID</th>
                                <th>Action</th>
                                <th>Total Companies</th>
                                <th>Excluded</th>
                                <th>Merged</th>
                                <th>Merged To</th>
                                <th>Final Name</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        # Add decision details
        for group_id, decision in self.engine.decisions.items():
            action = decision['action']
            group = decision['group']
            
            total_companies = len(group['similar_companies']) + 1
            excluded_count = len(group.get('excluded_companies', []))
            merged_count = len(decision.get('mergeable_companies', [])) - 1 if action == 'merge' else 0
            merge_to = decision.get('merge_to', '-')
            merge_name = decision.get('merge_name', '')
            custom_name = group.get('custom_merge_name', '')
            
            action_class = 'merge' if action == 'merge' else 'separate'
            name_cell_class = 'name-changed' if custom_name else ''
            
            html_content += f"""
                            <tr>
                                <td>{group_id}</td>
                                <td class="{action_class}">{action}</td>
                                <td>{total_companies}</td>
                                <td class="excluded">{excluded_count}</td>
                                <td>{merged_count}</td>
                                <td>{merge_to}</td>
                                <td class="{name_cell_class}">{merge_name}</td>
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


class DeduplicationOptimizer:
    """Optimization strategies for large-scale deduplication"""
    
    def suggest_blocking_strategy(self, company_count: int) -> Dict:
        """Suggest blocking strategies based on dataset size"""
        # Calculate potential comparison counts
        full_comparisons = (company_count * (company_count - 1)) / 2
        
        # Estimate time (assuming 10,000 comparisons per second)
        comparisons_per_sec = 10000
        full_time_seconds = full_comparisons / comparisons_per_sec
        
        strategies = {
            "no_blocking": {
                "comparisons": int(full_comparisons),
                "estimated_time_seconds": full_time_seconds
            }
        }
        
        # First letter blocking (assume even distribution across 26 letters)
        letter_blocks = 26
        avg_block_size = company_count / letter_blocks
        letter_comparisons = letter_blocks * (avg_block_size * (avg_block_size - 1)) / 2
        letter_time_seconds = letter_comparisons / comparisons_per_sec
        
        strategies["first_letter"] = {
            "comparisons": int(letter_comparisons),
            "estimated_time_seconds": letter_time_seconds
        }
        
        # First two letters blocking (26^2 = 676 potential blocks)
        two_letter_blocks = min(676, company_count)  # Can't have more blocks than companies
        avg_two_letter_size = company_count / two_letter_blocks
        two_letter_comparisons = two_letter_blocks * (avg_two_letter_size * (avg_two_letter_size - 1)) / 2
        two_letter_time_seconds = two_letter_comparisons / comparisons_per_sec
        
        strategies["first_two_letters"] = {
            "comparisons": int(two_letter_comparisons),
            "estimated_time_seconds": two_letter_time_seconds
        }
        
        return strategies
    
    def block_companies(self, companies: List[Company], block_key: str = 'first_letter') -> Dict[str, List[Company]]:
        """Block companies by specified key for efficient comparison"""
        blocks = {}
        
        for company in companies:
            name = company.cleaned_name.upper()
            
            if block_key == 'first_letter':
                if name:
                    key = name[0]
                else:
                    key = ''
            elif block_key == 'first_two_letters':
                if len(name) >= 2:
                    key = name[:2]
                else:
                    key = name.ljust(2)
            elif block_key == 'name_length':
                key = str(len(name))
            elif block_key == 'type_code':
                key = str(company.type_code)
            else:
                key = 'default'
            
            if key not in blocks:
                blocks[key] = []
            blocks[key].append(company)
        
        return blocks


# Run the complete deduplication process with optimizations
def run_optimized_deduplication(file_path: str, similarity_threshold: float = 0.4):
    """Run optimized deduplication process for catching 'BL' type duplicates"""
    # Initialize engine with lower threshold
    engine = CompanyDeduplicationEngine(similarity_threshold=similarity_threshold)
    
    # Load data
    engine.load_csv(file_path)
    
    # Check if optimization needed
    optimizer = DeduplicationOptimizer()
    company_count = len(engine.companies)
    
    if company_count > 1000:
        strategies = optimizer.suggest_blocking_strategy(company_count)
        logger.info("Blocking strategy recommendations:")
        for strategy, stats in strategies.items():
            logger.info(f"{strategy}: {stats['comparisons']} comparisons, {stats['estimated_time_seconds']:.1f} seconds")
        
        # Use blocking for large datasets
        engine.find_duplicates_with_blocking(prefix_length=2)
    else:
        # For smaller datasets, use comprehensive approach
        engine.find_all_duplicates(bl_specific=True)
    
    # Start interactive review
    reviewer = engine.get_review_interface()
    
    return engine, reviewer

# Find BL-specific duplicates only
def find_bl_duplicates_only(file_path: str):
    """Run only the BL-specific duplicate finder"""
    engine = CompanyDeduplicationEngine(similarity_threshold=0.5)  # Lower threshold
    engine.load_csv(file_path)
    engine.find_bl_type_duplicates()
    reviewer = engine.get_review_interface()
    return engine, reviewer