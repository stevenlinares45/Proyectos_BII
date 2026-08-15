-- ============================================================
-- BRONZE: ingesta cruda del dataset DataCo Smart Supply Chain
-- Catalogo: bootcamp | Schema: transporte_bronze | Tabla: envios_raw
-- ============================================================
-- Fuente: Kaggle - DataCo Smart Supply Chain for Big Data Analysis
-- https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis
--
-- Ingesta reproducible (requiere kaggle.json en ~/.kaggle/):
--   import kagglehub
--   path = kagglehub.dataset_download("shashwatwork/dataco-smart-supply-chain-for-big-data-analysis")
--
-- El CSV resultante se sube al Volume de Unity Catalog:
--   /Volumes/bootcamp/transporte_bronze/landing/DataCoSupplyChainDataset.csv
--
-- Regla de Bronze: SIN transformar datos de negocio. Unico cambio permitido:
-- normalizar nombres de columna (Delta no admite espacios/parentesis en
-- nombres de columna sin Column Mapping) y agregar metadata de ingesta.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS bootcamp.transporte_bronze
  COMMENT 'Proyecto Transporte/Logistica (DataCo) - capa Bronze: datos crudos';

CREATE VOLUME IF NOT EXISTS bootcamp.transporte_bronze.landing
  COMMENT 'Landing zone para archivos crudos del dataset DataCo';

CREATE OR REPLACE TABLE bootcamp.transporte_bronze.envios_raw
USING DELTA
AS
SELECT
  `Type`                            AS type,
  `Days for shipping (real)`        AS days_for_shipping_real,
  `Days for shipment (scheduled)`   AS days_for_shipment_scheduled,
  `Benefit per order`               AS benefit_per_order,
  `Sales per customer`              AS sales_per_customer,
  `Delivery Status`                 AS delivery_status,
  `Late_delivery_risk`              AS late_delivery_risk,
  `Category Id`                     AS category_id,
  `Category Name`                   AS category_name,
  `Customer City`                   AS customer_city,
  `Customer Country`                AS customer_country,
  `Customer Email`                  AS customer_email,
  `Customer Fname`                  AS customer_fname,
  `Customer Id`                     AS customer_id,
  `Customer Lname`                  AS customer_lname,
  `Customer Password`               AS customer_password,
  `Customer Segment`                AS customer_segment,
  `Customer State`                  AS customer_state,
  `Customer Street`                 AS customer_street,
  `Customer Zipcode`                AS customer_zipcode,
  `Department Id`                   AS department_id,
  `Department Name`                 AS department_name,
  `Latitude`                        AS latitude,
  `Longitude`                       AS longitude,
  `Market`                          AS market,
  `Order City`                      AS order_city,
  `Order Country`                   AS order_country,
  `Order Customer Id`               AS order_customer_id,
  `order date (DateOrders)`         AS order_date,
  `Order Id`                        AS order_id,
  `Order Item Cardprod Id`          AS order_item_cardprod_id,
  `Order Item Discount`             AS order_item_discount,
  `Order Item Discount Rate`        AS order_item_discount_rate,
  `Order Item Id`                   AS order_item_id,
  `Order Item Product Price`        AS order_item_product_price,
  `Order Item Profit Ratio`         AS order_item_profit_ratio,
  `Order Item Quantity`             AS order_item_quantity,
  `Sales`                           AS sales,
  `Order Item Total`                AS order_item_total,
  `Order Profit Per Order`          AS order_profit_per_order,
  `Order Region`                    AS order_region,
  `Order State`                     AS order_state,
  `Order Status`                    AS order_status,
  `Order Zipcode`                   AS order_zipcode,
  `Product Card Id`                 AS product_card_id,
  `Product Category Id`             AS product_category_id,
  `Product Description`             AS product_description,
  `Product Image`                   AS product_image,
  `Product Name`                    AS product_name,
  `Product Price`                   AS product_price,
  `Product Status`                  AS product_status,
  `shipping date (DateOrders)`      AS shipping_date,
  `Shipping Mode`                   AS shipping_mode,
  'DataCoSupplyChainDataset.csv'    AS _source_file,
  current_timestamp()               AS _ingested_at
FROM read_files(
  '/Volumes/bootcamp/transporte_bronze/landing/DataCoSupplyChainDataset.csv',
  format      => 'csv',
  header      => true,
  encoding    => 'ISO-8859-1',   -- el CSV trae caracteres fuera de UTF-8
  inferSchema => true
);

-- Verificacion: debe dar 180519 filas (igual al CSV origen)
-- SELECT count(*) FROM bootcamp.transporte_bronze.envios_raw;
