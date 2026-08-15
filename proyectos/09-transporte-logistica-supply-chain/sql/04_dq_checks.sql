-- ============================================================
-- CALIDAD DE DATOS: checks sobre Silver y Gold
-- ============================================================
-- Cada check debe devolver 0 filas / 0 en la columna de error para pasar.

-- 1) Unicidad de la PK natural en Silver
SELECT order_item_id, count(*) AS repeticiones
FROM bootcamp.transporte_silver.envios_clean
GROUP BY order_item_id
HAVING count(*) > 1;

-- 2) Nulos en columnas criticas de negocio (Silver)
SELECT
  sum(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END)        AS nulos_customer_id,
  sum(CASE WHEN product_card_id IS NULL THEN 1 ELSE 0 END)    AS nulos_product_id,
  sum(CASE WHEN sales IS NULL THEN 1 ELSE 0 END)              AS nulos_sales,
  sum(CASE WHEN order_date IS NULL THEN 1 ELSE 0 END)         AS nulos_order_date,
  sum(CASE WHEN shipping_date IS NULL THEN 1 ELSE 0 END)      AS nulos_shipping_date
FROM bootcamp.transporte_silver.envios_clean;

-- 3) Consistencia temporal: el envio nunca puede salir antes de pedirse
SELECT count(*) AS envios_antes_del_pedido
FROM bootcamp.transporte_silver.envios_clean
WHERE shipping_date < order_date;

-- 4) Valores negativos donde no deberian existir
SELECT
  sum(CASE WHEN sales < 0 THEN 1 ELSE 0 END)               AS sales_negativas,
  sum(CASE WHEN order_item_quantity <= 0 THEN 1 ELSE 0 END) AS cantidades_invalidas,
  sum(CASE WHEN order_item_discount_rate NOT BETWEEN 0 AND 1 THEN 1 ELSE 0 END) AS descuentos_fuera_de_rango
FROM bootcamp.transporte_silver.envios_clean;

-- 5) Integridad referencial: todo hecho debe tener sus 5 dimensiones resueltas
SELECT count(*) AS hechos_con_fk_nula
FROM bootcamp.transporte_gold.fact_envios
WHERE sk_fecha_pedido IS NULL
   OR sk_fecha_envio  IS NULL
   OR sk_cliente       IS NULL
   OR sk_producto      IS NULL
   OR sk_geografia     IS NULL
   OR sk_modo_envio    IS NULL;

-- 6) Cuadre de volumen entre capas (Bronze debe igualar Silver y Gold,
--    dado que este dataset no tiene registros invalidos conocidos)
SELECT
  (SELECT count(*) FROM bootcamp.transporte_bronze.envios_raw)     AS bronze,
  (SELECT count(*) FROM bootcamp.transporte_silver.envios_clean)   AS silver,
  (SELECT count(*) FROM bootcamp.transporte_gold.fact_envios)      AS gold;
