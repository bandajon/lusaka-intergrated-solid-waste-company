import pandas as pd
import logging
import os
import psycopg2
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection parameters
DB_PARAMS = {
    'host': os.getenv('DB_HOST', 'agripredict-prime-prod.caraj6fzskso.eu-west-2.rds.amazonaws.com'),
    'database': os.getenv('DB_NAME', 'users'),
    'user': os.getenv('DB_USER', 'agripredict'),
    'password': os.getenv('DB_PASSWORD', 'Wee8fdm0k2!!'),
    'port': int(os.getenv('DB_PORT', 5432))
}

# Database tables
TABLES = {
    'company': 'company',
    'vehicle': 'vehicle',
    'weigh_event': 'weigh_event'
}

def get_connection_string():
    """Get SQLAlchemy connection string"""
    return f"postgresql://{DB_PARAMS['user']}:{DB_PARAMS['password']}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['database']}"

def get_db_connection():
    """Get raw psycopg2 connection for transaction management"""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        return conn
    except Exception as e:
        logger.error(f"Error creating database connection: {e}")
        return None

def get_db_engine():
    """Get SQLAlchemy engine for database operations"""
    conn_string = get_connection_string()
    return create_engine(conn_string)

def read_companies():
    """Read companies from database"""
    try:
        engine = get_db_engine()
        query = f"SELECT * FROM {TABLES['company']}"
        companies_df = pd.read_sql(query, engine)
        logger.info(f"Successfully read {len(companies_df)} companies from database")
        return companies_df
    except Exception as e:
        logger.error(f"Error reading companies from database: {e}")
        return pd.DataFrame()

def read_vehicles():
    """Read vehicles from database"""
    try:
        engine = get_db_engine()
        query = f"SELECT * FROM {TABLES['vehicle']}"
        vehicles_df = pd.read_sql(query, engine)
        logger.info(f"Successfully read {len(vehicles_df)} vehicles from database")
        return vehicles_df
    except Exception as e:
        logger.error(f"Error reading vehicles from database: {e}")
        return pd.DataFrame()

def read_weigh_events(use_csv_fallback=True):
    """Read weigh events from database or CSV fallback"""
    try:
        engine = get_db_engine()
        query = f"SELECT * FROM {TABLES['weigh_event']}"
        weigh_df = pd.read_sql(query, engine)
        logger.info(f"Successfully read {len(weigh_df)} weigh events from database")
        return weigh_df
    except Exception as e:
        logger.error(f"Error reading weigh events from database: {e}")
        if use_csv_fallback:
            # Try to use CSV file as fallback
            csv_path = 'weigh_event.csv'
            if os.path.exists(csv_path):
                logger.info(f"Using CSV fallback file: {csv_path}")
                weigh_df = pd.read_csv(csv_path)
                logger.info(f"Successfully read {len(weigh_df)} weigh events from CSV")
                return weigh_df
        return pd.DataFrame()

def read_table(table_name):
    """Read data from a specific table"""
    if table_name not in TABLES.values():
        logger.error(f"Invalid table name: {table_name}")
        return pd.DataFrame()
    
    try:
        engine = get_db_engine()
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, engine)
        logger.info(f"Successfully read {len(df)} records from {table_name}")
        return df
    except Exception as e:
        logger.error(f"Error reading from {table_name}: {e}")
        return pd.DataFrame()

def execute_query(query, params=None):
    """Execute a custom query"""
    try:
        engine = get_db_engine()
        if params:
            result = pd.read_sql(query, engine, params=params)
        else:
            result = pd.read_sql(query, engine)
        logger.info(f"Successfully executed query, returned {len(result)} records")
        return result
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return pd.DataFrame()

def write_weigh_event(event_data):
    """Write a single weigh event to the database"""
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            # Convert to DataFrame for easier insertion
            df = pd.DataFrame([event_data])
            df.to_sql(TABLES['weigh_event'], conn, if_exists='append', index=False)
            logger.info(f"Successfully wrote weigh event to database")
            return True
    except Exception as e:
        logger.error(f"Error writing weigh event to database: {e}")
        return False

def write_multiple_weigh_events(events_df):
    """Write multiple weigh events to the database"""
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            events_df.to_sql(TABLES['weigh_event'], conn, if_exists='append', index=False)
            logger.info(f"Successfully wrote {len(events_df)} weigh events to database")
            return True
    except Exception as e:
        logger.error(f"Error writing weigh events to database: {e}")
        return False

def check_connection():
    """Check if database connection is working"""
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            if result and result[0] == 1:
                return True, "Connection successful"
            return False, "Connection test failed"
    except Exception as e:
        return False, f"Connection error: {e}"