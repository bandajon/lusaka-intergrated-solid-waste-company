#!/usr/bin/env python3
"""
Database Migration Runner for LISWMC Dashboard
----------------------------------------------
Runs the database migrations to create the user authentication table.
"""

import os
import sys
import psycopg2
from analytics.database_connection import get_db_connection

def run_migration(migration_file):
    """Execute a SQL migration file"""
    try:
        # Read the migration file
        with open(migration_file, 'r') as f:
            sql_commands = f.read()
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            print(f"❌ Failed to connect to database")
            return False
            
        cursor = conn.cursor()
        
        # Execute the migration
        print(f"📄 Running migration: {migration_file}")
        cursor.execute(sql_commands)
        conn.commit()
        
        print(f"✅ Migration completed successfully: {migration_file}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error in {migration_file}: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Migration file not found: {migration_file}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error in {migration_file}: {e}")
        return False

def main():
    """Run all migrations"""
    print("🚀 Starting LISWMC Database Migrations...")
    
    # List of migration files to run (in order)
    migrations = [
        "migrations/001_create_users_table.sql"
    ]
    
    success_count = 0
    total_count = len(migrations)
    
    for migration in migrations:
        if os.path.exists(migration):
            if run_migration(migration):
                success_count += 1
            else:
                print(f"❌ Failed to run migration: {migration}")
                print("❌ Stopping migration process due to error")
                break
        else:
            print(f"❌ Migration file not found: {migration}")
            break
    
    print(f"\n📊 Migration Summary:")
    print(f"   ✅ Successful: {success_count}/{total_count}")
    print(f"   ❌ Failed: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 All migrations completed successfully!")
        print("\n📋 Default User Accounts Created:")
        print("   👤 Admin: username=admin, password=admin123")
        print("   👁️  Viewer: username=viewer, password=viewer123")
        print("   ⚠️  Please change these passwords after first login!")
        return True
    else:
        print("❌ Some migrations failed. Please check the error messages above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 