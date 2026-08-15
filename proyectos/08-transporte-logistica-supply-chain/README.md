# Transporte y Logística — Supply Chain Analytics

**Sector:** Transporte / Logística / Cadena de suministro
**Rol:** Ingeniería de datos end-to-end (ingesta → modelado → calidad) + preparación para Power BI

> ℹ️ **Nota sobre los datos:** a diferencia del resto del portafolio, este proyecto usa un **dataset público** (DataCo Smart Supply Chain, Kaggle), no un cliente real — así que no aplica la nota de confidencialidad. Aun así se anonimizaron las columnas de PII (email, contraseña, nombre, apellido, calle) como buena práctica de gobierno de datos.

## Contexto y problema

Una cadena de suministro global necesita entender su **desempeño logístico**: qué tan seguido llega tarde, qué combinaciones de región/modo de envío concentran el riesgo de atraso, y si los envíos más rápidos están comiendo la rentabilidad de los pedidos.

**Preguntas de negocio que responde el modelo:**
1. % de pedidos entregados a tiempo vs. tarde, por región y modo de envío.
2. Qué combinaciones (región + modo de envío + categoría) concentran más riesgo de atraso.
3. Días reales vs. programados de entrega, por modo de envío.
4. Rentabilidad del pedido vs. costo/modo de envío.
5. Tendencia mensual de pedidos, atrasos y ventas.
6. Mercados y segmentos de cliente con mayor volumen y mayor tasa de problemas de entrega.

## Arquitectura

```
Kaggle (DataCo CSV, 180.519 filas)
        │  descarga manual / kagglehub
        ▼
Unity Catalog Volume  (bootcamp.transporte_bronze.landing)
        │
        ▼
BRONZE   bootcamp.transporte_bronze.envios_raw
        │  normalizar nombres de columna + metadata de ingesta (sin tocar datos de negocio)
        ▼
SILVER   bootcamp.transporte_silver.envios_clean
        │  tipado, anonimización PII, dedup por order_item_id, validación de fechas
        ▼
GOLD     bootcamp.transporte_gold  (Star Schema)
        │  fact_envios + dim_fecha + dim_cliente + dim_producto + dim_geografia + dim_modo_envio
        ▼
Power BI  (conexión directa al warehouse SQL de Databricks)
```

## Técnicas destacadas

- **Ingesta reproducible**: script documentado con `kagglehub` como fuente oficial (ver [`sql/01_bronze.sql`](sql/01_bronze.sql)).
- **Normalización estructural en Bronze**: los nombres de columna del CSV traían espacios y paréntesis, incompatibles con Delta Lake — se resolvió con alias explícitos, sin alterar los valores.
- **Anonimización en Silver**: se descartan email, contraseña, nombre, apellido y calle del cliente antes de que el dato avance en el pipeline.
- **Deduplicación por clave natural** (`order_item_id`) usando `ROW_NUMBER() OVER (PARTITION BY ...)`.
- **Modelo dimensional (Star Schema)** en Gold: 1 tabla de hechos a nivel de item de orden + 5 dimensiones con claves surrogadas (`sk_*`), incluyendo una `dim_fecha` generada con `sequence()`.
- **Idempotencia documentada**: el rebuild completo (`CREATE OR REPLACE`) es determinista porque la fuente es un snapshot histórico estático; se deja anotado el cambio a `MERGE` con `row_hash` para cuando haya cargas incrementales reales.
- **Calidad de datos verificada con 6 checks** (ver [`sql/04_dq_checks.sql`](sql/04_dq_checks.sql)): unicidad de PK, nulos críticos, consistencia temporal (envío nunca antes del pedido), valores negativos/fuera de rango, integridad referencial y cuadre de volumen entre capas.

## Stack técnico

Databricks (Unity Catalog, Delta Lake, SQL Warehouse serverless) · SQL · Power BI

## Resultado

Pipeline Bronze → Silver → Gold corriendo en Databricks sin pérdida de filas entre capas (180.519 → 180.519 → 180.519) y con los 6 checks de calidad en verde. Modelo Star Schema listo para conectar a Power BI y construir el dashboard de KPIs logísticos.

## Estructura de este proyecto

```
08-transporte-logistica-supply-chain/
├── README.md
├── sql/
│   ├── 01_bronze.sql       -- ingesta cruda
│   ├── 02_silver.sql       -- limpieza, tipado, anonimización
│   ├── 03_gold.sql         -- star schema (fact + 5 dims)
│   └── 04_dq_checks.sql    -- 6 checks de calidad
└── docs/
```

> Los datos (CSV origen y tablas Delta) **no se versionan en este repo** — viven en Databricks (Volume + Unity Catalog). Acá solo queda el código, siguiendo la convención del resto del portafolio.
