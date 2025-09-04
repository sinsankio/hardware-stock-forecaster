import pymysql
import pandas as pd
import os

# Database connection settings
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'poscnbhardware',
    'charset': 'utf8'
}

# Directory to save CSV files
output_dir = 'data/db-to-csv-exports'
os.makedirs(output_dir, exist_ok=True)

# Connect to MySQL database
connection = pymysql.connect(**db_config)

try:
    with connection.cursor() as cursor:
        # Fetch list of tables
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()

        for (table_name,) in tables:
            print(f"Exporting table: {table_name}")
            # Load table data into DataFrame
            df = pd.read_sql(f"SELECT * FROM `{table_name}`", connection)

            # Write to CSV
            csv_path = os.path.join(output_dir, f"{table_name}.csv")
            df.to_csv(csv_path, index=False, encoding='utf-8')

            print(f"Saved to {csv_path}")

finally:
    connection.close()

print("All tables exported successfully.")
