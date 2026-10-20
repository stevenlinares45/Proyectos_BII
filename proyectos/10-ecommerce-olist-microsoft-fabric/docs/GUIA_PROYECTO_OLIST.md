# Guía de inicio a fin: Proyecto Olist en Microsoft Fabric

Objetivo: construir una plataforma de datos completa (ingesta → limpieza → modelo → BI → orquestación → tiempo real → gobierno) con un dataset real, entendiendo **por qué** se hace cada paso.

Tiempo estimado: 10-15 horas, repartidas en 10 fases. Cada fase termina con un **checkpoint**: no pases a la siguiente sin cumplirlo.

---

## Mapa mental (léelo primero)

```
CSV (Kaggle) ──► BRONZE ──► SILVER ──► GOLD ──► Semantic Model ──► Power BI
                 crudo      limpio     estrella   (Direct Lake)     reporte
                    └──────── Notebooks PySpark + Delta ─────┘
                    └──────── Data Pipeline orquesta todo ───┘
                                  Warehouse (T-SQL) lee Gold
Eventstream ──► Eventhouse (KQL) ──► Dashboard en vivo
```

Conceptos que dominarás:
- **Lakehouse**: archivos (`Files/`) + tablas Delta (`Tables/`). Es donde trabaja Spark.
- **Medallion**: Bronze (copia fiel), Silver (confiable), Gold (listo para negocio).
- **Delta**: formato de tabla con transacciones, versionado y time travel.
- **OneLake**: un único almacenamiento para todo Fabric. Lakehouse, Warehouse y Power BI leen lo mismo sin copiar.
- **Direct Lake**: Power BI lee directo las tablas Delta, sin importar datos.

---

## Fase 0. Preparación

1. Cuenta de Fabric con **trial** o capacidad activa (foto de perfil → "Free trial").
2. Descarga el dataset: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
3. Descomprime en `raw_data/olist/`. Deben ser 9 archivos:

| Archivo | Contenido | Llave |
|---|---|---|
| olist_orders_dataset | pedidos y fechas de estado | order_id |
| olist_order_items_dataset | líneas de pedido (precio, flete) | order_id + order_item_id |
| olist_order_payments_dataset | pagos | order_id + payment_sequential |
| olist_order_reviews_dataset | reseñas | review_id |
| olist_customers_dataset | clientes | customer_id |
| olist_products_dataset | productos | product_id |
| olist_sellers_dataset | vendedores | seller_id |
| olist_geolocation_dataset | coordenadas por CP | (muchas filas repetidas) |
| product_category_name_translation | portugués → inglés | product_category_name |

**Ojo con `customer_id` vs `customer_unique_id`**: `customer_id` cambia en cada pedido; la persona real es `customer_unique_id`. Se usa en Gold.

**Checkpoint:** 9 CSV en la carpeta y trial activo.

---

## Fase 1. Workspace y Lakehouse

Para mantenerlo simple usaremos **un solo Lakehouse con esquemas** (bronze / silver / gold) en vez de tres lakehouses.

1. Portal Fabric → **Workspaces → New workspace** → `ws_olist` → License mode **Trial**.
2. **New item → Lakehouse** → nombre `lh_olist` → marca **Lakehouse schemas** (si no aparece la opción, ver nota abajo).
3. Crea los esquemas: en el Lakehouse, `Tables` → `...` → **New schema**: `bronze`, `silver`, `gold`.

> Nota: si tu tenant no ofrece esquemas, usa prefijos de tabla: `bronze_orders`, `silver_orders`, `gold_fact_ventas` y reemplaza `bronze.orders` por `bronze_orders` en el código.

**Checkpoint:** ves `lh_olist` con 3 esquemas vacíos.

---

## Fase 2. Ingesta — Bronze

**Regla de oro de Bronze:** no se corrige nada. Se guarda lo que llegó, todo como texto, más metadatos de carga. Si algo sale mal después, siempre puedes reconstruir desde aquí.

### 2.1 Subir archivos
Lakehouse → `Files` → `...` → **New subfolder** `olist` → **Upload → Upload files** → selecciona los 9 CSV.

### 2.2 Notebook `01_bronze`
Workspace → **New item → Notebook** → nombre `01_bronze`. A la izquierda adjunta `lh_olist` como Lakehouse por defecto.

```python
from pyspark.sql import functions as F

archivos = {
    "orders":        "olist_orders_dataset.csv",
    "order_items":   "olist_order_items_dataset.csv",
    "order_payments":"olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "customers":     "olist_customers_dataset.csv",
    "products":      "olist_products_dataset.csv",
    "sellers":       "olist_sellers_dataset.csv",
    "geolocation":   "olist_geolocation_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

for tabla, archivo in archivos.items():
    df = (spark.read
          .option("header", True)
          .option("multiLine", True)      # reseñas con saltos de línea
          .option("quote", '"')
          .option("escape", '"')
          .option("inferSchema", False)   # todo string: Bronze no interpreta
          .csv(f"Files/olist/{archivo}"))

    df = (df.withColumn("_ingested_at", F.current_timestamp())
            .withColumn("_source_file", F.lit(archivo)))

    (df.write.mode("overwrite").format("delta")
       .saveAsTable(f"bronze.{tabla}"))

    print(f"bronze.{tabla}: {df.count()} filas")
```

### 2.3 Validación
```python
for t in archivos:
    print(t, spark.table(f"bronze.{t}").count())
```
Valores esperados aprox.: orders 99.441 · order_items 112.650 · payments 103.886 · reviews ~99.224 · customers 99.441 · products 32.951 · sellers 3.095 · geolocation ~1.000.163 · translation 71.

**Concepto:** `overwrite` hace la carga idempotente: correrla dos veces da el mismo resultado.

**Checkpoint:** 9 tablas en `bronze` con conteos cercanos a los esperados.

---

## Fase 3. Limpieza — Silver

**Objetivo:** tipos correctos, sin duplicados, sin basura, con reglas de calidad medibles.

Notebook `02_silver`:

```python
from pyspark.sql import functions as F

def b(t): return spark.table(f"bronze.{t}")
def guardar(df, nombre):
    df.write.mode("overwrite").format("delta").saveAsTable(f"silver.{nombre}")
    print(f"silver.{nombre}: {df.count()} filas")

# --- orders
orders = (b("orders")
  .dropDuplicates(["order_id"])
  .withColumn("order_purchase_timestamp",      F.to_timestamp("order_purchase_timestamp"))
  .withColumn("order_approved_at",             F.to_timestamp("order_approved_at"))
  .withColumn("order_delivered_carrier_date",  F.to_timestamp("order_delivered_carrier_date"))
  .withColumn("order_delivered_customer_date", F.to_timestamp("order_delivered_customer_date"))
  .withColumn("order_estimated_delivery_date", F.to_timestamp("order_estimated_delivery_date"))
  .drop("_ingested_at", "_source_file"))
guardar(orders, "orders")

# --- order_items
items = (b("order_items")
  .dropDuplicates(["order_id", "order_item_id"])
  .withColumn("order_item_id", F.col("order_item_id").cast("int"))
  .withColumn("shipping_limit_date", F.to_timestamp("shipping_limit_date"))
  .withColumn("price",         F.col("price").cast("decimal(12,2)"))
  .withColumn("freight_value", F.col("freight_value").cast("decimal(12,2)"))
  .drop("_ingested_at", "_source_file"))
guardar(items, "order_items")

# --- payments
pagos = (b("order_payments")
  .withColumn("payment_sequential",   F.col("payment_sequential").cast("int"))
  .withColumn("payment_installments", F.col("payment_installments").cast("int"))
  .withColumn("payment_value",        F.col("payment_value").cast("decimal(12,2)"))
  .drop("_ingested_at", "_source_file"))
guardar(pagos, "order_payments")

# --- reviews (review_id se repite en el dataset: quedarse con la más reciente)
from pyspark.sql.window import Window
w = Window.partitionBy("review_id").orderBy(F.col("review_answer_timestamp").desc())
reviews = (b("order_reviews")
  .withColumn("review_score", F.col("review_score").cast("int"))
  .withColumn("review_creation_date",    F.to_timestamp("review_creation_date"))
  .withColumn("review_answer_timestamp", F.to_timestamp("review_answer_timestamp"))
  .filter(F.col("review_score").between(1, 5))
  .withColumn("rn", F.row_number().over(w)).filter("rn = 1").drop("rn")
  .drop("_ingested_at", "_source_file"))
guardar(reviews, "order_reviews")

# --- customers / sellers (normalizar texto)
customers = (b("customers").dropDuplicates(["customer_id"])
  .withColumn("customer_city",  F.initcap(F.trim("customer_city")))
  .withColumn("customer_state", F.upper(F.trim("customer_state")))
  .drop("_ingested_at", "_source_file"))
guardar(customers, "customers")

sellers = (b("sellers").dropDuplicates(["seller_id"])
  .withColumn("seller_city",  F.initcap(F.trim("seller_city")))
  .withColumn("seller_state", F.upper(F.trim("seller_state")))
  .drop("_ingested_at", "_source_file"))
guardar(sellers, "sellers")

# --- products + traducción de categoría
trad = b("category_translation").select("product_category_name", "product_category_name_english")
products = (b("products").dropDuplicates(["product_id"])
  .join(trad, "product_category_name", "left")
  .withColumn("categoria", F.coalesce("product_category_name_english",
                                      F.col("product_category_name"),
                                      F.lit("unknown")))
  .withColumnRenamed("product_name_lenght", "product_name_length")
  .withColumnRenamed("product_description_lenght", "product_description_length")
  .withColumn("product_weight_g", F.col("product_weight_g").cast("int"))
  .drop("_ingested_at", "_source_file"))
guardar(products, "products")

# --- geolocation: 1 fila por código postal (promedio de coordenadas)
geo = (b("geolocation")
  .withColumn("lat", F.col("geolocation_lat").cast("double"))
  .withColumn("lng", F.col("geolocation_lng").cast("double"))
  .groupBy("geolocation_zip_code_prefix")
  .agg(F.avg("lat").alias("lat"), F.avg("lng").alias("lng"),
       F.first("geolocation_state").alias("state")))
guardar(geo, "geolocation")
```

### Reglas de calidad (data quality)
```python
checks = {
  "orders sin order_id":        spark.table("silver.orders").filter("order_id is null").count(),
  "items con precio <= 0":      spark.table("silver.order_items").filter("price <= 0").count(),
  "items sin pedido (huérfanos)": spark.table("silver.order_items")
        .join(spark.table("silver.orders"), "order_id", "left_anti").count(),
  "entrega antes de compra":    spark.table("silver.orders")
        .filter("order_delivered_customer_date < order_purchase_timestamp").count(),
}
for k, v in checks.items():
    print(("OK   " if v == 0 else "REVISAR"), k, v)
```
Si algo da distinto de 0, **no lo ocultes**: documéntalo en `docs/` y decide (filtrar, corregir o marcar con una columna `es_valido`).

**Concepto:** Silver es donde se decide la verdad de los datos; por eso es donde viven las reglas de calidad.

**Checkpoint:** 9 tablas en `silver`, tipos correctos (`df.printSchema()`), checks sin sorpresas no explicadas.

---

## Fase 4. Modelado — Gold (modelo estrella)

Diseño (grano de la tabla de hechos = **una línea de pedido**):

```
dim_fecha ─┐
dim_cliente ┤
dim_producto┼── fact_ventas ── (order_id) ── fact_pagos
dim_vendedor┘                  └─────────── fact_resenas
```

Notebook `03_gold`:

```python
from pyspark.sql import functions as F

def s(t): return spark.table(f"silver.{t}")
def guardar(df, nombre):
    df.write.mode("overwrite").format("delta").saveAsTable(f"gold.{nombre}")
    print(f"gold.{nombre}: {df.count()} filas")

# --- dim_fecha (generada, no viene del dataset)
dim_fecha = (spark.sql("""
    SELECT explode(sequence(to_date('2016-01-01'), to_date('2018-12-31'), interval 1 day)) AS fecha
""")
  .withColumn("fecha_key",  F.date_format("fecha", "yyyyMMdd").cast("int"))
  .withColumn("anio",       F.year("fecha"))
  .withColumn("trimestre",  F.quarter("fecha"))
  .withColumn("mes",        F.month("fecha"))
  .withColumn("nombre_mes", F.date_format("fecha", "MMMM"))
  .withColumn("dia_semana", F.date_format("fecha", "EEEE"))
  .withColumn("es_fin_semana", F.dayofweek("fecha").isin(1, 7)))
guardar(dim_fecha, "dim_fecha")

# --- dim_cliente (persona real = customer_unique_id)
dim_cliente = (s("customers").select(
    "customer_id", "customer_unique_id",
    F.col("customer_city").alias("ciudad"),
    F.col("customer_state").alias("estado"),
    F.col("customer_zip_code_prefix").alias("cp")))
guardar(dim_cliente, "dim_cliente")

# --- dim_producto
dim_producto = s("products").select(
    "product_id", "categoria", "product_weight_g", "product_photos_qty")
guardar(dim_producto, "dim_producto")

# --- dim_vendedor
dim_vendedor = s("sellers").select(
    "seller_id",
    F.col("seller_city").alias("ciudad"),
    F.col("seller_state").alias("estado"))
guardar(dim_vendedor, "dim_vendedor")

# --- fact_ventas (grano: línea de pedido)
o = s("orders")
fact_ventas = (s("order_items")
  .join(o, "order_id")
  .select(
    "order_id", "order_item_id", "customer_id", "product_id", "seller_id",
    F.date_format("order_purchase_timestamp", "yyyyMMdd").cast("int").alias("fecha_key"),
    "order_status", "price", "freight_value",
    (F.col("price") + F.col("freight_value")).alias("total_linea"),
    "order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date",
    F.datediff("order_delivered_customer_date", "order_purchase_timestamp").alias("dias_entrega"),
    (F.col("order_delivered_customer_date") <= F.col("order_estimated_delivery_date")).alias("entrega_a_tiempo")))
guardar(fact_ventas, "fact_ventas")

# --- fact_pagos y fact_resenas (a nivel pedido)
guardar(s("order_payments"), "fact_pagos")
guardar(s("order_reviews").select("review_id", "order_id", "review_score", "review_creation_date"),
        "fact_resenas")
```

**Por qué dos hechos aparte?** Un pedido tiene varios ítems y varios pagos. Si unes ítems con pagos, **duplicas importes**. Error clásico: nunca mezcles hechos de distinto grano en una sola tabla.

### Validación cruzada (muy importante)
```python
print(spark.sql("""
  SELECT ROUND(SUM(price),2) AS ventas_gold FROM gold.fact_ventas
""").first())
print(spark.sql("""
  SELECT ROUND(SUM(CAST(price AS decimal(18,2))),2) AS ventas_silver FROM silver.order_items
""").first())
```
Deben ser **idénticos**. Si no lo son, tu join perdió o duplicó filas.

**Checkpoint:** 7 tablas en `gold` y ventas Gold = ventas Silver (~13,59 M BRL).

---

## Fase 5. Data Warehouse y T-SQL

Practicas el otro motor de Fabric: el Warehouse (T-SQL, sin Spark).

1. **New item → Warehouse** → `wh_olist`.
2. **Add Lakehouse** (panel izquierdo) para consultar `lh_olist` desde el Warehouse.
3. En el editor SQL:

```sql
-- Copiar una tabla Gold al Warehouse con CTAS
CREATE TABLE dbo.fact_ventas AS
SELECT * FROM lh_olist.gold.fact_ventas;

-- Vista de negocio
CREATE VIEW dbo.vw_ventas_mensuales AS
SELECT f.anio, f.mes, p.categoria,
       SUM(v.price) AS ventas, COUNT(DISTINCT v.order_id) AS pedidos
FROM lh_olist.gold.fact_ventas v
JOIN lh_olist.gold.dim_fecha    f ON f.fecha_key  = v.fecha_key
JOIN lh_olist.gold.dim_producto p ON p.product_id = v.product_id
GROUP BY f.anio, f.mes, p.categoria;

-- Practica: top 10 categorías por ventas
SELECT TOP 10 categoria, SUM(ventas) AS ventas
FROM dbo.vw_ventas_mensuales GROUP BY categoria ORDER BY ventas DESC;
```

**Concepto:** Lakehouse y Warehouse comparten OneLake. Puedes consultar uno desde el otro sin mover datos. Cuándo usar cuál: Lakehouse para ingeniería/Spark, Warehouse para equipos SQL y T-SQL transaccional.

**Checkpoint:** la vista devuelve resultados y el top 10 tiene sentido (cama_mesa_banho / health_beauty / watches arriba).

---

## Fase 6. Semantic model (Direct Lake)

1. Lakehouse `lh_olist` → **New semantic model** → nombre `sm_olist` → selecciona las tablas de `gold`.
2. Abre **Model view** y crea relaciones (muchos a uno, filtro único):
   - `fact_ventas[fecha_key]` → `dim_fecha[fecha_key]`
   - `fact_ventas[customer_id]` → `dim_cliente[customer_id]`
   - `fact_ventas[product_id]` → `dim_producto[product_id]`
   - `fact_ventas[seller_id]` → `dim_vendedor[seller_id]`
   - `fact_resenas[order_id]` y `fact_pagos[order_id]` → relación con `fact_ventas[order_id]` (cuidado: `order_id` no es único en `fact_ventas`; para estos usa medidas con `DISTINCTCOUNT` o crea una tabla `dim_pedido` con un `order_id` único).
3. Marca `dim_fecha` como **tabla de fechas** (`fecha`).
4. Medidas DAX (**New measure**):

```dax
Ventas = SUM(fact_ventas[price])
Flete = SUM(fact_ventas[freight_value])
Pedidos = DISTINCTCOUNT(fact_ventas[order_id])
Clientes unicos = DISTINCTCOUNT(dim_cliente[customer_unique_id])
Ticket Medio = DIVIDE([Ventas], [Pedidos])
% Entrega a Tiempo =
    DIVIDE(
        CALCULATE(COUNTROWS(fact_ventas), fact_ventas[entrega_a_tiempo] = TRUE()),
        CALCULATE(COUNTROWS(fact_ventas), NOT ISBLANK(fact_ventas[entrega_a_tiempo]))
    )
Dias Entrega Prom = AVERAGE(fact_ventas[dias_entrega])
Score Promedio = AVERAGE(fact_resenas[review_score])
Ventas YTD = TOTALYTD([Ventas], dim_fecha[fecha])
Ventas Año Anterior = CALCULATE([Ventas], SAMEPERIODLAYEAR(dim_fecha[fecha]))
Crecimiento YoY = DIVIDE([Ventas] - [Ventas Año Anterior], [Ventas Año Anterior])
```

**Concepto:** en Direct Lake no hay refresh de importación; el modelo lee los Delta. Después de correr el notebook Gold, los datos ya están actualizados (puede requerir un *reframe*).

**Checkpoint:** una tabla de prueba con `Ventas` por año coincide con el total de Gold.

---

## Fase 7. Reporte Power BI

Desde `sm_olist` → **Create report**. Plan de 3 páginas:

1. **Ejecutivo**: tarjetas (Ventas, Pedidos, Ticket Medio, Score), línea de Ventas por mes, barras por categoría (top 10), mapa o barras por estado.
2. **Logística**: % Entrega a Tiempo, días de entrega por estado, evolución mensual del retraso.
3. **Satisfacción**: distribución de `review_score`, score por categoría, relación entre retraso y score.

Buenas prácticas: máximo 5-6 visuales por página, segmentadores de año y estado, títulos que digan la conclusión ("Las entregas tardías bajan el score en 1,5 puntos"), nada de 3D ni gráficos de torta con muchas categorías.

**Checkpoint:** reporte publicado en el workspace, con segmentadores funcionando.

---

## Fase 8. Orquestación (el paso que te vuelve ingeniero)

Un notebook suelto no es una solución; un pipeline que se repite solo, sí.

1. **New item → Data pipeline** → `pl_olist_diario`.
2. Añade 3 actividades **Notebook** encadenadas con la flecha verde (*On success*): `01_bronze` → `02_silver` → `03_gold`.
3. Añade una actividad final que refresque el semantic model (**Semantic model refresh**).
4. Para alertas: en cada notebook actividad, flecha roja (*On fail*) → actividad **Teams** o **Office 365 Outlook**.
5. **Schedule**: diario a las 02:00.
6. Mejora (parametrizar): en pipeline define `ruta_origen` y `fecha_proceso` y pásalos a los notebooks (celda de parámetros).

**Concepto:** el estado de cada ejecución se ve en **Monitor hub**. Aprende a leer errores ahí: es 50% del trabajo real.

**Checkpoint:** ejecución manual completa en verde y visible en Monitor hub.

---

## Fase 9. Real-Time Intelligence (streaming)

Simulas pedidos que llegan en vivo.

1. **New item → Eventhouse** → `eh_olist` (incluye una base KQL).
2. **New item → Eventstream** → `es_pedidos` → **Add source → Custom endpoint**. Copia la *connection string* (Event Hub compatible).
3. **Add destination → Eventhouse** → tabla `PedidosVivos`.
4. Generador en local (instala `pip install azure-eventhub`):

```python
import json, random, time, uuid
from azure.eventhub import EventHubProducerClient, EventData

CONN = "<connection string del custom endpoint>"
producer = EventHubProducerClient.from_connection_string(CONN)

while True:
    evento = {
        "order_id": str(uuid.uuid4()),
        "estado": random.choice(["SP", "RJ", "MG", "RS"]),
        "categoria": random.choice(["health_beauty", "watches_gifts", "bed_bath_table"]),
        "valor": round(random.uniform(20, 400), 2),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    batch = producer.create_batch()
    batch.add(EventData(json.dumps(evento)))
    producer.send_batch(batch)
    time.sleep(1)
```

5. Consulta KQL:
```kusto
PedidosVivos
| where ingestion_time() > ago(5m)
| summarize pedidos = count(), ventas = sum(valor) by bin(todatetime(ts), 30s), estado
| render timechart
```
6. En el editor KQL → **Pin to dashboard** → Real-Time Dashboard con refresco automático.

**Checkpoint:** el gráfico se mueve cada pocos segundos.

---

## Fase 10. Gobierno y DevOps

1. **Git integration**: Workspace settings → Git integration → conecta a un repo (Azure DevOps o GitHub). Haz *commit* de notebooks, pipelines y modelo. Trabaja con ramas.
2. **Deployment pipelines**: crea Dev → Test → Prod y promueve contenido entre etapas.
3. **Linaje**: vista **Lineage** del workspace; confirma que ves Lakehouse → Semantic model → Report.
4. **Seguridad**: roles del workspace (Admin/Member/Contributor/Viewer), RLS en el semantic model (por ejemplo, un vendedor solo ve su estado), etiquetas de sensibilidad.
5. **Mantenimiento Delta** (notebook semanal):
```python
for t in ["fact_ventas", "fact_pagos", "fact_resenas"]:
    spark.sql(f"OPTIMIZE gold.{t}")
    spark.sql(f"VACUUM gold.{t} RETAIN 168 HOURS")
```
6. Practica **time travel**: `DESCRIBE HISTORY gold.fact_ventas` y `SELECT * FROM gold.fact_ventas VERSION AS OF 0`.

---

## Retos de nivel avanzado (cuando termines)

1. Carga **incremental** en Silver con `MERGE INTO` en vez de `overwrite`.
2. Añade tus CSV de `raw_data/` (otro separador y codificación) como segunda fuente y concílialos.
3. Calcula segmentación **RFM** de clientes en Gold y úsala en el reporte.
4. Particiona `fact_ventas` por año y mide la diferencia de rendimiento.
5. Añade pruebas automáticas de calidad que **fallen el pipeline** si hay huérfanos.
6. Documenta todo con un diagrama del linaje en `docs/`.

---

## Errores comunes y cómo salir

| Síntoma | Causa probable | Solución |
|---|---|---|
| `Table or view not found: bronze.orders` | Notebook sin Lakehouse por defecto | Adjunta `lh_olist` en el panel izquierdo |
| Reseñas se parten en varias filas | Faltó `multiLine` / `escape` | Usa las opciones de la Fase 2 |
| Ventas Gold ≠ Silver | Join duplica o pierde filas | Revisa grano y tipo de join |
| Importes inflados en Power BI | Relación mal armada con tabla de pagos | Usa grano de pedido o `DISTINCTCOUNT` |
| Pipeline en rojo | Notebook falló | Monitor hub → ver la celda con error |
| Sin capacidad | Trial vencido o inactivo | Reactiva trial o usa capacidad F2 |

---

## Cómo trabajar conmigo en cada fase

Cuando termines una fase dime **"fase N lista"** y pega el resultado del checkpoint (conteos, errores, capturas). Yo reviso, te explico lo que no cuadre y pasamos a la siguiente. Si te atascas, pega el mensaje de error completo.
