-- ============================================================
-- GOLD: modelo dimensional (Star Schema) para Power BI
-- Catalogo: bootcamp | Schema: transporte_gold
-- ============================================================
-- fact_envios  (grano: 1 fila = 1 item de orden)
--   -> dim_fecha      (por order_date y shipping_date)
--   -> dim_cliente
--   -> dim_producto
--   -> dim_geografia  (region/estado/pais/ciudad del pedido)
--   -> dim_modo_envio
--
-- Nota de idempotencia: el dataset de origen es un extracto historico
-- estatico (no CDC), por eso el rebuild completo (CREATE OR REPLACE)
-- es determinista e idempotente: correr esto 2 veces da el mismo
-- resultado. Si en el futuro llegan cargas incrementales reales,
-- las dimensiones pasan a MERGE con row_hash (ver seccion "Estrategias
-- de carga" del playbook) y el fact a MERGE por order_item_id.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS bootcamp.transporte_gold
  COMMENT 'Proyecto Transporte/Logistica (DataCo) - capa Gold: modelo star schema para BI';

-- ---------- DIM FECHA ----------
CREATE OR REPLACE TABLE bootcamp.transporte_gold.dim_fecha
USING DELTA
AS
WITH fechas AS (
  SELECT explode(sequence(
    (SELECT date(min(order_date)) FROM bootcamp.transporte_silver.envios_clean),
    (SELECT date(max(shipping_date)) FROM bootcamp.transporte_silver.envios_clean),
    interval 1 day
  )) AS fecha
)
SELECT
  CAST(date_format(fecha, 'yyyyMMdd') AS INT) AS sk_fecha,
  fecha,
  year(fecha)                                  AS anio,
  month(fecha)                                 AS mes,
  date_format(fecha, 'MMMM')                   AS nombre_mes,
  day(fecha)                                   AS dia,
  dayofweek(fecha)                             AS dia_semana_num,
  date_format(fecha, 'EEEE')                   AS dia_semana_nombre,
  quarter(fecha)                                AS trimestre,
  weekofyear(fecha)                            AS semana_anio,
  CASE WHEN dayofweek(fecha) IN (1,7) THEN true ELSE false END AS es_fin_de_semana
FROM fechas;

-- ---------- DIM CLIENTE ----------
CREATE OR REPLACE TABLE bootcamp.transporte_gold.dim_cliente
USING DELTA
AS
SELECT
  ROW_NUMBER() OVER (ORDER BY customer_id) AS sk_cliente,
  customer_id,
  customer_segment,
  customer_city,
  customer_state,
  customer_country
FROM (
  SELECT DISTINCT customer_id, customer_segment, customer_city, customer_state, customer_country
  FROM bootcamp.transporte_silver.envios_clean
);

-- ---------- DIM PRODUCTO ----------
CREATE OR REPLACE TABLE bootcamp.transporte_gold.dim_producto
USING DELTA
AS
SELECT
  ROW_NUMBER() OVER (ORDER BY product_card_id) AS sk_producto,
  product_card_id,
  product_name,
  category_name,
  department_name
FROM (
  SELECT DISTINCT product_card_id, product_name, category_name, department_name
  FROM bootcamp.transporte_silver.envios_clean
);

-- ---------- DIM GEOGRAFIA (destino del pedido) ----------
CREATE OR REPLACE TABLE bootcamp.transporte_gold.dim_geografia
USING DELTA
AS
SELECT
  ROW_NUMBER() OVER (ORDER BY order_country, order_region, order_state, order_city) AS sk_geografia,
  order_country  AS pais,
  order_region   AS region,
  order_state    AS estado,
  order_city     AS ciudad,
  market         AS mercado
FROM (
  SELECT DISTINCT order_country, order_region, order_state, order_city, market
  FROM bootcamp.transporte_silver.envios_clean
);

-- ---------- DIM MODO DE ENVIO ----------
CREATE OR REPLACE TABLE bootcamp.transporte_gold.dim_modo_envio
USING DELTA
AS
SELECT
  ROW_NUMBER() OVER (ORDER BY shipping_mode, type) AS sk_modo_envio,
  shipping_mode,
  type AS tipo_pago
FROM (
  SELECT DISTINCT shipping_mode, type
  FROM bootcamp.transporte_silver.envios_clean
);

-- ---------- FACT ENVIOS ----------
CREATE OR REPLACE TABLE bootcamp.transporte_gold.fact_envios
USING DELTA
AS
SELECT
  e.order_item_id,
  e.order_id,
  df_pedido.sk_fecha  AS sk_fecha_pedido,
  df_envio.sk_fecha   AS sk_fecha_envio,
  dc.sk_cliente,
  dp.sk_producto,
  dg.sk_geografia,
  dm.sk_modo_envio,
  e.order_item_quantity,
  e.order_item_product_price,
  e.order_item_discount,
  e.order_item_discount_rate,
  e.sales,
  e.order_item_total,
  e.benefit_per_order,
  e.order_profit_per_order,
  e.order_item_profit_ratio,
  e.days_for_shipping_real,
  e.days_for_shipment_scheduled,
  (e.days_for_shipping_real - e.days_for_shipment_scheduled) AS dias_diferencia_entrega,
  e.late_delivery_risk,
  e.delivery_status,
  e.order_status
FROM bootcamp.transporte_silver.envios_clean e
JOIN bootcamp.transporte_gold.dim_fecha df_pedido ON date(e.order_date)   = df_pedido.fecha
JOIN bootcamp.transporte_gold.dim_fecha df_envio  ON date(e.shipping_date) = df_envio.fecha
JOIN bootcamp.transporte_gold.dim_cliente dc      ON e.customer_id  = dc.customer_id
JOIN bootcamp.transporte_gold.dim_producto dp     ON e.product_card_id = dp.product_card_id
JOIN bootcamp.transporte_gold.dim_geografia dg    ON e.order_country = dg.pais
                                                  AND e.order_region  = dg.region
                                                  AND e.order_state   = dg.estado
                                                  AND e.order_city    = dg.ciudad
JOIN bootcamp.transporte_gold.dim_modo_envio dm   ON e.shipping_mode = dm.shipping_mode
                                                  AND e.type = dm.tipo_pago;

-- Verificacion: el fact no deberia perder filas contra silver por joins fallidos
-- SELECT (SELECT count(*) FROM bootcamp.transporte_silver.envios_clean) AS silver,
--        (SELECT count(*) FROM bootcamp.transporte_gold.fact_envios)   AS gold;
