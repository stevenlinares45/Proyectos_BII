-- Fase 5 · Vistas de negocio sobre el modelo estrella del Warehouse.
CREATE VIEW dwh.vw_ventas_mensuales AS
SELECT f.anio, f.mes, f.nombre_mes, p.categoria,
       SUM(v.price)                 AS ventas,
       SUM(v.freight_value)         AS flete,
       COUNT(DISTINCT v.order_id)   AS pedidos
FROM dwh.fact_ventas v
JOIN dwh.dim_fecha    f ON v.fecha_key  = f.fecha_key
JOIN dwh.dim_producto p ON v.product_id = p.product_id
GROUP BY f.anio, f.mes, f.nombre_mes, p.categoria
GO
CREATE VIEW dwh.vw_entregas_por_estado AS
SELECT c.estado,
       COUNT(DISTINCT v.order_id)                          AS pedidos,
       AVG(CAST(v.dias_entrega AS FLOAT))                  AS dias_entrega_prom,
       CAST(100.0 * SUM(CASE WHEN v.entrega_a_tiempo = 1 THEN 1 ELSE 0 END)
            / NULLIF(SUM(CASE WHEN v.entrega_a_tiempo IS NOT NULL THEN 1 ELSE 0 END), 0)
            AS DECIMAL(5,2))                               AS pct_a_tiempo
FROM dwh.fact_ventas v
JOIN dwh.dim_cliente c ON v.customer_id = c.customer_id
GROUP BY c.estado
GO
CREATE VIEW dwh.vw_satisfaccion_entrega AS
SELECT CASE WHEN d.fecha_entrega IS NULL                        THEN '3. sin entregar'
            WHEN d.fecha_entrega <= d.fecha_entrega_estimada    THEN '1. a tiempo'
            ELSE                                                     '2. con retraso' END AS entrega,
       COUNT(*)                              AS resenas,
       CAST(AVG(CAST(r.puntuacion AS FLOAT)) AS DECIMAL(4,2)) AS puntuacion_prom
FROM dwh.fact_resenas r
JOIN dwh.dim_pedido d ON r.order_id = d.order_id
GROUP BY CASE WHEN d.fecha_entrega IS NULL                     THEN '3. sin entregar'
              WHEN d.fecha_entrega <= d.fecha_entrega_estimada THEN '1. a tiempo'
              ELSE                                                  '2. con retraso' END
