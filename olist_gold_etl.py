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
database_gold = 'olist_gold_dw'

# Standard connection string template for App Registrations
conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};Authentication=ActiveDirectoryServicePrincipal;UID={client_id};PWD={client_secret};Encrypt=yes;TrustServerCertificate=no;'

def fast_mirror_table(table_name):
    print(f"⚡ Processing [{table_name}] via Fabric internal engine...")
    try:
        with pyodbc.connect(conn_str + f'DATABASE={database_gold};') as conn:
            cursor = conn.cursor()
            
            # Step A: Safely drop the table if it already exists in your Gold warehouse
            cursor.execute(f"IF OBJECT_ID('dbo.[{table_name}]', 'U') IS NOT NULL DROP TABLE dbo.[{table_name}]")
            
            # Step B: Fast cross-database copy straight from Silver to Gold
            # Fabric reads across items in the same workspace automatically using three-part naming structures
            copy_sql = f"SELECT * INTO dbo.[{table_name}] FROM [{database_silver}].dbo.[{table_name}]"
            cursor.execute(copy_sql)
            
            conn.commit()
        print(f"✅ Successfully mirrored [{table_name}] to Gold Warehouse!")
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

# Run the lightning fast copy loop
for table in all_tables:
    fast_mirror_table(table)

print("🎉 Success! All Olist Silver tables have been perfectly copied to the Gold Warehouse instantly!")
