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

## 📖 Appendix: Technical Data Dictionary (Gold Star-Schema)

This appendix outlines the core schemas and columns available within `olist_gold_dw`. These tables are optimized for dynamic relational modeling and DAX measure compilation in Power BI.

### 🛍️ 1. Core Transactional Tables

#### `silver_orders`
Tracks the lifecycle of every customer purchase order.
*   **`order_id`** (VARCHAR) - *Primary Key*. The unique identifier for each customer purchase.
*   **`customer_id`** (VARCHAR) - *Foreign Key*. Ties the order back to a specific customer record.
*   **`order_status`** (VARCHAR) - The operational state of the order (e.g., `delivered`, `shipped`, `canceled`).
*   **`order_purchase_timestamp`** (DATETIME2) - The exact date and time the customer placed the order.
*   **`order_delivered_customer_date`** (DATETIME2) - The actual arrival date at the customer's address (critical for delivery SLA metrics).

#### `silver_order_items`
Contains the granular product line items contained inside each order bucket.
*   **`order_id`** (VARCHAR) - *Composite Key*. Ties back to the parent order record.
*   **`order_item_id`** (INT) - Sequential number showing the number of distinct items within the same order.
*   **`product_id`** (VARCHAR) - *Foreign Key*. Connects the line item to the product master table.
*   **`seller_id`** (VARCHAR) - *Foreign Key*. Connects the item to the fulfilling merchant.
*   **`price`** (DECIMAL) - The actual catalog price paid for the single item.
*   **`freight_value`** (DECIMAL) - The shipping/freight cost allocated to this specific item line.

#### `silver_order_payments`
Details the financial split and transaction methods used to fulfill order totals.
*   **`order_id`** (VARCHAR) - *Foreign Key*. Pairs transaction values back to a specific order.
*   **`payment_sequential`** (INT) - Sequence tracking split payments (e.g., if a customer pays using two separate credit cards).
*   **`payment_type`** (VARCHAR) - The transaction medium used (`credit_card`, `boleto`, `voucher`, `debit_card`).
*   **`payment_installments`** (INT) - The number of monthly installment options chosen by the consumer.
*   **`payment_value`** (DECIMAL) - The exact monetary amount processed in this transaction line.

#### `silver_order_reviews`
Houses the satisfaction surveys and ratings left by consumers post-delivery.
*   **`review_id`** (VARCHAR) - Unique identifier for the customer feedback submission.
*   **`order_id`** (VARCHAR) - *Foreign Key*. Connects the review scores directly back to a purchase transaction.
*   **`review_score`** (INT) - Customer satisfaction rating scaled from 1 (poor) to 5 (excellent).
*   **`review_comment_title`** (VARCHAR) - Optional short headline summary of the text review.
*   **`review_comment_message`** (VARCHAR) - Deep text feedback detailing customer satisfaction or logistics complaints.

---

### 👥 2. Dimension Profiles (Master Tables)

#### `silver_customers`
Master database of consumer geographic data points.
*   **`customer_id`** (VARCHAR) - Unique identifier for an individual transactional order placement.
*   **`customer_unique_id`** (VARCHAR) - *Master Customer Key*. Permanent identity string tracking repeat purchases over time.
*   **`customer_zip_code_prefix`** (INT) - The first 5 digits of the customer's mailing zip code.
*   **`customer_city`** (VARCHAR) - The localized residential city of the buyer.
*   **`customer_state`** (VARCHAR) - The regional state code of the buyer (e.g., SP, RJ).

#### `silver_products`
Master log of all physical inventory items offered on the platform.
*   **`product_id`** (VARCHAR) - *Primary Key*. Unique identity token for an item.
*   **`product_category_name`** (VARCHAR) - The raw category classification code (stored in native Portuguese).
*   **`product_name_lenght`** (INT) - Character count metadata of the product listing title.
*   **`product_description_lenght`** (INT) - Character count metadata of the product information page.
*   **`product_weight_g`** (INT) - Physical mass of the item package measured in grams.

#### `silver_sellers`
The registry of all third-party merchants fulfilling product listings.
*   **`seller_id`** (VARCHAR) - *Primary Key*. Unique identification code matching a merchant.
*   **`seller_zip_code_prefix`** (INT) - The operational dispatch location zip code prefix of the store.
*   **`seller_city`** (VARCHAR) - The hub city where the seller operates.
*   **`seller_state`** (VARCHAR) - The official state jurisdiction code of the seller.

---

### 🗺️ 3. Support & Mapping Geographies

#### `dim_geolocation`
Massive coordinate database tracking spatial information across Brazil.
*   **`geolocation_zip_code_prefix`** (INT) - Spatial join key matching customer and seller boundaries.
*   **`geolocation_lat`** (DECIMAL) - Exact geographic mapping Latitude coordinate string.
*   **`geolocation_lng`** (DECIMAL) - Exact geographic mapping Longitude coordinate string.
*   **`geolocation_city`** (VARCHAR) - Certified municipality label tied to the coordinates.
*   **`geolocation_state`** (VARCHAR) - State boundary code matching the physical location.

#### `silver_product_category_name_translation`
A simple lookup reference table utilized to dynamically translate interface columns.
*   **`product_category_name`** (VARCHAR) - *Join Key*. The native Portuguese classification code.
*   **`product_category_name_english`** (VARCHAR) - Clean English translation mapping for standard localization reporting.

#### `dim_dates`
A custom enterprise time table generated to run high-performance Time-Intelligence DAX logic.
*   **`date_key`** (DATETIME2) - The exact chronological calendar day.
*   **`year`** (INT) - Calendar year value (e.g., 2017, 2018).
*   **`month`** (INT) - Numerical month index scaling from 1 to 12.
*   **`month_name`** (VARCHAR) - Full alpha text label of the month (e.g., January).
*   **`quarter`** (INT) - Business reporting fiscal quarter metrics (1 through 4).
