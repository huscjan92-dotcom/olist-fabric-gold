# 🚀 Automated Olist Gold ETL Data Platform

An automated, enterprise-grade cloud data engineering pipeline that mirrors e-commerce data from a Silver Lakehouse layer into a write-enabled **Microsoft Fabric Gold Data Warehouse** using **GitHub Actions**, **Python**, and **Azure Entra ID**.

---

## 🏗️ Architecture Design

Github Action Runner -> Triggers T-SQL via secure tunnel -> MICROSOFT FABRIC WORKSPACE -> olist_silver (internal engine copy -> olist_gold_dw

### Why this design?

* **High-Speed ELT:** Data processing runs *internally* within Microsoft Fabric using T-SQL cross-database queries (`SELECT INTO`). This eliminated a row-by-row memory insert process, slashing execution time from over **6 hours** down to just **45 seconds**!
* **Write Permissions Unlocked:** The target destination uses a Fabric **Data Warehouse** (`olist_gold_dw`) instead of a Lakehouse, bypassing the read-only limitations of standard external database drivers.

---

## 🔐 Security & Identity Bridge

Because GitHub Actions is an external platform, it utilizes an **Azure Microsoft Entra ID App Registration** (`github-fabric-etl`) acting as a secure "Service Principal" identity bridge. This eliminates the need for personal human credentials, bypasses Multi-Factor Authentication (MFA) blocks, and ensures 24/7 automated pipeline stability.

### Secure Environment Credentials
The following encrypted deployment keys were generated in Azure and are safely stored inside **GitHub Repository Secrets**:

* **`AZURE_CLIENT_ID`**: The unique "Username" ID of the GitHub runner application.
* **`AZURE_TENANT_ID`**: The unique organizational ID of the Azure cloud network.
* **`AZURE_CLIENT_SECRET`**: The encrypted cryptographic password value used to authenticate.

---

## 🤖 Pipeline Automation (`.github/workflows/run_etl.yml`)

The pipeline runs automatically on a scheduled **Cron timer every day at 2:00 AM UTC** or can be manually triggered via the GitHub UI.

1. **Environment Setup:** Boots a clean Ubuntu Linux virtual machine runner.
2. **Driver Assembly:** Securely installs the official **Microsoft ODBC Driver 18 for SQL Server** to talk to Fabric.
3. **Execution:** Injects the encrypted secrets and fires the Core Python script.

---

## 🐍 Core Script Execution Loop (`olist_gold_etl.py`)

The script loops through all **10 primary e-commerce tables** from `olist_silver` and mirrors them 1:1 into the gold reporting warehouse under the `dbo` schema:

* `silver_orders`
* `silver_order_payments`
* `silver_customers`
* `silver_products`
* `silver_sellers`
* `silver_order_items`
* `silver_order_reviews`
* `dim_dates`
* `dim_geolocation`
* `silver_product_category_name_translation`

---

## 📊 Business Readiness & Next Steps
By keeping the data in its pure schema state in the Gold layer, data analysts can build **DAX measures** natively within the **Power BI Service** without encountering data transformation mismatch or truncating errors.

