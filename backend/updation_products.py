import psycopg2
form dotenv import load_dotenv
# Database connection details
DB_NAME = os.getenv("DB_NAME", "")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = os.getenv("DB_PORT", "")

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
        host=DB_HOST, port=DB_PORT
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # ✅ Step 1: Update 'department' with department IDs while it's still TEXT
    cursor.execute("""
        UPDATE products
        SET department = departments.id::TEXT
        FROM departments
        WHERE products.department = departments.department_name;
    """)
    print("✅ Updated 'department' column with department IDs (as TEXT).")

    # ✅ Step 2: Convert 'department' column from TEXT to INTEGER
    cursor.execute("""
        ALTER TABLE products
        ALTER COLUMN department TYPE INTEGER USING department::INTEGER;
    """)
    print("✅ Converted 'department' column to INTEGER.")

    # ✅ Step 3: Add foreign key constraint
    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_department'
                  AND table_name = 'products'
            ) THEN
                ALTER TABLE products
                ADD CONSTRAINT fk_department
                FOREIGN KEY (department)
                REFERENCES departments(id);
            END IF;
        END $$;
    """)
    print("✅ Foreign key constraint added on 'department' column.")

except Exception as e:
    print("❌ Error:", e)
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()
