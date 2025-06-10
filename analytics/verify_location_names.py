#!/usr/bin/env python3
"""
Simple script to verify the location_names table
"""

import pandas as pd
from sqlalchemy import create_engine, text
import logging

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

def verify_table():
    """Verify the location_names table"""
    try:
        # Create engine
        conn_string = f"postgresql://{DB_PARAMS['user']}:{DB_PARAMS['password']}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['database']}"
        engine = create_engine(conn_string)
        
        with engine.connect() as conn:
            # Check if table exists
            exists_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'location_names'
            );
            """
            exists = conn.execute(text(exists_query)).scalar()
            print(f"Table 'location_names' exists: {exists}")
            
            if not exists:
                print("Table does not exist!")
                return
            
            # Get table structure
            structure_query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'location_names'
            ORDER BY ordinal_position;
            """
            structure_df = pd.read_sql(structure_query, conn)
            print("\nTable Structure:")
            print(structure_df.to_string(index=False))
            
            # Get row count
            count_query = "SELECT COUNT(*) FROM location_names;"
            count = conn.execute(text(count_query)).scalar()
            print(f"\nTotal locations: {count}")
            
            # Get sample data
            sample_query = "SELECT * FROM location_names ORDER BY location_name LIMIT 10;"
            sample_df = pd.read_sql(sample_query, conn)
            print("\nFirst 10 locations (alphabetically):")
            print(sample_df.to_string(index=False))
            
            # Search for specific patterns
            search_patterns = ['MALL', 'ROAD', 'MILES']
            for pattern in search_patterns:
                search_query = f"SELECT COUNT(*) FROM location_names WHERE location_name LIKE '%{pattern}%';"
                count = conn.execute(text(search_query)).scalar()
                print(f"\nLocations containing '{pattern}': {count}")
                
                if count > 0 and count <= 5:
                    examples_query = f"SELECT location_name FROM location_names WHERE location_name LIKE '%{pattern}%' LIMIT 5;"
                    examples = conn.execute(text(examples_query)).fetchall()
                    print(f"Examples: {', '.join([row[0] for row in examples])}")
        
        print("\n✅ Table verification completed successfully!")
        
    except Exception as e:
        logger.error(f"Error verifying table: {e}")

if __name__ == "__main__":
    verify_table() 