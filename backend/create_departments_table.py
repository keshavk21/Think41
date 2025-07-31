import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'e_commerce'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', '5432')
}

def create_and_populate_departments_table():
    conn = None
    cursor = None
    try:
        # Connect to database
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        # Drop the table if it exists to ensure a clean start for the example
        # (You can remove this line in a production environment)
        cursor.execute("DROP TABLE IF EXISTS departments CASCADE;")

        # Create the departments table with an id and department_name column.
        # We will use the id from the products table as a department_id, so it should not be SERIAL
        # if you want to copy the exact id. If you want a new, unique ID, you can use SERIAL.
        # Here, I've chosen to use SERIAL for the new table's own primary key.
        create_table_query = """
        CREATE TABLE departments (
            id SERIAL PRIMARY KEY,
            department_name VARCHAR(100) NOT NULL UNIQUE
        );
        """
        
        print("Creating 'departments' table...")
        cursor.execute(create_table_query)

        # SQL query to insert unique department names from the 'products' table.
        # We use a SELECT DISTINCT to avoid duplicating department names.
        copy_data_query = """
        INSERT INTO departments (department_name)
        SELECT DISTINCT department FROM products
        ON CONFLICT (department_name) DO NOTHING;
        """
        
        print("Populating 'departments' table with data from 'products' table...")
        cursor.execute(copy_data_query)
        
        # Commit the transaction
        conn.commit()
        print("Departments table created and populated successfully!")
        
        # Show the created table and its contents
        cursor.execute("SELECT * FROM departments ORDER BY id;")
        departments = cursor.fetchall()
        print(f"\nSuccessfully inserted {cursor.rowcount} unique records.")
        print("\nDepartments in the database:")
        for dept in departments:
            print(f"ID: {dept[0]}, Name: {dept[1]}")
            
    except psycopg2.Error as e:
        print(f"Database Error: {e}")
        # Rollback the transaction on error
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Close the cursor and connection in the 'finally' block
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    create_and_populate_departments_table()