import psycopg2
import pandas as pd
import os
import glob
import io
from dotenv import load_dotenv

# Database connection details
DB_NAME = "DB_NAME"
DB_USER = "DB_USER"
DB_PASSWORD = "DB_PASSWORD"
DB_HOST = "DB_HOST"
DB_PORT = "DB_PORT"

# Directory containing CSV files
# Use a raw string or double backslashes for the path
CSV_DIRECTORY = "data\archive"

def create_database_if_not_exists():
    """Create database if it doesn't exist"""
    try:
        # Connect to default 'postgres' database first
        conn = psycopg2.connect(
            dbname="postgres",  # Connect to default database
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE "{DB_NAME}"')
            print(f"Database '{DB_NAME}' created successfully.")
        else:
            print(f"Database '{DB_NAME}' already exists.")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return False

def get_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        print("Connected to the database successfully.")
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

def create_table_from_csv(conn, csv_file, table_name):
    """Create table based on CSV structure"""
    try:
        # Read first few rows to determine data types
        data = pd.read_csv(csv_file, nrows=100)
        cursor = conn.cursor()
        
        # Drop table if exists
        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        
        # Create table query
        create_query = f'CREATE TABLE "{table_name}" (\n'
        
        for col in data.columns:
            # Determine PostgreSQL data type
            if data[col].dtype == 'object':
                col_type = 'TEXT'
            elif data[col].dtype in ['int64', 'int32']:
                col_type = 'INTEGER'
            elif data[col].dtype in ['float64', 'float32']:
                col_type = 'NUMERIC'
            else:
                col_type = 'TEXT'
            
            # Use a sanitized column name in the query
            sanitized_col = col.strip().replace('"', '')
            create_query += f'    "{sanitized_col}" {col_type},\n'
        
        create_query = create_query.rstrip(',\n') + '\n);'
        
        cursor.execute(create_query)
        conn.commit()
        cursor.close()
        
        print(f"Created table: {table_name}")
        return True
        
    except Exception as e:
        print(f"Error creating table {table_name}: {e}")
        return False

def create_orders_table_manually(conn):
    """Create orders table with proper timestamp data types"""
    cursor = conn.cursor()
    
    try:
        # Drop existing table
        cursor.execute('DROP TABLE IF EXISTS "orders"')
        
        # Create orders table with proper data types
        create_query = '''
        CREATE TABLE "orders" (
            "order_id" INTEGER,
            "user_id" INTEGER,
            "status" TEXT,
            "gender" TEXT,
            "created_at" TIMESTAMP WITH TIME ZONE,
            "returned_at" TIMESTAMP WITH TIME ZONE,
            "shipped_at" TIMESTAMP WITH TIME ZONE,
            "delivered_at" TIMESTAMP WITH TIME ZONE,
            "num_of_item" INTEGER
        );
        '''
        
        cursor.execute(create_query)
        conn.commit()
        cursor.close()
        
        print("✓ Orders table created successfully with proper timestamp types")
        return True
        
    except Exception as e:
        print(f"Error creating orders table: {e}")
        conn.rollback()
        return False

def import_orders_csv(conn, csv_file):
    """Import orders.csv with proper timestamp handling using copy_from for speed and reliability"""
    try:
        # Read CSV file
        data = pd.read_csv(csv_file)
        print(f"Reading orders.csv: {len(data)} rows")
        
        # Create orders table first
        if not create_orders_table_manually(conn):
            return False
        
        # Convert date columns to proper format
        date_columns = ['created_at', 'returned_at', 'shipped_at', 'delivered_at']
        for col in date_columns:
            if col in data.columns:
                data[col] = pd.to_datetime(data[col], utc=True, errors='coerce')
        
        # Convert the DataFrame to a CSV string buffer
        # Use na_rep='\\N' to represent NULL values for PostgreSQL's COPY command
        buffer = io.StringIO()
        data.to_csv(buffer, index=False, header=False, na_rep='\\N')
        buffer.seek(0)
        
        cursor = conn.cursor()
        
        # Use copy_from for efficient bulk insert
        cursor.copy_from(buffer, 'orders', sep=',', null='\\N', columns=data.columns)
        
        conn.commit()
        cursor.close()
        
        print(f"✓ Successfully inserted {len(data)} rows into orders using COPY")
        return True
    
    except Exception as e:
        print(f"✗ Error importing orders.csv: {e}")
        conn.rollback()
        return False

def import_csv_to_table(conn, csv_file, table_name):
    """Import other CSVs using the copy_from method for efficiency"""
    try:
        # Read CSV file
        data = pd.read_csv(csv_file)
        print(f"Reading {os.path.basename(csv_file)}: {len(data)} rows")
        
        # Create table first
        if not create_table_from_csv(conn, csv_file, table_name):
            return False
        
        # Convert the DataFrame to a CSV string buffer
        buffer = io.StringIO()
        data.to_csv(buffer, index=False, header=False, na_rep='\\N')
        buffer.seek(0)
        
        cursor = conn.cursor()
        
        # Use copy_from for efficient bulk insert
        cursor.copy_from(buffer, table_name, sep=',', null='\\N', columns=data.columns)

        conn.commit()
        cursor.close()
        
        print(f"✓ Successfully inserted {len(data)} rows into {table_name} using COPY")
        return True
        
    except Exception as e:
        print(f"✗ Error importing {os.path.basename(csv_file)}: {e}")
        conn.rollback()
        return False

def import_all_csvs():
    """Main function to orchestrate the import process"""
    # Create database if it doesn't exist
    if not create_database_if_not_exists():
        return
    
    # Connect to database
    conn = get_connection()
    if not conn:
        return
    
    try:
        # Get all CSV files in directory
        csv_files = glob.glob(os.path.join(CSV_DIRECTORY, "*.csv"))
        print(f"Found {len(csv_files)} CSV files")
        
        if not csv_files:
            print("No CSV files found!")
            return
        
        successful = 0
        failed = 0
        
        # Process each CSV file
        for csv_file in csv_files:
            filename = os.path.basename(csv_file)
            
            # Use filename (without .csv) as table name
            table_name = filename.replace('.csv', '').lower()
            
            print(f"\nProcessing: {filename} -> {table_name}")
            
            # Handle orders.csv separately
            if filename.lower() == 'orders.csv':
                if import_orders_csv(conn, csv_file):
                    successful += 1
                else:
                    failed += 1
            else:
                # Handle other CSV files normally
                if import_csv_to_table(conn, csv_file, table_name):
                    successful += 1
                else:
                    failed += 1
        
        print(f"\n--- SUMMARY ---")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total: {len(csv_files)}")
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    import_all_csvs()