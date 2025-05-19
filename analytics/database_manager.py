import pandas as pd
import numpy as np
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
import logging
import psycopg2
from sqlalchemy import create_engine
from pathlib import Path
import json
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection parameters
DB_PARAMS = {
    'host': 'agripredict-prime-prod.caraj6fzskso.eu-west-2.rds.amazonaws.com',
    'database': 'users',
    'user': 'agripredict',
    'password': 'Wee8fdm0k2!!',
    'port': 5432
}

# Database tables we want to manage
TABLES = [
    'company',
    'vehicle',
    'weigh_event'
]

class DatabaseManager:
    """Interface for database operations"""
    
    def __init__(self):
        self.db_params = DB_PARAMS
        self.tables = TABLES
        self.status_output = widgets.Output()
        self.file_selector = None
        self.table_selector = None
        self.action_selector = None
        self.truncate_button = None
        self.import_button = None
        self.export_button = None
        self.connection = None
        self.engine = None
        
    def get_connection(self, max_retries=3, retry_delay=5):
        """Get a database connection with retry logic"""
        with self.status_output:
            for attempt in range(max_retries):
                try:
                    print(f"Connection attempt {attempt + 1}/{max_retries}...")
                    conn = psycopg2.connect(**self.db_params)
                    print("✅ Connection established")
                    return conn
                except Exception as e:
                    print(f"Connection attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        print(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        print(f"❌ Failed to connect after {max_retries} attempts")
                        raise
    
    def get_engine(self):
        """Get SQLAlchemy engine for more complex operations"""
        # Always create a fresh engine to avoid transaction issues
        conn_string = f"postgresql://{self.db_params['user']}:{self.db_params['password']}@{self.db_params['host']}:{self.db_params['port']}/{self.db_params['database']}"
        return create_engine(conn_string)
    
    def check_tables(self):
        """Check if all required tables exist"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            tables = [record[0] for record in cursor.fetchall()]
            
            with self.status_output:
                print(f"📋 Available tables: {', '.join(tables)}")
                
                missing_tables = [table for table in self.tables if table not in tables]
                if missing_tables:
                    print(f"⚠️ Missing tables: {', '.join(missing_tables)}")
                else:
                    print("✅ All required tables exist")
                
            cursor.close()
            conn.close()
            return tables
        except Exception as e:
            with self.status_output:
                print(f"❌ Error checking tables: {e}")
            return []
    
    def get_table_counts(self):
        """Get row counts for each table"""
        counts = {}
        try:
            # Create a fresh connection each time to avoid transaction issues
            conn_string = f"postgresql://{self.db_params['user']}:{self.db_params['password']}@{self.db_params['host']}:{self.db_params['port']}/{self.db_params['database']}"
            engine = create_engine(conn_string)
            
            with engine.connect() as connection:
                # Explicitly set autocommit to avoid transaction issues
                connection.execution_options(isolation_level="AUTOCOMMIT")
                
                for table in self.tables:
                    try:
                        result = pd.read_sql(f"SELECT COUNT(*) FROM {table}", connection)
                        counts[table] = result.iloc[0, 0]
                    except Exception as e:
                        counts[table] = f"Error: {e}"
            
            with self.status_output:
                print("\n📊 Table Row Counts:")
                for table, count in counts.items():
                    print(f"- {table}: {count}")
        except Exception as e:
            with self.status_output:
                print(f"❌ Error getting table counts: {e}")
        
        return counts
    
    def truncate_table(self, table):
        """Truncate a specific table"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            with self.status_output:
                print(f"🔄 Truncating table '{table}'...")
                
                # Check if table is referenced by foreign keys
                cursor.execute(f"""
                    SELECT
                        tc.table_name as referencing_table,
                        kcu.column_name as referencing_column,
                        ccu.table_name as referenced_table,
                        ccu.column_name as referenced_column
                    FROM
                        information_schema.table_constraints AS tc
                        JOIN information_schema.key_column_usage AS kcu
                          ON tc.constraint_name = kcu.constraint_name
                          AND tc.table_schema = kcu.table_schema
                        JOIN information_schema.constraint_column_usage AS ccu
                          ON ccu.constraint_name = tc.constraint_name
                          AND ccu.table_schema = tc.table_schema
                    WHERE constraint_type = 'FOREIGN KEY'
                    AND ccu.table_name = %s;
                """, (table,))
                
                references = cursor.fetchall()
                if references:
                    print(f"⚠️ Table '{table}' is referenced by foreign keys:")
                    for ref in references:
                        print(f"  - {ref[0]}.{ref[1]} references {ref[2]}.{ref[3]}")
                        
                    print("Using CASCADE to truncate table and dependent data")
                    cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
                else:
                    cursor.execute(f"TRUNCATE TABLE {table}")
                
                conn.commit()
                print(f"✅ Table '{table}' truncated successfully")
            
            cursor.close()
            conn.close()
            
            # Update table counts
            self.get_table_counts()
            return True
        
        except Exception as e:
            with self.status_output:
                print(f"❌ Error truncating table '{table}': {e}")
            return False
    
    def truncate_all_tables(self):
        """Truncate all tables in the correct order to handle dependencies"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            with self.status_output:
                print("🔄 Truncating all tables...")
                
                # Truncate in reverse order to handle dependencies
                for table in reversed(self.tables):
                    print(f"  - Truncating '{table}'...")
                    cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
                
                conn.commit()
                print("✅ All tables truncated successfully")
            
            cursor.close()
            conn.close()
            
            # Update table counts
            self.get_table_counts()
            return True
        
        except Exception as e:
            with self.status_output:
                print(f"❌ Error truncating all tables: {e}")
            return False
    
    def export_table(self, table):
        """Export a table to CSV"""
        try:
            engine = self.get_engine()
            
            with self.status_output:
                print(f"🔄 Exporting table '{table}' to CSV...")
                
                # Read the table
                df = pd.read_sql(f"SELECT * FROM {table}", engine)
                
                # Create filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"db_export_{table}_{timestamp}.csv"
                
                # Save to CSV
                df.to_csv(filename, index=False)
                
                print(f"✅ Exported {len(df)} rows to '{filename}'")
            
            return filename
        
        except Exception as e:
            with self.status_output:
                print(f"❌ Error exporting table '{table}': {e}")
            return None
    
    def export_all_tables(self):
        """Export all tables to CSV files"""
        exported_files = []
        
        with self.status_output:
            print("🔄 Exporting all tables to CSV...")
        
        for table in self.tables:
            filename = self.export_table(table)
            if filename:
                exported_files.append(filename)
        
        with self.status_output:
            if exported_files:
                print(f"✅ Exported {len(exported_files)} tables")
            else:
                print("❌ Failed to export any tables")
        
        return exported_files
    
    def import_table(self, table, file_path):
        """Import data from CSV to a table with enhanced reliability"""
        try:
            # Check if file exists
            if not Path(file_path).exists():
                with self.status_output:
                    print(f"❌ File not found: {file_path}")
                return False
            
            # Use specialized import functions for specific tables
            if table == 'vehicle':
                return self.import_vehicles(file_path)
            elif table == 'company':
                return self.import_companies(file_path)
            
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            with self.status_output:
                print(f"🔄 Importing {len(df)} rows to table '{table}' from '{file_path}'...")
                
                # Get column information from the table
                engine = self.get_engine()
                with engine.connect() as connection:
                    table_cols = pd.read_sql(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'", connection)
                    table_columns = table_cols['column_name'].tolist()
                
                print(f"  - Table columns: {', '.join(table_columns)}")
                print(f"  - CSV columns: {', '.join(df.columns)}")
                
                # Check for required columns
                missing_cols = [col for col in table_columns if col not in df.columns and col not in ['id', 'created_at', 'updated_at']]
                if missing_cols:
                    print(f"⚠️ Missing columns in CSV: {', '.join(missing_cols)}")
                    print("Will proceed with import anyway, missing columns will be NULL")
                    print("Please wait...")
                
                # Connect to database
                conn = self.get_connection()
                cursor = conn.cursor()
                
                # Set longer timeout for batch operations
                cursor.execute("SET statement_timeout = '600000'")  # 10 minutes
                
                # Import in smaller batches with more error handling
                BATCH_SIZE = 50  # Smaller batch size for more frequent commits
                imported = 0
                skipped = 0
                error_count = 0
                
                # Save failed rows to retry later
                failed_rows = []
                
                for i in range(0, len(df), BATCH_SIZE):
                    batch = df.iloc[i:i+BATCH_SIZE]
                    batch_failed = False
                    
                    try:
                        for _, row in batch.iterrows():
                            try:
                                # Prepare columns and values
                                valid_cols = [col for col in row.index if col in table_columns and pd.notna(row[col])]
                                values = [row[col] for col in valid_cols]
                                placeholders = ['%s'] * len(valid_cols)
                                
                                # Skip empty rows
                                if not valid_cols:
                                    skipped += 1
                                    continue
                                
                                # Create and execute SQL
                                sql = f"INSERT INTO {table} ({', '.join(valid_cols)}) VALUES ({', '.join(placeholders)})"
                                
                                try:
                                    cursor.execute(sql, values)
                                    imported += 1
                                except psycopg2.errors.UniqueViolation:
                                    # Skip duplicates
                                    skipped += 1
                                    conn.rollback()  # Roll back transaction to continue
                                except Exception as e:
                                    # Save failed row for retry
                                    failed_rows.append(row)
                                    skipped += 1
                                    error_count += 1
                                    conn.rollback()
                            
                            except Exception as e:
                                skipped += 1
                                error_count += 1
                                print(f"  ⚠️ Error processing row: {e}")
                        
                        # Commit after processing all rows in batch (if no errors)
                        conn.commit()
                        
                    except Exception as batch_error:
                        # If batch fails, rollback and try individual rows
                        print(f"  ⚠️ Batch error: {batch_error}")
                        conn.rollback()
                        batch_failed = True
                    
                    # Report progress
                    if i % (BATCH_SIZE * 10) == 0 or batch_failed:
                        print(f"  - Progress: {imported} imported, {skipped} skipped, {error_count} errors")
                
                # Try to import failed rows one by one
                if failed_rows:
                    print(f"Retrying {len(failed_rows)} failed rows individually...")
                    retry_success = 0
                    
                    for row in failed_rows:
                        try:
                            # Prepare columns and values
                            valid_cols = [col for col in row.index if col in table_columns and pd.notna(row[col])]
                            values = [row[col] for col in valid_cols]
                            placeholders = ['%s'] * len(valid_cols)
                            
                            # Create and execute SQL
                            sql = f"INSERT INTO {table} ({', '.join(valid_cols)}) VALUES ({', '.join(placeholders)})"
                            
                            cursor.execute(sql, values)
                            conn.commit()
                            retry_success += 1
                            imported += 1
                            skipped -= 1  # Adjust since we counted this as skipped earlier
                            
                        except Exception as retry_error:
                            conn.rollback()
                    
                    print(f"Retry results: {retry_success} of {len(failed_rows)} succeeded")
                
                cursor.close()
                conn.close()
                
                print(f"✅ Import complete: {imported} rows imported, {skipped} rows skipped, {error_count} errors")
                
                # Update table counts
                self.get_table_counts()
                
                return True
        
        except Exception as e:
            with self.status_output:
                print(f"❌ Error importing to table '{table}': {e}")
                import traceback
                traceback.print_exc()
                
                # Attempt to rollback any pending transactions
                try:
                    if 'conn' in locals() and conn:
                        print("Attempting to rollback any pending transactions...")
                        conn.rollback()
                        conn.close()
                except Exception as rollback_error:
                    print(f"Error during rollback: {rollback_error}")
                
                # Reset the engine to clear any bad connections
                try:
                    self.engine = None
                except:
                    pass
            return False
            
    def import_vehicles(self, file_path):
        """Import vehicle data with new UUIDs to avoid conflicts and ensure no duplicate license plates"""
        try:
            # Check if file exists
            if not Path(file_path).exists():
                with self.status_output:
                    print(f"❌ File not found: {file_path}")
                return False
            
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            with self.status_output:
                print(f"🔄 Importing {len(df)} vehicles from '{file_path}'...")
                print("🔑 Generating new UUIDs for all vehicles to avoid conflicts")
                
                # Check for license_plate column which is required
                if 'license_plate' not in df.columns:
                    print(f"❌ Missing 'license_plate' column which is required")
                    return False
                
                # Pre-process: Clean and standardize license plates
                print("🧹 Cleaning and standardizing license plates...")
                
                # Using the existing license plate cleaner if available
                try:
                    from vehicle_plate_cleaner import clean_license_plate
                    has_cleaner = True
                    print("  ✓ Using vehicle_plate_cleaner for standardization")
                except ImportError:
                    has_cleaner = False
                    print("  ⚠️ vehicle_plate_cleaner not found, using basic cleaning")
                    
                # Basic cleaning function if the cleaner is not available
                def basic_clean_plate(plate):
                    if pd.isna(plate) or not plate:
                        return ""
                    return str(plate).strip().upper().replace(" ", "")
                
                # Apply cleaning function to all plates
                if has_cleaner:
                    df['cleaned_plate'] = df['license_plate'].apply(clean_license_plate)
                else:
                    df['cleaned_plate'] = df['license_plate'].apply(basic_clean_plate)
                
                # Check for empty cleaned plates (rejected by the cleaner)
                empty_plates = df[df['cleaned_plate'] == '']
                if not empty_plates.empty:
                    print(f"  ⚠️ {len(empty_plates)} plates were rejected by the cleaner (empty strings, just numbers, etc.)")
                    print(f"    Sample rejected plates: {', '.join(empty_plates['license_plate'].head(5).tolist())}")
                    if len(empty_plates) > 5:
                        print(f"    ... and {len(empty_plates) - 5} more")
                
                # Check for duplicate license plates in the input data
                duplicates_in_input = df[df['cleaned_plate'] != ''].duplicated(subset=['cleaned_plate'], keep=False)
                input_duplicates = df[duplicates_in_input]
                if not input_duplicates.empty:
                    print(f"  ⚠️ Found {len(input_duplicates)} rows with duplicate license plates in the input file")
                    
                    # Group duplicates for display
                    dup_groups = input_duplicates.groupby('cleaned_plate')
                    print(f"    Found {len(dup_groups)} duplicate plate groups:")
                    
                    # Show up to 5 duplicate groups
                    for i, (plate, group) in enumerate(dup_groups):
                        if i >= 5:
                            print(f"    ... and {len(dup_groups) - 5} more duplicate groups")
                            break
                        print(f"    Plate '{plate}' appears {len(group)} times with original values: {', '.join(group['license_plate'].tolist())}")
                    
                    # User confirm whether to continue with first occurrence only
                    print("\n⚠️ For duplicate plates in the input, only the first occurrence will be imported.")
                    
                # Get vehicle table columns
                engine = self.get_engine()
                with engine.connect() as connection:
                    table_cols = pd.read_sql("SELECT column_name FROM information_schema.columns WHERE table_name = 'vehicle'", connection)
                    table_columns = table_cols['column_name'].tolist()
                    
                    # Also check for existing license plates in the database
                    existing_plates_df = pd.read_sql("SELECT license_plate FROM vehicle", connection)
                    existing_plates = set()
                    
                    # Clean existing plates for comparison
                    if has_cleaner:
                        for plate in existing_plates_df['license_plate']:
                            if plate and not pd.isna(plate):
                                cleaned = clean_license_plate(plate)
                                if cleaned:
                                    existing_plates.add(cleaned)
                    else:
                        for plate in existing_plates_df['license_plate']:
                            if plate and not pd.isna(plate):
                                cleaned = basic_clean_plate(plate)
                                if cleaned:
                                    existing_plates.add(cleaned)
                    
                    if existing_plates:
                        print(f"  - Found {len(existing_plates)} existing license plates in the database")
                        
                        # Check for conflicts with database
                        conflicts_with_db = df[df['cleaned_plate'].isin(existing_plates)]
                        if not conflicts_with_db.empty:
                            print(f"  ⚠️ Found {len(conflicts_with_db)} plates that already exist in the database")
                            print(f"    Sample conflicting plates: {', '.join(conflicts_with_db['license_plate'].head(5).tolist())}")
                            if len(conflicts_with_db) > 5:
                                print(f"    ... and {len(conflicts_with_db) - 5} more")
                            print("    These plates will be skipped during import.")
                
                # Connect to database with psycopg2 for more control
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute("SET statement_timeout = '900000'")  # 15 minutes
                
                # Count before import
                cursor.execute("SELECT COUNT(*) FROM vehicle")
                before_count = cursor.fetchone()[0]
                print(f"  - Current vehicle count: {before_count}")
                
                # Import in larger batches for better performance
                BATCH_SIZE = 100
                imported = 0
                skipped_empty = 0
                skipped_duplicates_input = 0
                skipped_duplicates_db = 0
                error_count = 0
                
                # Track mapping of old vehicle IDs to new UUIDs if needed
                id_mapping = {}
                
                # Keep track of license plates we've already processed to avoid duplicates
                processed_plates = set()
                
                # Track which plates were skipped and why
                skipped_records = {
                    'empty_plates': [],
                    'duplicates_input': [],
                    'duplicates_db': [],
                    'errors': []
                }
                
                # Process in batches to avoid memory issues with large files
                for i in range(0, len(df), BATCH_SIZE):
                    batch = df.iloc[i:i+BATCH_SIZE]
                    
                    # Process each row in the batch
                    for _, row in batch.iterrows():
                        try:
                            # Get original and cleaned license plate
                            license_plate = row.get('license_plate', '')
                            cleaned_plate = row.get('cleaned_plate', '')
                            
                            # Skip if no license plate or it was rejected by the cleaner
                            if not cleaned_plate:
                                skipped_empty += 1
                                skipped_records['empty_plates'].append(license_plate)
                                continue
                                
                            # Skip if this plate already exists in the database
                            if cleaned_plate in existing_plates:
                                skipped_duplicates_db += 1
                                skipped_records['duplicates_db'].append(license_plate)
                                continue
                                
                            # Skip if we've already processed this plate in the current import
                            if cleaned_plate in processed_plates:
                                skipped_duplicates_input += 1
                                skipped_records['duplicates_input'].append(license_plate)
                                continue
                            
                            # Generate a new UUID for this vehicle
                            import uuid
                            new_vehicle_id = str(uuid.uuid4())
                            
                            # If the CSV has a vehicle_id, save the mapping for reference
                            if 'vehicle_id' in row and not pd.isna(row['vehicle_id']):
                                old_id = row['vehicle_id']
                                id_mapping[old_id] = new_vehicle_id
                            
                            # Use the cleaned plate for insertion, as it's standardized
                            use_plate = cleaned_plate
                            
                            # Prepare values for insertion, using only valid columns
                            columns = ['vehicle_id', 'license_plate']  # Must include these
                            values = [new_vehicle_id, use_plate]
                            
                            # Add any other available columns that match the database
                            for col in table_columns:
                                if col in row.index and col not in ['vehicle_id', 'license_plate'] and not pd.isna(row[col]):
                                    columns.append(col)
                                    values.append(row[col])
                            
                            # Insert the vehicle with new UUID
                            placeholder_str = ', '.join(['%s'] * len(columns))
                            sql = f"INSERT INTO vehicle ({', '.join(columns)}) VALUES ({placeholder_str})"
                            
                            try:
                                cursor.execute(sql, values)
                                imported += 1
                                processed_plates.add(cleaned_plate)  # Mark as processed
                                
                                # Also add to existing plates set to avoid future duplicates in this session
                                existing_plates.add(cleaned_plate)
                                
                            except Exception as e:
                                # If there's an error with this specific insert
                                conn.rollback()
                                error_count += 1
                                error_msg = f"{license_plate}: {str(e)[:100]}..."
                                skipped_records['errors'].append(error_msg)
                                print(f"  - Error inserting vehicle {error_msg}")
                        
                        except Exception as row_error:
                            error_count += 1
                            error_msg = f"{license_plate if 'license_plate' in locals() else 'unknown'}: {str(row_error)[:100]}..."
                            skipped_records['errors'].append(error_msg)
                            print(f"  - Error processing vehicle row: {error_msg}")
                    
                    # Commit after each batch
                    conn.commit()
                    
                    # Show progress
                    if i % (BATCH_SIZE * 5) == 0 or i + BATCH_SIZE >= len(df):
                        total_skipped = skipped_empty + skipped_duplicates_input + skipped_duplicates_db
                        print(f"  - Progress: {imported}/{len(df)} vehicles imported ({total_skipped} skipped, {error_count} errors)")
                
                # Save UUID mapping to a file if needed
                if id_mapping:
                    mapping_file = f"vehicle_id_mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(mapping_file, 'w') as f:
                        import json
                        json.dump(id_mapping, f, indent=2)
                    print(f"  - Saved mapping of {len(id_mapping)} old IDs to new UUIDs in {mapping_file}")
                
                # Save skipped records to a CSV for reference
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                skipped_file = f"skipped_vehicles_{timestamp}.csv"
                
                # Prepare skipped data for CSV
                skipped_data = []
                for reason, plates in skipped_records.items():
                    for plate in plates:
                        skipped_data.append({
                            'license_plate': plate,
                            'reason': reason
                        })
                
                if skipped_data:
                    skipped_df = pd.DataFrame(skipped_data)
                    skipped_df.to_csv(skipped_file, index=False)
                    print(f"  - Saved list of {len(skipped_data)} skipped plates to {skipped_file}")
                
                # Count after import
                cursor.execute("SELECT COUNT(*) FROM vehicle")
                after_count = cursor.fetchone()[0]
                cursor.close()
                conn.close()
                
                # Report final statistics
                print(f"✅ Vehicle import complete:")
                print(f"  - Before: {before_count} vehicles")
                print(f"  - After: {after_count} vehicles")
                print(f"  - Net change: +{after_count - before_count} vehicles")
                print(f"  - Successfully imported: {imported} vehicles")
                print(f"  - Skipped: {skipped_empty + skipped_duplicates_input + skipped_duplicates_db} vehicles")
                print(f"    • Empty/invalid plates: {skipped_empty}")
                print(f"    • Duplicates within input file: {skipped_duplicates_input}")
                print(f"    • Duplicates with database: {skipped_duplicates_db}")
                print(f"  - Errors: {error_count}")
                
                # Update table counts
                self.get_table_counts()
                
                return True
        
        except Exception as e:
            with self.status_output:
                print(f"❌ Error importing vehicles: {e}")
                import traceback
                traceback.print_exc()
                
                # Attempt to rollback any pending transactions
                try:
                    if 'conn' in locals() and conn:
                        print("Attempting to rollback any pending transactions...")
                        conn.rollback()
                        conn.close()
                except Exception as rollback_error:
                    print(f"Error during rollback: {rollback_error}")
            
            return False
            
    def import_companies(self, file_path):
        """Import company data with new UUIDs to avoid conflicts"""
        try:
            # Check if file exists
            if not Path(file_path).exists():
                with self.status_output:
                    print(f"❌ File not found: {file_path}")
                return False
            
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            with self.status_output:
                print(f"🔄 Importing {len(df)} companies from '{file_path}'...")
                print("🔑 Generating new UUIDs for all companies to avoid conflicts")
                
                # Get company table columns
                engine = self.get_engine()
                with engine.connect() as connection:
                    table_cols = pd.read_sql("SELECT column_name FROM information_schema.columns WHERE table_name = 'company'", connection)
                    table_columns = table_cols['column_name'].tolist()
                
                # Check for name column which is required
                if 'name' not in df.columns:
                    print(f"❌ Missing 'name' column which is required")
                    return False
                
                # Connect to database with psycopg2 for more control
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute("SET statement_timeout = '900000'")  # 15 minutes
                
                # Count before import
                cursor.execute("SELECT COUNT(*) FROM company")
                before_count = cursor.fetchone()[0]
                print(f"  - Current company count: {before_count}")
                
                # Import in batches for better performance
                BATCH_SIZE = 50
                imported = 0
                skipped = 0
                error_count = 0
                
                # Track mapping of old company IDs to new UUIDs
                id_mapping = {}
                
                # Keep track of company names we've already imported to avoid duplicates
                imported_names = set()
                
                # Process in batches
                for i in range(0, len(df), BATCH_SIZE):
                    batch = df.iloc[i:i+BATCH_SIZE]
                    
                    # Process each row in the batch
                    for _, row in batch.iterrows():
                        try:
                            # Skip if no name or it's empty
                            company_name = row.get('name')
                            if pd.isna(company_name) or company_name == '':
                                skipped += 1
                                continue
                                
                            # Skip duplicate names (optional - comment out if you want to allow duplicates)
                            if company_name in imported_names:
                                skipped += 1
                                continue
                            
                            # Generate a new UUID for this company
                            import uuid
                            new_company_id = str(uuid.uuid4())
                            
                            # If the CSV has a company_id, save the mapping for reference
                            if 'company_id' in row and not pd.isna(row['company_id']):
                                old_id = row['company_id']
                                id_mapping[old_id] = new_company_id
                            
                            # Get type_code, defaulting to 1 (Private Company) if not present
                            type_code = 1  # Default to Private Company
                            if 'type_code' in row and not pd.isna(row['type_code']):
                                type_code = int(row['type_code'])
                            
                            # Required fields for company table
                            columns = ['company_id', 'name', 'type_code']
                            values = [new_company_id, company_name, type_code]
                            
                            # Add required contact fields with defaults if not provided
                            if 'primary_contact_name' not in row or pd.isna(row['primary_contact_name']):
                                columns.append('primary_contact_name')
                                values.append('Contact Required')
                                
                            if 'primary_contact_phone' not in row or pd.isna(row['primary_contact_phone']):
                                columns.append('primary_contact_phone')
                                values.append('Phone Required')

                            if 'primary_contact_email' not in row or pd.isna(row['primary_contact_email']):
                                columns.append('primary_contact_email')
                                values.append('Email Required')
                            
                            # Add any other available columns that match the database
                            for col in table_columns:
                                if col not in ['company_id', 'name', 'type_code', 'primary_contact_name', 'primary_contact_phone', 'primary_contact_email'] and col in row.index and not pd.isna(row[col]):
                                    columns.append(col)
                                    values.append(row[col])
                            
                            # Insert the company with new UUID
                            placeholder_str = ', '.join(['%s'] * len(columns))
                            sql = f"INSERT INTO company ({', '.join(columns)}) VALUES ({placeholder_str})"
                            
                            try:
                                cursor.execute(sql, values)
                                imported += 1
                                imported_names.add(company_name)  # Mark as imported
                                
                            except Exception as e:
                                # If there's an error with this specific insert
                                conn.rollback()
                                error_count += 1
                                print(f"  - Error inserting company '{company_name}': {str(e)[:100]}...")
                        
                        except Exception as row_error:
                            error_count += 1
                            print(f"  - Error processing company row: {str(row_error)[:100]}...")
                    
                    # Commit after each batch
                    conn.commit()
                    
                    # Show progress
                    if i % (BATCH_SIZE * 2) == 0 or i + BATCH_SIZE >= len(df):
                        print(f"  - Progress: {imported}/{len(df)} companies imported ({skipped} skipped, {error_count} errors)")
                
                # Save UUID mapping to a file
                if id_mapping:
                    mapping_file = f"company_id_mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(mapping_file, 'w') as f:
                        import json
                        json.dump(id_mapping, f, indent=2)
                    print(f"  - Saved mapping of {len(id_mapping)} old IDs to new UUIDs in {mapping_file}")
                
                # Count after import
                cursor.execute("SELECT COUNT(*) FROM company")
                after_count = cursor.fetchone()[0]
                cursor.close()
                conn.close()
                
                # Report final statistics
                print(f"✅ Company import complete:")
                print(f"  - Before: {before_count} companies")
                print(f"  - After: {after_count} companies")
                print(f"  - Net change: +{after_count - before_count} companies")
                print(f"  - Successfully imported: {imported} companies")
                print(f"  - Skipped: {skipped} companies")
                print(f"  - Errors: {error_count}")
                
                # Update table counts
                self.get_table_counts()
                
                return True
        
        except Exception as e:
            with self.status_output:
                print(f"❌ Error importing companies: {e}")
                import traceback
                traceback.print_exc()
                
                # Attempt to rollback any pending transactions
                try:
                    if 'conn' in locals() and conn:
                        print("Attempting to rollback any pending transactions...")
                        conn.rollback()
                        conn.close()
                except Exception as rollback_error:
                    print(f"Error during rollback: {rollback_error}")
            
            return False
    
    def create_interface(self):
        """Create an interactive interface for database operations"""
        # Get list of CSV files in the current directory
        csv_files = list(Path('.').glob('*.csv'))
        csv_options = [(file.name, str(file)) for file in csv_files]
        
        # Create output area
        self.status_output = widgets.Output()
        
        # Create file selector
        self.file_selector = widgets.Dropdown(
            options=csv_options,
            description='File:',
            disabled=False,
            layout=widgets.Layout(width='70%')
        )
        
        # Create table selector
        self.table_selector = widgets.Dropdown(
            options=self.tables,
            description='Table:',
            disabled=False
        )
        
        # Create action selector
        self.action_selector = widgets.Dropdown(
            options=[
                ('Import data to table', 'import'),
                ('Export table to CSV', 'export'),
                ('Truncate table', 'truncate'),
                ('View table structure', 'structure'),
                ('View row count', 'count')
            ],
            description='Action:',
            disabled=False
        )
        
        # Create buttons
        self.refresh_button = widgets.Button(
            description='🔄 Refresh',
            button_style='info',
            tooltip='Refresh file list and table counts'
        )
        
        self.truncate_button = widgets.Button(
            description='❌ Truncate Table',
            button_style='danger',
            tooltip='Delete all rows from the selected table'
        )
        
        self.truncate_all_button = widgets.Button(
            description='⚠️ Truncate ALL Tables',
            button_style='danger',
            tooltip='Delete all rows from all tables'
        )
        
        self.import_button = widgets.Button(
            description='📥 Import Data',
            button_style='success',
            tooltip='Import data from selected file to selected table'
        )
        
        self.export_button = widgets.Button(
            description='📤 Export Table',
            button_style='primary',
            tooltip='Export selected table to CSV'
        )
        
        self.export_all_button = widgets.Button(
            description='📤 Export ALL Tables',
            button_style='primary',
            tooltip='Export all tables to CSV files'
        )
        
        # Connect button events
        self.refresh_button.on_click(self._on_refresh)
        self.truncate_button.on_click(self._on_truncate)
        self.truncate_all_button.on_click(self._on_truncate_all)
        self.import_button.on_click(self._on_import)
        self.export_button.on_click(self._on_export)
        self.export_all_button.on_click(self._on_export_all)
        
        # Create layout
        title = widgets.HTML("<h2>Database Manager</h2>")
        connection_info = widgets.HTML(f"<p>Connected to: {self.db_params['database']} on {self.db_params['host']}</p>")
        
        selectors = widgets.VBox([
            widgets.HBox([self.table_selector, self.action_selector]),
            widgets.HBox([self.file_selector, self.refresh_button])
        ])
        
        buttons = widgets.HBox([
            self.import_button,
            self.export_button,
            self.export_all_button,
            self.truncate_button,
            self.truncate_all_button
        ])
        
        # Main container
        container = widgets.VBox([
            title,
            connection_info,
            selectors,
            buttons,
            self.status_output
        ])
        
        # Initialize
        self._on_refresh(None)
        
        return container
    
    def _on_refresh(self, button):
        """Refresh file list and table counts"""
        with self.status_output:
            clear_output()
            print("🔄 Refreshing...")
            
            # Update CSV file list
            csv_files = list(Path('.').glob('*.csv'))
            csv_options = [(file.name, str(file)) for file in csv_files]
            self.file_selector.options = csv_options
            
            # Check database connection and tables
            try:
                self.check_tables()
                self.get_table_counts()
            except Exception as e:
                print(f"❌ Error connecting to database: {e}")
    
    def _on_truncate(self, button):
        """Handle truncate button click"""
        table = self.table_selector.value
        
        with self.status_output:
            clear_output()
            print(f"⚠️ Are you sure you want to truncate table '{table}'?")
            print("This will delete ALL data in the table.")
            
            # Create confirmation buttons
            confirm_btn = widgets.Button(
                description='YES - Truncate Table',
                button_style='danger',
                tooltip='Confirm truncate'
            )
            
            cancel_btn = widgets.Button(
                description='Cancel',
                button_style='info',
                tooltip='Cancel operation'
            )
            
            # Handlers
            def on_confirm(b):
                clear_output()
                self.truncate_table(table)
                
            def on_cancel(b):
                clear_output()
                print("❌ Operation cancelled")
            
            confirm_btn.on_click(on_confirm)
            cancel_btn.on_click(on_cancel)
            
            # Display buttons
            display(widgets.HBox([confirm_btn, cancel_btn]))
    
    def _on_truncate_all(self, button):
        """Handle truncate all button click"""
        with self.status_output:
            clear_output()
            print("⚠️ Are you sure you want to truncate ALL tables?")
            print("This will delete ALL data in ALL tables.")
            print(f"Tables to truncate: {', '.join(self.tables)}")
            
            # Create confirmation buttons
            confirm_btn = widgets.Button(
                description='YES - Truncate ALL Tables',
                button_style='danger',
                tooltip='Confirm truncate all tables'
            )
            
            cancel_btn = widgets.Button(
                description='Cancel',
                button_style='info',
                tooltip='Cancel operation'
            )
            
            # Handlers
            def on_confirm(b):
                clear_output()
                self.truncate_all_tables()
                
            def on_cancel(b):
                clear_output()
                print("❌ Operation cancelled")
            
            confirm_btn.on_click(on_confirm)
            cancel_btn.on_click(on_cancel)
            
            # Display buttons
            display(widgets.HBox([confirm_btn, cancel_btn]))
    
    def _on_import(self, button):
        """Handle import button click"""
        file_path = self.file_selector.value
        table = self.table_selector.value
        
        with self.status_output:
            clear_output()
            print(f"🔄 Preparing to import '{file_path}' to table '{table}'...")
            
            # Create confirmation buttons
            confirm_btn = widgets.Button(
                description='YES - Import Data',
                button_style='success',
                tooltip='Confirm import'
            )
            
            cancel_btn = widgets.Button(
                description='Cancel',
                button_style='info',
                tooltip='Cancel operation'
            )
            
            # Handlers
            def on_confirm(b):
                clear_output()
                self.import_table(table, file_path)
                
            def on_cancel(b):
                clear_output()
                print("❌ Operation cancelled")
            
            confirm_btn.on_click(on_confirm)
            cancel_btn.on_click(on_cancel)
            
            # Display buttons
            display(widgets.HBox([confirm_btn, cancel_btn]))
    
    def _on_export(self, button):
        """Handle export button click"""
        table = self.table_selector.value
        
        with self.status_output:
            clear_output()
            self.export_table(table)
    
    def _on_export_all(self, button):
        """Handle export all button click"""
        with self.status_output:
            clear_output()
            self.export_all_tables()

# Create and run interface
def run_interface():
    """Run the database manager interface"""
    manager = DatabaseManager()
    display(manager.create_interface())

if __name__ == "__main__":
    run_interface()