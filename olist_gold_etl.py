import os
import struct
import pyodbc
import pandas as pd

# 1. Grab your secure Azure credentials from GitHub Actions
client_id = os.environ['AZURE_CLIENT_ID']
client_secret = os.environ['AZURE_CLIENT_SECRET']
tenant_id = os.environ['AZURE_TENANT_ID']

# 2. Fabric Connection Configuration 
# (Your saved string looks great!)
server = 'dn6gtpmbysoepba6yymfijtvym-6g4xqxngnkjepceb736ijbh3xe.datawarehouse.fabric.microsoft.com'
database_silver = 'olist_silver'
database_gold = 'olist_gold'

# Standard connection string template for App Registrations
conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};Authentication=ActiveDirectoryServicePrincipal;UID={client_id};PWD={client_secret};Encrypt=yes;TrustServerCertificate=no;'

def copy_table_as_is(table_name):
    print(f"📖 Reading [{table_name}] from Silver Lakehouse...")
    try:
        # Read the data exactly as it is using the explicit dbo schema
        with pyodbc.connect(conn_str + f'DATABASE={database_silver};') as conn:
            df = pd.read_sql(f"SELECT * FROM dbo.[{table_name}]", conn)
        
        if df.empty:
            print(f"⚠️ Warning: {table_name} was empty in Silver. Skipping.")
            return

        print(f"✍️ Writing [{table_name}] directly into Gold Lakehouse...")
        with pyodbc.connect(conn_str + f'DATABASE={database_gold};') as conn:
            cursor = conn.cursor()
            
            # Build strict dynamic SQL column strings based on your actual data
            cols_definition = []
            for col, dtype in zip(df.columns, df.dtypes):
                if "int" in str(dtype):
                    cols_definition.append(f"[{col}] INT")
                elif "float" in str(dtype):
                    cols_definition.append(f"[{col}] DECIMAL(18,4)")
                elif "datetime" in str(dtype):
                    # Fixed: Explicitly added the (6) precision required by Fabric SQL endpoint
                    cols_definition.append(f"[{col}] DATETIME2(6)")
                else:
                    cols_definition.append(f"[{col}] VARCHAR(255)")
            
            # Create table under dbo schema if it doesn't exist
            create_sql = f"IF OBJECT_ID('dbo.[{table_name}]', 'U') IS NULL CREATE TABLE dbo.[{table_name}] ({', '.join(cols_definition)})"
            cursor.execute(create_sql)
            
            # Truncate old data to ensure clean overwrite
            cursor.execute(f"TRUNCATE TABLE dbo.[{table_name}]")
            
            # Bulk load values for maximum speed
            placeholders = ", ".join(["?"] * len(df.columns))
            insert_sql = f"INSERT INTO dbo.[{table_name}] VALUES ({placeholders})"
            
            # Convert dataframe back to raw list of tuples for quick pyodbc insertion
            records = [tuple(x) for x in df.to_numpy()]
            cursor.executemany(insert_sql, records)
            conn.commit()
        print(f"✅ Successfully mirrored [{table_name}] to Gold!")
    except Exception as e:
        print(f"❌ Error processing table [{table_name}]: {str(e)}")
        raise e

# 📋 The Full Array of Your 10 Olist Silver Tables
all_tables = [
    "silver_orders",
    "silver_order_payments",
    "silver_customers",
    "silver_products",
    "silver_sellers",
    "silver_order_items",
    "silver_order_reviews",
    "dim_dates",
    "dim_geolocation",
    "silver_product_category_name_translation"
]

# Run the mirror loop for every single table automatically
for table in all_tables:
    copy_table_as_is(table)

print("🎉 Success! All Olist Silver tables have been perfectly mirrored to Gold!")
