-- ============================================================
-- SILVER: limpieza, tipado y anonimizacion
-- Catalogo: bootcamp | Schema: transporte_silver | Tabla: envios_clean
-- ============================================================
-- Grano: 1 fila = 1 item de orden (order_item_id es la PK natural)
--
-- Reglas aplicadas:
--   1. Tipar fechas (vienen como string en Bronze)
--   2. Quitar columnas PII: email, password, nombre, apellido, calle
--      (el dataset es sintetico/publico, pero se anonimiza igual como
--      buena practica -> mismo criterio que el resto del portafolio)
--   3. Deduplicar por order_item_id (clave natural del grano)
--   4. Descartar filas con claves nulas o fechas invalidas
--      (shipping_date < order_date no tiene sentido de negocio)
--   5. Idempotente: CREATE OR REPLACE sobre un origen Bronze de snapshot
--      completo (no incremental todavia). Cuando se automatice con Jobs,
--      pasa a MERGE por order_item_id.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS bootcamp.transporte_silver
  COMMENT 'Proyecto Transporte/Logistica (DataCo) - capa Silver: datos limpios y tipados';

CREATE OR REPLACE TABLE bootcamp.transporte_silver.envios_clean
USING DELTA
AS
WITH base AS (
  SELECT
    order_item_id,
    order_id,
    type,
    days_for_shipping_real,
    days_for_shipment_scheduled,
    CAST(benefit_per_order AS DECIMAL(12,2))      AS benefit_per_order,
    CAST(sales_per_customer AS DECIMAL(12,2))     AS sales_per_customer,
    delivery_status,
    CAST(late_delivery_risk AS BOOLEAN)           AS late_delivery_risk,
    category_id,
    category_name,
    customer_city,
    customer_country,
    customer_id,
    customer_segment,
    customer_state,
    customer_zipcode,
    department_id,
    department_name,
    latitude,
    longitude,
    market,
    order_city,
    order_country,
    order_customer_id,
    to_timestamp(order_date, 'M/d/yyyy H:mm')     AS order_date,
    order_item_cardprod_id,
    CAST(order_item_discount AS DECIMAL(12,2))    AS order_item_discount,
    CAST(order_item_discount_rate AS DECIMAL(6,4)) AS order_item_discount_rate,
    CAST(order_item_product_price AS DECIMAL(12,2)) AS order_item_product_price,
    CAST(order_item_profit_ratio AS DECIMAL(6,4)) AS order_item_profit_ratio,
    CAST(order_item_quantity AS INT)              AS order_item_quantity,
    CAST(sales AS DECIMAL(12,2))                  AS sales,
    CAST(order_item_total AS DECIMAL(12,2))       AS order_item_total,
    CAST(order_profit_per_order AS DECIMAL(12,2)) AS order_profit_per_order,
    order_region,
    order_state,
    order_status,
    product_card_id,
    product_category_id,
    product_name,
    CAST(product_price AS DECIMAL(12,2))          AS product_price,
    product_status,
    to_timestamp(shipping_date, 'M/d/yyyy H:mm')  AS shipping_date,
    shipping_mode,
    _source_file,
    _ingested_at,
    ROW_NUMBER() OVER (
      PARTITION BY order_item_id
      ORDER BY _ingested_at DESC
    ) AS rn
  FROM bootcamp.transporte_bronze.envios_raw
  WHERE order_item_id IS NOT NULL
    AND order_id IS NOT NULL
)
SELECT * EXCEPT (rn)
FROM base
WHERE rn = 1
  AND order_date IS NOT NULL
  AND shipping_date IS NOT NULL
  AND shipping_date >= order_date;

-- Verificacion de calidad (ver docs/dq_checks.sql para el detalle completo)
-- SELECT count(*) AS filas, count(DISTINCT order_item_id) AS pk_unica
-- FROM bootcamp.transporte_silver.envios_clean;
