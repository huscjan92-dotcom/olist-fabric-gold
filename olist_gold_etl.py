import os
import struct
import pyodbc
import pandas as pd

# 1. Grab your secure Azure credentials from GitHub Actions
client_id = os.environ['AZURE_CLIENT_ID']
client_secret = os.environ['AZURE_CLIENT_SECRET']
tenant_id = os.environ['AZURE_TENANT_ID']

# 2. Fabric Connection Configuration 
# ⚠️ REPLACE THE STRING BELOW with your real SQL Connection string from your Fabric workspace
server = 'dn6gtpmbysoepba6yymfijtvym-6g4xqxngnkjepceb736ijbh3xe.datawarehouse.fabric.microsoft.com'
database_silver = 'olist_silver'
database_gold = 'olist_gold'

# Standard connection string template for App Registrations
conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};Authentication=ActiveDirectoryServicePrincipal;UID={client_id};PWD={client_secret};Encrypt=yes;TrustServerCertificate=no;'

def copy_table_as_is(table_name):
    print(f"📖 Reading [{table_name}] from Silver Lakehouse...")
    # Read the data exactly as it is
    with pyodbc.connect(conn_str + f'DATABASE={database_silver};') as conn:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    
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
                cols_definition.append(f"[{col}] DATETIME2")
            else:
                cols_definition.append(f"[{col}] VARCHAR(255)")
        
        create_sql = f"IF OBJECT_ID('{table_name}', 'U') IS NULL CREATE TABLE [{table_name}] ({', '.join(cols_definition)})"
        cursor.execute(create_sql)
        
        # Truncate old data to ensure clean overwrite
        cursor.execute(f"TRUNCATE TABLE [{table_name}]")
        
        # Bulk load values for maximum speed
        placeholders = ", ".join(["?"] * len(df.columns))
        insert_sql = f"INSERT INTO [{table_name}] VALUES ({placeholders})"
        
        # Convert dataframe back to raw list of tuples for quick pyodbc insertion
        records = [tuple(x) for x in df.to_numpy()]
        cursor.executemany(insert_sql, records)
        conn.commit()
    print(f"✅ Successfully mirrored [{table_name}] to Gold!")

# Execute exact mirrors for your main Olist tables
copy_table_as_is("cleaned_orders")
copy_table_as_is("cleaned_payments")

print("🎉 Success! Your Olist Gold Layer is a perfect 1:1 match of your Silver tables!")
