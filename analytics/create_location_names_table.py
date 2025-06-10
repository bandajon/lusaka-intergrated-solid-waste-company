#!/usr/bin/env python3
"""
Script to create location_names table and populate it with data from locations.csv
"""

import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection parameters (using the existing configuration)
DB_PARAMS = {
    'host': 'agripredict-prime-prod.caraj6fzskso.eu-west-2.rds.amazonaws.com',
    'database': 'users',
    'user': 'agripredict',
    'password': 'Wee8fdm0k2!!',
    'port': 5432
}

def get_db_engine():
    """Get SQLAlchemy engine for database operations"""
    conn_string = f"postgresql://{DB_PARAMS['user']}:{DB_PARAMS['password']}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['database']}"
    return create_engine(conn_string)

def get_connection():
    """Get psycopg2 connection for database operations"""
    return psycopg2.connect(**DB_PARAMS)

def create_location_names_table():
    """Create the location_names table"""
    try:
        engine = get_db_engine()
        
        with engine.connect() as conn:
            # Check if table already exists
            check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'location_names'
            );
            """
            exists = conn.execute(text(check_query)).scalar()
            
            if exists:
                logger.info("Table 'location_names' already exists")
                return True
            
            # Create the table
            create_table_query = """
            CREATE TABLE location_names (
                id SERIAL PRIMARY KEY,
                location_name VARCHAR(255) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            conn.execute(text(create_table_query))
            conn.commit()
            logger.info("Successfully created 'location_names' table")
            return True
            
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        return False

def populate_location_names_table(csv_file_path):
    """Populate the location_names table with data from CSV"""
    try:
        # Check if CSV file exists
        if not Path(csv_file_path).exists():
            logger.error(f"CSV file not found: {csv_file_path}")
            return False
        
        # Read CSV file
        df = pd.read_csv(csv_file_path)
        logger.info(f"Read {len(df)} locations from CSV file")
        
        # Check if 'Location' column exists
        if 'Location' not in df.columns:
            logger.error("CSV file must have a 'Location' column")
            return False
        
        # Clean and prepare data
        df = df.dropna(subset=['Location'])  # Remove rows with null location names
        df = df.drop_duplicates(subset=['Location'])  # Remove duplicate location names
        df['location_name'] = df['Location'].str.strip()  # Remove leading/trailing spaces
        
        logger.info(f"After cleaning: {len(df)} unique locations to import")
        
        # Get database connection
        engine = get_db_engine()
        
        with engine.connect() as conn:
            # Insert locations with conflict handling (ignore duplicates)
            inserted_count = 0
            skipped_count = 0
            
            for _, row in df.iterrows():
                location_name = row['location_name']
                
                try:
                    # Try to insert the location
                    insert_query = """
                    INSERT INTO location_names (location_name)
                    VALUES (:location_name)
                    ON CONFLICT (location_name) DO NOTHING
                    RETURNING id;
                    """
                    
                    result = conn.execute(text(insert_query), {'location_name': location_name})
                    
                    if result.rowcount > 0:
                        inserted_count += 1
                    else:
                        skipped_count += 1
                        logger.debug(f"Skipped duplicate location: {location_name}")
                
                except Exception as e:
                    logger.error(f"Error inserting location '{location_name}': {e}")
                    skipped_count += 1
            
            conn.commit()
            
        logger.info(f"Import completed:")
        logger.info(f"  - Inserted: {inserted_count} locations")
        logger.info(f"  - Skipped (duplicates): {skipped_count} locations")
        
        return True
        
    except Exception as e:
        logger.error(f"Error populating table: {e}")
        return False

def verify_data():
    """Verify the data was imported correctly"""
    try:
        engine = get_db_engine()
        
        with engine.connect() as conn:
            # Count total records
            count_query = "SELECT COUNT(*) FROM location_names;"
            total_count = conn.execute(text(count_query)).scalar()
            
            # Get a sample of records
            sample_query = "SELECT id, location_name, created_at FROM location_names ORDER BY id LIMIT 5;"
            sample_records = conn.execute(text(sample_query)).fetchall()
            
        logger.info(f"Verification results:")
        logger.info(f"  - Total records in location_names table: {total_count}")
        logger.info(f"  - Sample records:")
        
        for record in sample_records:
            logger.info(f"    ID: {record[0]}, Name: {record[1]}, Created: {record[2]}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verifying data: {e}")
        return False

def main():
    """Main function to create table and import data"""
    logger.info("Starting location_names table creation and data import...")
    
    # Path to the CSV file
    csv_file_path = Path(__file__).parent / "locations.csv"
    
    # Step 1: Create table
    logger.info("Step 1: Creating location_names table...")
    if not create_location_names_table():
        logger.error("Failed to create table. Exiting.")
        sys.exit(1)
    
    # Step 2: Populate table
    logger.info("Step 2: Populating location_names table...")
    if not populate_location_names_table(csv_file_path):
        logger.error("Failed to populate table. Exiting.")
        sys.exit(1)
    
    # Step 3: Verify data
    logger.info("Step 3: Verifying imported data...")
    if not verify_data():
        logger.error("Failed to verify data.")
        sys.exit(1)
    
    logger.info("Successfully completed location_names table creation and data import!")

if __name__ == "__main__":
    main() 