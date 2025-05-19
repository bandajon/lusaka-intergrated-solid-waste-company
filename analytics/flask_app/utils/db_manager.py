import psycopg2
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from pathlib import Path
import json
import time
from datetime import datetime
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Flask-compatible version of the database manager"""
    
    def __init__(self):
        # Default database parameters (will be updated in get_db_params)
        self.db_params = {
            'host': 'agripredict-prime-prod.caraj6fzskso.eu-west-2.rds.amazonaws.com',
            'database': 'users',
            'user': 'agripredict',
            'password': 'Wee8fdm0k2!!',
            'port': 5432
        }
        
        # Tables we manage
        self.tables = ['company', 'vehicle', 'weigh_event']
    
    def get_db_params(self):
        """Get database parameters from app config when within app context"""
        try:
            from flask import current_app
            # Update DB params from app config if available
            self.db_params = {
                'host': current_app.config['DB_HOST'],
                'database': current_app.config['DB_NAME'],
                'user': current_app.config['DB_USER'],
                'password': current_app.config['DB_PASS'],
                'port': current_app.config['DB_PORT']
            }
        except RuntimeError:
            # Outside app context, use default params
            pass
        return self.db_params
    
    def get_connection(self, max_retries=3, retry_delay=5):
        """Get a database connection with retry logic"""
        # Ensure db_params is updated from app config if in app context
        db_params = self.get_db_params()
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Connection attempt {attempt + 1}/{max_retries}...")
                conn = psycopg2.connect(**db_params)
                logger.info("Connection established")
                return conn
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to connect after {max_retries} attempts")
                    raise
    
    def get_engine(self):
        """Get SQLAlchemy engine for more complex operations"""
        # Ensure db_params is updated from app config if in app context
        db_params = self.get_db_params()
        conn_string = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"
        return create_engine(conn_string)
    
    def list_tables(self):
        """Get a list of available tables in the database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            tables = [record[0] for record in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return tables
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return self.tables  # Fall back to predefined tables
    
    def get_table_counts_dict(self):
        """Get row counts for each table as a dictionary"""
        counts = {}
        try:
            engine = self.get_engine()
            
            with engine.connect() as connection:
                connection.execution_options(isolation_level="AUTOCOMMIT")
                
                for table in self.tables:
                    try:
                        result = pd.read_sql(f"SELECT COUNT(*) FROM {table}", connection)
                        counts[table] = int(result.iloc[0, 0])
                    except Exception as e:
                        logger.error(f"Error getting count for table {table}: {e}")
                        counts[table] = 0
        except Exception as e:
            logger.error(f"Error getting table counts: {e}")
        
        return counts
    
    def get_table_data(self, table, limit=1000):
        """Get data from a table"""
        try:
            engine = self.get_engine()
            
            # Check if table exists in our managed tables
            if table not in self.tables and table not in self.list_tables():
                logger.error(f"Table {table} does not exist")
                return None
            
            # Get data
            df = pd.read_sql(f"SELECT * FROM {table} LIMIT {limit}", engine)
            return df
        
        except Exception as e:
            logger.error(f"Error getting data from table {table}: {e}")
            return None
    
    def truncate_table(self, table):
        """Truncate a specific table"""
        try:
            # Check if table exists in our managed tables
            if table not in self.tables and table not in self.list_tables():
                logger.error(f"Table {table} does not exist or is not managed")
                return False
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            logger.info(f"Truncating table '{table}'...")
            
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
                logger.info(f"Table '{table}' is referenced by foreign keys")
                for ref in references:
                    logger.info(f"  - {ref[0]}.{ref[1]} references {ref[2]}.{ref[3]}")
                    
                logger.info("Using CASCADE to truncate table and dependent data")
                cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
            else:
                cursor.execute(f"TRUNCATE TABLE {table}")
            
            conn.commit()
            logger.info(f"Table '{table}' truncated successfully")
            
            cursor.close()
            conn.close()
            
            return True
        
        except Exception as e:
            logger.error(f"Error truncating table '{table}': {e}")
            return False
    
    def export_table(self, table):
        """Export a table to CSV"""
        try:
            # Check if table exists in our managed tables
            if table not in self.tables and table not in self.list_tables():
                logger.error(f"Table {table} does not exist or is not managed")
                return None
            
            engine = self.get_engine()
            
            logger.info(f"Exporting table '{table}' to CSV...")
            
            # Read the table
            df = pd.read_sql(f"SELECT * FROM {table}", engine)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"db_export_{table}_{timestamp}.csv"
            
            # Save to CSV
            df.to_csv(filename, index=False)
            
            logger.info(f"Exported {len(df)} rows to '{filename}'")
            
            return filename
        
        except Exception as e:
            logger.error(f"Error exporting table '{table}': {e}")
            return None
    
    def import_table(self, table, file_path):
        """Import data from CSV to a table"""
        try:
            # Check if file exists
            if not Path(file_path).exists():
                logger.error(f"File not found: {file_path}")
                return False
            
            # Check if table exists in our managed tables
            if table not in self.tables and table not in self.list_tables():
                logger.error(f"Table {table} does not exist or is not managed")
                return False
            
            # Use specialized import functions for specific tables
            if table == 'vehicle':
                return self.import_vehicles(file_path)
            elif table == 'company':
                return self.import_companies(file_path)
            
            # For other tables, use a more generic import
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            logger.info(f"Importing {len(df)} rows to table '{table}' from '{file_path}'...")
            
            # Get column information from the table
            engine = self.get_engine()
            with engine.connect() as connection:
                table_cols = pd.read_sql(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'", connection)
                table_columns = table_cols['column_name'].tolist()
            
            logger.info(f"Table columns: {', '.join(table_columns)}")
            logger.info(f"CSV columns: {', '.join(df.columns)}")
            
            # Check for required columns
            missing_cols = [col for col in table_columns if col not in df.columns and col not in ['id', 'created_at', 'updated_at']]
            if missing_cols:
                logger.warning(f"Missing columns in CSV: {', '.join(missing_cols)}")
            
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
            
            # Process in batches
            for i in range(0, len(df), BATCH_SIZE):
                batch = df.iloc[i:i+BATCH_SIZE]
                
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
                                # Skip error rows
                                skipped += 1
                                error_count += 1
                                logger.error(f"Error inserting row: {e}")
                                conn.rollback()
                        
                        except Exception as e:
                            skipped += 1
                            error_count += 1
                            logger.error(f"Error processing row: {e}")
                    
                    # Commit after processing all rows in batch
                    conn.commit()
                    
                except Exception as batch_error:
                    # If batch fails, rollback
                    logger.error(f"Batch error: {batch_error}")
                    conn.rollback()
                
                # Report progress
                if i % (BATCH_SIZE * 10) == 0:
                    logger.info(f"Progress: {imported} imported, {skipped} skipped, {error_count} errors")
            
            cursor.close()
            conn.close()
            
            logger.info(f"Import complete: {imported} rows imported, {skipped} rows skipped, {error_count} errors")
            
            return True
        
        except Exception as e:
            logger.error(f"Error importing to table '{table}': {e}")
            
            # Attempt to rollback any pending transactions
            try:
                if 'conn' in locals() and conn:
                    conn.rollback()
                    conn.close()
            except Exception:
                pass
            
            return False
    
    def import_vehicles(self, file_path):
        """Import vehicle data with new UUIDs to avoid conflicts and ensure no duplicate license plates"""
        try:
            # Check if file exists
            if not Path(file_path).exists():
                logger.error(f"File not found: {file_path}")
                return False
            
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            logger.info(f"Importing {len(df)} vehicles from '{file_path}'...")
            logger.info("Generating new UUIDs for all vehicles to avoid conflicts")
            
            # Check for license_plate column which is required
            if 'license_plate' not in df.columns:
                logger.error(f"Missing 'license_plate' column which is required")
                return False
            
            # Pre-process: Clean and standardize license plates
            logger.info("Cleaning and standardizing license plates...")
            
            # Using the existing license plate cleaner if available
            try:
                from .plate_cleaner import clean_license_plate
                has_cleaner = True
                logger.info("Using plate_cleaner for standardization")
            except ImportError:
                has_cleaner = False
                logger.info("plate_cleaner not found, using basic cleaning")
                
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
                logger.warning(f"{len(empty_plates)} plates were rejected by the cleaner")
            
            # Check for duplicate license plates in the input data
            duplicates_in_input = df[df['cleaned_plate'] != ''].duplicated(subset=['cleaned_plate'], keep=False)
            input_duplicates = df[duplicates_in_input]
            if not input_duplicates.empty:
                logger.warning(f"Found {len(input_duplicates)} rows with duplicate license plates in the input file")
                
                # Group duplicates for logging
                dup_groups = input_duplicates.groupby('cleaned_plate')
                logger.info(f"Found {len(dup_groups)} duplicate plate groups")
            
            # Get vehicle table columns and check existing plates
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
                    logger.info(f"Found {len(existing_plates)} existing license plates in the database")
                    
                    # Check for conflicts with database
                    conflicts_with_db = df[df['cleaned_plate'].isin(existing_plates)]
                    if not conflicts_with_db.empty:
                        logger.warning(f"Found {len(conflicts_with_db)} plates that already exist in the database")
            
            # Connect to database with psycopg2 for more control
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SET statement_timeout = '900000'")  # 15 minutes
            
            # Count before import
            cursor.execute("SELECT COUNT(*) FROM vehicle")
            before_count = cursor.fetchone()[0]
            logger.info(f"Current vehicle count: {before_count}")
            
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
                            logger.error(f"Error inserting vehicle {error_msg}")
                    
                    except Exception as row_error:
                        error_count += 1
                        error_msg = f"{license_plate if 'license_plate' in locals() else 'unknown'}: {str(row_error)[:100]}..."
                        skipped_records['errors'].append(error_msg)
                        logger.error(f"Error processing vehicle row: {error_msg}")
                
                # Commit after each batch
                conn.commit()
                
                # Show progress
                if i % (BATCH_SIZE * 5) == 0 or i + BATCH_SIZE >= len(df):
                    total_skipped = skipped_empty + skipped_duplicates_input + skipped_duplicates_db
                    logger.info(f"Progress: {imported}/{len(df)} vehicles imported ({total_skipped} skipped, {error_count} errors)")
            
            # Save UUID mapping to a file if needed
            if id_mapping:
                mapping_file = f"vehicle_id_mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(mapping_file, 'w') as f:
                    json.dump(id_mapping, f, indent=2)
                logger.info(f"Saved mapping of {len(id_mapping)} old IDs to new UUIDs in {mapping_file}")
            
            # Save skipped records to a CSV for reference
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
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
                logger.info(f"Saved list of {len(skipped_data)} skipped plates to {skipped_file}")
            
            # Count after import
            cursor.execute("SELECT COUNT(*) FROM vehicle")
            after_count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            # Report final statistics
            logger.info(f"Vehicle import complete:")
            logger.info(f"Before: {before_count} vehicles")
            logger.info(f"After: {after_count} vehicles")
            logger.info(f"Net change: +{after_count - before_count} vehicles")
            logger.info(f"Successfully imported: {imported} vehicles")
            logger.info(f"Skipped: {skipped_empty + skipped_duplicates_input + skipped_duplicates_db} vehicles")
            logger.info(f"Empty/invalid plates: {skipped_empty}")
            logger.info(f"Duplicates within input file: {skipped_duplicates_input}")
            logger.info(f"Duplicates with database: {skipped_duplicates_db}")
            logger.info(f"Errors: {error_count}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error importing vehicles: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Attempt to rollback any pending transactions
            try:
                if 'conn' in locals() and conn:
                    conn.rollback()
                    conn.close()
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {rollback_error}")
            
            return False

    def import_companies(self, file_path):
        """Import company data with new UUIDs to avoid conflicts"""
        try:
            # Check if file exists
            if not Path(file_path).exists():
                logger.error(f"File not found: {file_path}")
                return False
            
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            logger.info(f"Importing {len(df)} companies from '{file_path}'...")
            logger.info("Generating new UUIDs for all companies to avoid conflicts")
            
            # Check for name column which is required
            if 'name' not in df.columns:
                logger.error(f"Missing 'name' column which is required")
                return False
            
            # Get company table columns
            engine = self.get_engine()
            with engine.connect() as connection:
                table_cols = pd.read_sql("SELECT column_name FROM information_schema.columns WHERE table_name = 'company'", connection)
                table_columns = table_cols['column_name'].tolist()
            
            # Connect to database with psycopg2 for more control
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SET statement_timeout = '900000'")  # 15 minutes
            
            # Count before import
            cursor.execute("SELECT COUNT(*) FROM company")
            before_count = cursor.fetchone()[0]
            logger.info(f"Current company count: {before_count}")
            
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
                        
                        # Add any other available columns that match the database
                        for col in table_columns:
                            if col not in ['company_id', 'name', 'type_code', 'primary_contact_name', 'primary_contact_phone'] and col in row.index and not pd.isna(row[col]):
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
                            logger.error(f"Error inserting company '{company_name}': {str(e)[:100]}...")
                    
                    except Exception as row_error:
                        error_count += 1
                        logger.error(f"Error processing company row: {str(row_error)[:100]}...")
                
                # Commit after each batch
                conn.commit()
                
                # Show progress
                if i % (BATCH_SIZE * 2) == 0 or i + BATCH_SIZE >= len(df):
                    logger.info(f"Progress: {imported}/{len(df)} companies imported ({skipped} skipped, {error_count} errors)")
            
            # Save UUID mapping to a file
            if id_mapping:
                mapping_file = f"company_id_mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(mapping_file, 'w') as f:
                    json.dump(id_mapping, f, indent=2)
                logger.info(f"Saved mapping of {len(id_mapping)} old IDs to new UUIDs in {mapping_file}")
            
            # Count after import
            cursor.execute("SELECT COUNT(*) FROM company")
            after_count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            # Report final statistics
            logger.info(f"Company import complete:")
            logger.info(f"Before: {before_count} companies")
            logger.info(f"After: {after_count} companies")
            logger.info(f"Net change: +{after_count - before_count} companies")
            logger.info(f"Successfully imported: {imported} companies")
            logger.info(f"Skipped: {skipped} companies")
            logger.info(f"Errors: {error_count}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error importing companies: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Attempt to rollback any pending transactions
            try:
                if 'conn' in locals() and conn:
                    conn.rollback()
                    conn.close()
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {rollback_error}")
            
            return False