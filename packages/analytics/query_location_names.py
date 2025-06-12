#!/usr/bin/env python3
"""
Helper script to query and work with the location_names table
"""

import pandas as pd
from sqlalchemy import create_engine, text
import logging
import sys

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

def get_db_engine():
    """Get SQLAlchemy engine for database operations"""
    conn_string = f"postgresql://{DB_PARAMS['user']}:{DB_PARAMS['password']}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['database']}"
    return create_engine(conn_string)

def get_all_locations():
    """Get all locations from the location_names table"""
    try:
        engine = get_db_engine()
        query = "SELECT * FROM location_names ORDER BY location_name;"
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        logger.error(f"Error retrieving locations: {e}")
        return None

def search_locations(search_term):
    """Search for locations containing the search term"""
    try:
        engine = get_db_engine()
        query = """
        SELECT * FROM location_names 
        WHERE location_name ILIKE %s 
        ORDER BY location_name;
        """
        df = pd.read_sql(query, engine, params=[f'%{search_term}%'])
        return df
    except Exception as e:
        logger.error(f"Error searching locations: {e}")
        return None

def get_table_info():
    """Get information about the location_names table"""
    try:
        engine = get_db_engine()
        
        with engine.connect() as conn:
            # Get table structure
            structure_query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'location_names'
            ORDER BY ordinal_position;
            """
            structure_df = pd.read_sql(structure_query, conn)
            
            # Get row count
            count_query = "SELECT COUNT(*) as total_locations FROM location_names;"
            count_result = conn.execute(text(count_query)).scalar()
            
            return structure_df, count_result
            
    except Exception as e:
        logger.error(f"Error getting table info: {e}")
        return None, None

def add_location(location_name):
    """Add a new location to the table"""
    try:
        engine = get_db_engine()
        
        with engine.connect() as conn:
            query = """
            INSERT INTO location_names (location_name)
            VALUES (:location_name)
            ON CONFLICT (location_name) DO NOTHING
            RETURNING id;
            """
            result = conn.execute(text(query), {'location_name': location_name.strip()})
            conn.commit()
            
            if result.rowcount > 0:
                logger.info(f"Successfully added location: {location_name}")
                return True
            else:
                logger.warning(f"Location already exists: {location_name}")
                return False
                
    except Exception as e:
        logger.error(f"Error adding location: {e}")
        return False

def delete_location(location_name):
    """Delete a location from the table"""
    try:
        engine = get_db_engine()
        
        with engine.connect() as conn:
            query = "DELETE FROM location_names WHERE location_name = :location_name;"
            result = conn.execute(text(query), {'location_name': location_name})
            conn.commit()
            
            if result.rowcount > 0:
                logger.info(f"Successfully deleted location: {location_name}")
                return True
            else:
                logger.warning(f"Location not found: {location_name}")
                return False
                
    except Exception as e:
        logger.error(f"Error deleting location: {e}")
        return False

def main():
    """Interactive main function"""
    print("Location Names Database Helper")
    print("=" * 40)
    
    while True:
        print("\nChoose an option:")
        print("1. View all locations")
        print("2. Search locations")
        print("3. Add a location")
        print("4. Delete a location")
        print("5. Show table info")
        print("6. Export to CSV")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            print("\nAll locations:")
            df = get_all_locations()
            if df is not None:
                print(f"Total locations: {len(df)}")
                if len(df) > 20:
                    print("Showing first 20 locations:")
                    print(df.head(20).to_string(index=False))
                    print(f"... and {len(df) - 20} more")
                else:
                    print(df.to_string(index=False))
        
        elif choice == '2':
            search_term = input("Enter search term: ").strip()
            if search_term:
                print(f"\nSearching for locations containing '{search_term}':")
                df = search_locations(search_term)
                if df is not None:
                    if len(df) > 0:
                        print(df.to_string(index=False))
                    else:
                        print("No locations found.")
        
        elif choice == '3':
            location_name = input("Enter location name to add: ").strip()
            if location_name:
                add_location(location_name)
        
        elif choice == '4':
            location_name = input("Enter location name to delete: ").strip()
            if location_name:
                if input(f"Are you sure you want to delete '{location_name}'? (y/N): ").lower() == 'y':
                    delete_location(location_name)
        
        elif choice == '5':
            print("\nTable Information:")
            structure_df, count = get_table_info()
            if structure_df is not None:
                print(f"Total locations: {count}")
                print("\nTable structure:")
                print(structure_df.to_string(index=False))
        
        elif choice == '6':
            filename = input("Enter CSV filename (default: locations_export.csv): ").strip()
            if not filename:
                filename = "locations_export.csv"
            
            df = get_all_locations()
            if df is not None:
                df.to_csv(filename, index=False)
                print(f"Exported {len(df)} locations to {filename}")
        
        elif choice == '7':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 