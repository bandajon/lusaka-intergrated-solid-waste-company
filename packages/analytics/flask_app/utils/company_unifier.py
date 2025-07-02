"""
Company Unification Tool for Flask Application
============================================
Web-based interface for identifying and merging duplicate company entries
"""

import pandas as pd
import numpy as np
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz
from datetime import datetime
import json
import sys
import os

# Import database utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
try:
    from database_connection import read_companies, get_db_engine, get_db_connection
    DATABASE_AVAILABLE = True
except ImportError:
    print("Warning: Database utilities not available")
    DATABASE_AVAILABLE = False

class CompanyUnifier:
    """
    Web-based company unification tool for identifying and merging duplicates
    """
    
    def __init__(self, similarity_threshold=0.7):
        self.similarity_threshold = similarity_threshold
        self.companies_df = None
        self.duplicate_groups = []
        
    def load_companies_from_db(self):
        """Load companies from the database"""
        if not DATABASE_AVAILABLE:
            print("Database utilities not available")
            return False
            
        try:
            self.companies_df = read_companies()
            if self.companies_df is not None and not self.companies_df.empty:
                print(f"✅ Loaded {len(self.companies_df)} companies from database")
                # Ensure company_id column exists
                if 'id' in self.companies_df.columns and 'company_id' not in self.companies_df.columns:
                    self.companies_df['company_id'] = self.companies_df['id']
                return True
            else:
                print("❌ No companies found in database")
                return False
        except Exception as e:
            print(f"❌ Error loading companies: {e}")
            return False
    
    def calculate_similarity(self, name1, name2):
        """Calculate similarity score between two company names"""
        if pd.isna(name1) or pd.isna(name2):
            return 0.0
            
        # Normalize names
        n1 = str(name1).lower().strip()
        n2 = str(name2).lower().strip()
        
        if n1 == n2:
            return 1.0
        
        # Check if one is a prefix of another
        prefix_similarity = 0
        if n1.startswith(n2) or n2.startswith(n1):
            min_len = min(len(n1), len(n2))
            max_len = max(len(n1), len(n2))
            length_ratio = min_len / max_len if max_len > 0 else 0
            prefix_similarity = 0.8 + (0.2 * length_ratio)
        
        # Multiple similarity metrics
        seq_similarity = SequenceMatcher(None, n1, n2).ratio()
        fuzzy_ratio = fuzz.ratio(n1, n2) / 100
        token_sort_ratio = fuzz.token_sort_ratio(n1, n2) / 100
        token_set_ratio = fuzz.token_set_ratio(n1, n2) / 100
        
        # Weighted average with prefix consideration
        combined_similarity = max(
            (seq_similarity * 0.25) + (fuzzy_ratio * 0.25) + 
            (token_sort_ratio * 0.25) + (token_set_ratio * 0.25),
            prefix_similarity
        )
        
        return combined_similarity
    
    def find_duplicate_groups(self):
        """Find groups of potentially duplicate companies"""
        if self.companies_df is None or self.companies_df.empty:
            return []
        
        self.duplicate_groups = []
        processed_ids = set()
        
        for idx, company in self.companies_df.iterrows():
            if company['company_id'] in processed_ids:
                continue
                
            similar_companies = []
            main_company = {
                'company_id': company['company_id'],
                'name': company['name'],
                'type_code': company.get('type_code', None),
                'location': company.get('location', None)
            }
            
            # Find similar companies
            for idx2, other_company in self.companies_df.iterrows():
                if (idx != idx2 and 
                    other_company['company_id'] not in processed_ids):
                    
                    similarity = self.calculate_similarity(
                        company['name'], 
                        other_company['name']
                    )
                    
                    if similarity >= self.similarity_threshold:
                        similar_companies.append({
                            'company_id': other_company['company_id'],
                            'name': other_company['name'],
                            'type_code': other_company.get('type_code', None),
                            'location': other_company.get('location', None),
                            'similarity': round(similarity, 3)
                        })
                        processed_ids.add(other_company['company_id'])
            
            if similar_companies:
                group = {
                    'group_id': f"group_{len(self.duplicate_groups)}",
                    'main_company': main_company,
                    'similar_companies': similar_companies,
                    'suggested_merge_name': self._suggest_merge_name(main_company, similar_companies)
                }
                self.duplicate_groups.append(group)
                processed_ids.add(company['company_id'])
        
        return self.duplicate_groups
    
    def _suggest_merge_name(self, main_company, similar_companies):
        """Suggest the best name for merged company"""
        all_names = [main_company['name']] + [c['name'] for c in similar_companies]
        
        # Prefer longest non-empty name
        valid_names = [name for name in all_names if name and str(name).strip()]
        if not valid_names:
            return main_company['name']
        
        # Sort by length (longest first) and return the longest
        return max(valid_names, key=len)
    
    def get_duplicate_summary(self):
        """Get summary statistics of duplicates found"""
        if not self.duplicate_groups:
            return {
                'total_groups': 0,
                'total_duplicates': 0,
                'potential_reduction': 0
            }
        
        total_duplicates = sum(len(group['similar_companies']) for group in self.duplicate_groups)
        
        return {
            'total_groups': len(self.duplicate_groups),
            'total_duplicates': total_duplicates,
            'potential_reduction': total_duplicates,
            'original_count': len(self.companies_df) if self.companies_df is not None else 0
        }
    
    def merge_companies(self, merge_decisions):
        """
        Execute company merges based on user decisions
        
        merge_decisions: List of dict with structure:
        {
            'group_id': 'group_0',
            'action': 'merge',  # or 'keep_separate'
            'merge_to_id': 'company_id_to_keep',
            'merge_name': 'Final Company Name',
            'companies_to_remove': ['id1', 'id2', ...],
            'selected_companies': ['id1', 'id2', 'id3', ...]  # NEW: companies selected for merge
        }
        """
        if not merge_decisions:
            return False, "No merge decisions provided"
        
        print(f"📋 Starting merge process for {len(merge_decisions)} decisions")
        
        try:
            # Track changes
            companies_to_remove = []
            name_updates = {}
            
            for i, decision in enumerate(merge_decisions):
                print(f"📋 Processing decision {i+1}: {decision}")
                
                if decision['action'] == 'merge':
                    # Record company to keep with potential name update
                    merge_to_id = decision['merge_to_id']
                    new_name = decision.get('merge_name', '').strip()
                    
                    print(f"✅ Merge target: {merge_to_id}, New name: {new_name}")
                    
                    if new_name:
                        name_updates[merge_to_id] = new_name
                        print(f"🏷️ Will update company {merge_to_id} name to: {new_name}")
                    
                    # Handle both old and new data formats
                    if 'selected_companies' in decision:
                        # New format: only merge selected companies
                        selected_companies = decision['selected_companies']
                        companies_to_remove_in_group = [cid for cid in selected_companies if cid != merge_to_id]
                        print(f"📋 New format: Selected companies {selected_companies}, removing {companies_to_remove_in_group}")
                    else:
                        # Old format: remove specified companies
                        companies_to_remove_in_group = decision.get('companies_to_remove', [])
                        print(f"📋 Old format: Removing companies {companies_to_remove_in_group}")
                    
                    companies_to_remove.extend(companies_to_remove_in_group)
                    print(f"🗑️ Total companies to remove so far: {len(companies_to_remove)}")
            
            print(f"📋 Summary: {len(name_updates)} name updates, {len(companies_to_remove)} companies to remove")
            
            # Update company names first
            if name_updates:
                print("🏷️ Updating company names...")
                for company_id, new_name in name_updates.items():
                    print(f"Updating {company_id} -> {new_name}")
                    self._update_company_name(company_id, new_name)
                print("✅ Company names updated")
            
            # Remove duplicate companies with cascading
            if companies_to_remove:
                print(f"🗑️ Removing {len(companies_to_remove)} companies with cascading...")
                self._remove_companies(companies_to_remove)
                print("✅ Companies removed with cascading")
            
            # Reassign data from merged companies to kept companies
            print("🔄 Reassigning merged data...")
            try:
                self.reassign_merged_data(merge_decisions)
                print("✅ Data reassignment completed")
            except Exception as e:
                print(f"⚠️ Warning: Data reassignment had issues: {e}")
                # Continue anyway as the main merge was successful
            
            result_message = f"Successfully merged companies with database cascading. Removed {len(companies_to_remove)} duplicates, updated {len(name_updates)} names."
            print(f"🎉 {result_message}")
            return True, result_message
        
        except Exception as e:
            error_msg = f"Error during merge: {str(e)}"
            print(f"❌ Exception in merge_companies: {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg
    
    def _update_company_name(self, company_id, new_name):
        """Update company name in database"""
        try:
            conn = get_db_connection()
            if not conn:
                raise Exception("Could not establish database connection")
                
            cur = conn.cursor()
            try:
                cur.execute(
                    "UPDATE company SET name = %s WHERE company_id = %s",
                    (new_name, company_id)
                )
                conn.commit()
                print(f"✅ Updated company {company_id} name to: {new_name}")
            finally:
                cur.close()
        except Exception as e:
            print(f"Error updating company name: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _remove_companies(self, company_ids):
        """Remove companies from database with cascading updates to related tables"""
        if not company_ids:
            return
            
        try:
            # Use raw psycopg2 connection for transaction control
            conn = get_db_connection()
            if not conn:
                raise Exception("Could not establish database connection")
                
            cur = conn.cursor()
            
            try:
                # Start transaction
                cur.execute("BEGIN;")
                
                # First, get the company IDs that we're removing and the one we're keeping
                # Find the company to keep (not in removal list) from the same merge decision
                placeholders = ','.join(['%s'] * len(company_ids))
                
                # For each company being removed, update all related tables
                for company_id in company_ids:
                    print(f"Processing cascade for company ID: {company_id}")
                    
                    # Update vehicles table - reassign vehicles to the kept company
                    # For now, we'll mark these as merged and let admin handle reassignment
                    cur.execute("""
                        UPDATE vehicle 
                        SET company_id = NULL, 
                            license_plate = CONCAT('[MERGED] ', license_plate)
                        WHERE company_id = %s;
                    """, (company_id,))
                    print(f"Updated {cur.rowcount} vehicles for company {company_id}")
                    
                    # Update weigh_events through vehicles - this is more complex
                    # We need to find all weigh events for vehicles that belonged to this company
                    cur.execute("""
                        UPDATE weigh_event 
                        SET remarks = CASE 
                            WHEN remarks IS NULL OR remarks = '' THEN '[COMPANY_MERGED]'
                            ELSE CONCAT(remarks, ' [COMPANY_MERGED]')
                        END
                        WHERE vehicle_id IN (
                            SELECT vehicle_id FROM vehicle WHERE company_id IS NULL 
                            AND license_plate LIKE '[MERGED]%%'
                        );
                    """)
                    print(f"Updated weigh events for merged company {company_id}")
                
                # Finally, mark the companies as merged (soft delete)
                cur.execute(f"""
                    UPDATE company 
                    SET name = CONCAT('[MERGED] ', name)
                    WHERE company_id IN ({placeholders});
                """, company_ids)
                print(f"Marked {cur.rowcount} companies as merged")
                
                # Commit transaction
                cur.execute("COMMIT;")
                print("✅ Company merge cascade completed successfully")
                
            except Exception as e:
                # Rollback on error
                cur.execute("ROLLBACK;")
                print(f"❌ Error during cascade, rolled back: {e}")
                raise
            finally:
                cur.close()
                
        except Exception as e:
            print(f"Error in company removal cascade: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def reassign_merged_data(self, merge_decisions):
        """
        Reassign data from merged companies to the kept company
        This is called after the main merge to properly reassign vehicles and events
        """
        if not merge_decisions:
            return
            
        try:
            conn = get_db_connection()
            if not conn:
                raise Exception("Could not establish database connection")
                
            cur = conn.cursor()
            
            try:
                cur.execute("BEGIN;")
                
                for decision in merge_decisions:
                    if decision['action'] == 'merge':
                        keep_company_id = decision['merge_to_id']
                        remove_company_ids = decision.get('companies_to_remove', [])
                        
                        for remove_id in remove_company_ids:
                            # Reassign vehicles to the kept company
                            cur.execute("""
                                UPDATE vehicle 
                                SET company_id = %s,
                                    license_plate = REPLACE(license_plate, '[MERGED] ', '')
                                WHERE company_id IS NULL 
                                AND license_plate LIKE '[MERGED]%%';
                            """, (keep_company_id,))
                            
                            print(f"Reassigned vehicles from {remove_id} to {keep_company_id}")
                
                cur.execute("COMMIT;")
                print("✅ Data reassignment completed successfully")
                
            except Exception as e:
                cur.execute("ROLLBACK;")
                print(f"❌ Error during reassignment, rolled back: {e}")
                raise
            finally:
                cur.close()
                
        except Exception as e:
            print(f"Error in data reassignment: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def get_companies_by_pattern(self, pattern):
        """Find companies matching a specific pattern (for targeted analysis)"""
        if self.companies_df is None:
            return []
        
        pattern_lower = pattern.lower()
        matching_companies = []
        
        for _, company in self.companies_df.iterrows():
            if pattern_lower in str(company['name']).lower():
                matching_companies.append({
                    'company_id': company['company_id'],
                    'name': company['name'],
                    'type_code': company.get('type_code', None),
                    'location': company.get('location', None)
                })
        
        return matching_companies
    
    def export_duplicate_report(self, output_path=None):
        """Export duplicate analysis report as JSON"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"duplicate_report_{timestamp}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.get_duplicate_summary(),
            'duplicate_groups': self.duplicate_groups,
            'settings': {
                'similarity_threshold': self.similarity_threshold
            }
        }
        
        try:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            return output_path
        except Exception as e:
            print(f"Error exporting report: {e}")
            return None