CREATE CATALOG IF NOT EXISTS `__CATALOG__` COMMENT 'Synthetic data catalog for the Unity Catalog chatbot demo.';
CREATE SCHEMA IF NOT EXISTS `__CATALOG__`.bronze COMMENT 'Synthetic source-shaped demo data.';
CREATE SCHEMA IF NOT EXISTS `__CATALOG__`.silver COMMENT 'Validated and normalized synthetic demo data.';
CREATE SCHEMA IF NOT EXISTS `__CATALOG__`.gold COMMENT 'Curated business-facing views for Genie.';
CREATE SCHEMA IF NOT EXISTS `__CATALOG__`.app COMMENT 'Minimal application metadata; no prompt or answer content.';
CREATE SCHEMA IF NOT EXISTS `__CATALOG__`.monitoring COMMENT 'Operational metadata that complements platform audit logs.';

CREATE TABLE IF NOT EXISTS `__CATALOG__`.bronze.customers_raw (
  customer_id STRING COMMENT 'Synthetic customer key; primary key for customers.',
  customer_name STRING COMMENT 'Synthetic customer display name.',
  region STRING COMMENT 'Source region label; normalized in silver.',
  created_at STRING COMMENT 'Source timestamp text; parsed in silver.',
  source_record_id STRING COMMENT 'Synthetic source-system record identifier.',
  ingested_at TIMESTAMP COMMENT 'Time this synthetic row was loaded.'
) USING DELTA COMMENT 'Synthetic raw customers. One row per source record; customer_id is the business key.';
CREATE TABLE IF NOT EXISTS `__CATALOG__`.bronze.products_raw (
  product_id STRING COMMENT 'Synthetic product key; primary key for products.',
  product_name STRING COMMENT 'Synthetic product name.',
  category STRING COMMENT 'Business product category.',
  unit_price STRING COMMENT 'Source unit price text; cast to decimal in silver.',
  source_record_id STRING COMMENT 'Synthetic source-system record identifier.',
  ingested_at TIMESTAMP COMMENT 'Time this synthetic row was loaded.'
) USING DELTA COMMENT 'Synthetic raw products. One row per source record; product_id is the business key.';
CREATE TABLE IF NOT EXISTS `__CATALOG__`.bronze.orders_raw (
  order_id STRING COMMENT 'Synthetic order key; primary key for orders.',
  customer_id STRING COMMENT 'Foreign key to bronze.customers_raw.customer_id.',
  order_date STRING COMMENT 'Source order date text; parsed in silver.',
  order_status STRING COMMENT 'Source order status.',
  source_record_id STRING COMMENT 'Synthetic source-system record identifier.',
  ingested_at TIMESTAMP COMMENT 'Time this synthetic row was loaded.'
) USING DELTA COMMENT 'Synthetic raw orders. customer_id references customers; order_id is unique.';
CREATE TABLE IF NOT EXISTS `__CATALOG__`.bronze.order_items_raw (
  order_item_id STRING COMMENT 'Synthetic order-item key; primary key for order items.',
  order_id STRING COMMENT 'Foreign key to bronze.orders_raw.order_id.',
  product_id STRING COMMENT 'Foreign key to bronze.products_raw.product_id.',
  quantity STRING COMMENT 'Source quantity text; cast to integer in silver.',
  unit_price STRING COMMENT 'Source unit price text; cast to decimal in silver.',
  source_record_id STRING COMMENT 'Synthetic source-system record identifier.',
  ingested_at TIMESTAMP COMMENT 'Time this synthetic row was loaded.'
) USING DELTA COMMENT 'Synthetic raw order items. order_id and product_id reference orders and products.';

MERGE INTO `__CATALOG__`.bronze.customers_raw AS target
USING (SELECT * FROM VALUES
  ('C001', 'Avery Chen', 'West', '2025-01-10T00:00:00Z', 'demo-customer-001'),
  ('C002', 'Jordan Patel', 'East', '2025-02-14T00:00:00Z', 'demo-customer-002'),
  ('C003', 'Morgan Rivera', 'Central', '2025-03-21T00:00:00Z', 'demo-customer-003')
  AS source(customer_id, customer_name, region, created_at, source_record_id)) AS source
ON target.customer_id = source.customer_id AND target.source_record_id = source.source_record_id
WHEN NOT MATCHED THEN INSERT (customer_id, customer_name, region, created_at, source_record_id, ingested_at)
VALUES (source.customer_id, source.customer_name, source.region, source.created_at, source.source_record_id, current_timestamp());

MERGE INTO `__CATALOG__`.bronze.products_raw AS target
USING (SELECT * FROM VALUES
  ('P001', 'Trail Pack', 'Outdoor', '79.00', 'demo-product-001'),
  ('P002', 'Travel Mug', 'Accessories', '24.50', 'demo-product-002'),
  ('P003', 'Rain Shell', 'Outdoor', '119.00', 'demo-product-003')
  AS source(product_id, product_name, category, unit_price, source_record_id)) AS source
ON target.product_id = source.product_id AND target.source_record_id = source.source_record_id
WHEN NOT MATCHED THEN INSERT (product_id, product_name, category, unit_price, source_record_id, ingested_at)
VALUES (source.product_id, source.product_name, source.category, source.unit_price, source.source_record_id, current_timestamp());

MERGE INTO `__CATALOG__`.bronze.orders_raw AS target
USING (SELECT * FROM VALUES
  ('O1001', 'C001', '2025-04-01', 'complete', 'demo-order-001'),
  ('O1002', 'C002', '2025-04-05', 'complete', 'demo-order-002'),
  ('O1003', 'C001', '2025-05-02', 'complete', 'demo-order-003'),
  ('O1004', 'C003', '2025-05-09', 'cancelled', 'demo-order-004')
  AS source(order_id, customer_id, order_date, order_status, source_record_id)) AS source
ON target.order_id = source.order_id AND target.source_record_id = source.source_record_id
WHEN NOT MATCHED THEN INSERT (order_id, customer_id, order_date, order_status, source_record_id, ingested_at)
VALUES (source.order_id, source.customer_id, source.order_date, source.order_status, source.source_record_id, current_timestamp());

MERGE INTO `__CATALOG__`.bronze.order_items_raw AS target
USING (SELECT * FROM VALUES
  ('I001', 'O1001', 'P001', '1', '79.00', 'demo-item-001'),
  ('I002', 'O1001', 'P002', '2', '24.50', 'demo-item-002'),
  ('I003', 'O1002', 'P003', '1', '119.00', 'demo-item-003'),
  ('I004', 'O1003', 'P002', '3', '24.50', 'demo-item-004'),
  ('I005', 'O1004', 'P001', '1', '79.00', 'demo-item-005')
  AS source(order_item_id, order_id, product_id, quantity, unit_price, source_record_id)) AS source
ON target.order_item_id = source.order_item_id AND target.source_record_id = source.source_record_id
WHEN NOT MATCHED THEN INSERT (order_item_id, order_id, product_id, quantity, unit_price, source_record_id, ingested_at)
VALUES (source.order_item_id, source.order_id, source.product_id, source.quantity, source.unit_price, source.source_record_id, current_timestamp());

CREATE OR REPLACE TABLE `__CATALOG__`.silver.customers
COMMENT 'Validated synthetic customers; unique customer_id, non-empty names, normalized region labels.'
AS SELECT customer_id, trim(customer_name) AS customer_name,
  initcap(trim(region)) AS region, try_to_timestamp(created_at) AS created_at
FROM `__CATALOG__`.bronze.customers_raw
WHERE customer_id IS NOT NULL AND trim(customer_name) <> ''
QUALIFY row_number() OVER (PARTITION BY customer_id ORDER BY ingested_at DESC) = 1;
CREATE OR REPLACE TABLE `__CATALOG__`.silver.products
COMMENT 'Validated synthetic products; unique product_id, positive decimal unit_price.'
AS SELECT product_id, trim(product_name) AS product_name,
  initcap(trim(category)) AS category, try_cast(unit_price AS DECIMAL(12, 2)) AS unit_price
FROM `__CATALOG__`.bronze.products_raw
WHERE product_id IS NOT NULL AND trim(product_name) <> ''
  AND try_cast(unit_price AS DECIMAL(12, 2)) > 0
QUALIFY row_number() OVER (PARTITION BY product_id ORDER BY ingested_at DESC) = 1;
CREATE OR REPLACE TABLE `__CATALOG__`.silver.orders
COMMENT 'Validated synthetic orders; unique order_id and valid customer relationship.'
AS SELECT order_id, customer_id, try_cast(order_date AS DATE) AS order_date,
  lower(trim(order_status)) AS order_status
FROM `__CATALOG__`.bronze.orders_raw
WHERE order_id IS NOT NULL AND customer_id IS NOT NULL
  AND try_cast(order_date AS DATE) IS NOT NULL
QUALIFY row_number() OVER (PARTITION BY order_id ORDER BY ingested_at DESC) = 1;
CREATE OR REPLACE TABLE `__CATALOG__`.silver.order_items
COMMENT 'Validated synthetic order items; unique item id and positive quantity and unit price.'
AS SELECT order_item_id, order_id, product_id,
  try_cast(quantity AS INT) AS quantity, try_cast(unit_price AS DECIMAL(12, 2)) AS unit_price
FROM `__CATALOG__`.bronze.order_items_raw
WHERE order_item_id IS NOT NULL AND order_id IS NOT NULL AND product_id IS NOT NULL
  AND try_cast(quantity AS INT) > 0 AND try_cast(unit_price AS DECIMAL(12, 2)) > 0
QUALIFY row_number() OVER (PARTITION BY order_item_id ORDER BY ingested_at DESC) = 1;

COMMENT ON COLUMN `__CATALOG__`.silver.customers.customer_id IS 'Customer primary key; joins to silver.orders.customer_id.';
COMMENT ON COLUMN `__CATALOG__`.silver.customers.region IS 'Normalized sales region; synonyms include territory and market.';
COMMENT ON COLUMN `__CATALOG__`.silver.products.product_id IS 'Product primary key; joins to silver.order_items.product_id.';
COMMENT ON COLUMN `__CATALOG__`.silver.products.unit_price IS 'Synthetic list price in USD.';
COMMENT ON COLUMN `__CATALOG__`.silver.orders.order_id IS 'Order primary key; joins to silver.order_items.order_id.';
COMMENT ON COLUMN `__CATALOG__`.silver.orders.order_status IS 'Normalized order status; only complete orders count as sales.';
COMMENT ON COLUMN `__CATALOG__`.silver.order_items.quantity IS 'Number of product units in the order line.';
COMMENT ON COLUMN `__CATALOG__`.silver.order_items.unit_price IS 'Synthetic USD price per unit at order time.';

CREATE OR REPLACE VIEW `__CATALOG__`.gold.sales_summary
COMMENT 'Synthetic completed sales by order date, region, and product. Sales, revenue, and bookings mean extended_amount in USD. Excludes cancelled orders.'
AS SELECT o.order_date, c.region, p.product_id, p.product_name, p.category,
  sum(i.quantity) AS units_sold,
  sum(i.quantity * i.unit_price) AS revenue_usd,
  count(DISTINCT o.order_id) AS order_count
FROM `__CATALOG__`.silver.orders AS o
JOIN `__CATALOG__`.silver.customers AS c ON c.customer_id = o.customer_id
JOIN `__CATALOG__`.silver.order_items AS i ON i.order_id = o.order_id
JOIN `__CATALOG__`.silver.products AS p ON p.product_id = i.product_id
WHERE o.order_status = 'complete'
GROUP BY o.order_date, c.region, p.product_id, p.product_name, p.category;
CREATE OR REPLACE VIEW `__CATALOG__`.gold.customer_summary
COMMENT 'Synthetic customer lifetime summary. Lifetime value and spend mean lifetime_revenue_usd in USD; includes completed orders only.'
AS SELECT c.customer_id, c.customer_name, c.region,
  count(DISTINCT o.order_id) AS completed_order_count,
  coalesce(sum(i.quantity * i.unit_price), 0) AS lifetime_revenue_usd
FROM `__CATALOG__`.silver.customers AS c
LEFT JOIN `__CATALOG__`.silver.orders AS o
  ON o.customer_id = c.customer_id AND o.order_status = 'complete'
LEFT JOIN `__CATALOG__`.silver.order_items AS i ON i.order_id = o.order_id
GROUP BY c.customer_id, c.customer_name, c.region;

COMMENT ON COLUMN `__CATALOG__`.gold.sales_summary.revenue_usd IS 'Completed-order revenue in USD; synonym: sales.';
COMMENT ON COLUMN `__CATALOG__`.gold.sales_summary.units_sold IS 'Total completed units; synonym: quantity sold.';
COMMENT ON COLUMN `__CATALOG__`.gold.customer_summary.lifetime_revenue_usd IS 'Completed-order customer revenue in USD; synonyms: customer spend, lifetime value.';