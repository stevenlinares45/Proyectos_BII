# E-commerce Olist — Plataforma de datos en Microsoft Fabric

**Sector:** E-commerce / Retail
**Rol:** Ingeniería de datos end-to-end (ingesta → modelado → Warehouse → modelo semántico → reporte → orquestación)

> ℹ️ **Nota sobre los datos:** como el proyecto 09, usa un **dataset público** (*Brazilian E-Commerce Public Dataset by Olist*, Kaggle, ~99 mil pedidos 2016-2018), no un cliente real; no aplica la nota de confidencialidad. Los CSV **no** se versionan en este repositorio: se descargan de Kaggle.

## Contexto y problema

Un marketplace necesita entender **ventas, logística y satisfacción** en un mismo modelo: cuánto vende, dónde, qué categorías lideran, qué tan puntual es la entrega y cómo afecta eso a la experiencia del cliente.

**Preguntas de negocio que responde el modelo:**
1. Ventas, pedidos, ticket medio y crecimiento año contra año.
2. Qué categorías y estados concentran las ventas.
3. % de entregas a tiempo y días de entrega, por estado.
4. Cómo cambia la puntuación de las reseñas según la entrega sea puntual o tardía.

## Arquitectura

```
CSV (Lakehouse Files)
   │
   ▼
BRONZE  lh_olist.bronze   texto + trazabilidad (_ingested_at, _source_file)        [PySpark]
   ▼
SILVER  lh_olist.silver   tipos, deduplicación, texto normalizado, CP a 5 dígitos  [Spark SQL]
   ▼
GOLD    lh_olist.gold     modelo estrella: 5 dimensiones + 3 hechos                [Spark SQL]
   ▼
WAREHOUSE wh_olist.dwh    carga idempotente con controles + vistas de negocio      [T-SQL]
   ▼
MODELO SEMÁNTICO sm_olist (Direct Lake)   8 tablas · 7 relaciones · 12 medidas DAX
   ▼
INFORME POWER BI rpt_olist                panel ejecutivo

Orquestación: pipeline pl_olist_diario  (01_bronze → 02_silver → 03_gold)
```

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| `notebooks/` | `01_bronze`, `02_silver`, `03_gold` (formato `.ipynb`, importables a Fabric) |
| `warehouse/` | Carga idempotente con bitácora y vistas de negocio (T-SQL) |
| `semantic_model/` | `model.bim` (Direct Lake), `medidas.dax` |
| `report/` | Definición del informe en formato PBIR |
| `pipelines/` | Definición del pipeline de orquestación |
| `scripts/` | Utilidades para publicar el modelo/informe y ejecutar T-SQL desde Python |
| `docs/` | Guía paso a paso y resumen final |

## Modelo de datos (Gold)

- `fact_ventas` — grano: **una línea de pedido** (112.650 filas).
- `fact_pagos` y `fact_resenas` van **aparte**: mezclar hechos de distinto grano duplicaría importes.
- `dim_pedido` es el puente (un `order_id` repetido en `fact_ventas` no puede relacionarse directamente con pagos y reseñas).
- Dimensiones: `dim_fecha` (generada), `dim_cliente`, `dim_producto`, `dim_vendedor`, `dim_pedido`.

## Técnicas destacadas

**1. Carga idempotente con controles (Warehouse).** `TRUNCATE + INSERT` dentro de una transacción, comparación de conteos origen/destino, `ROLLBACK` si no cuadran, y bitácora en `dwh.control_cargas`. Cargarla 1 o 10 veces deja el mismo resultado.

```sql
BEGIN TRAN;
    TRUNCATE TABLE dwh.tabla;
    INSERT INTO dwh.tabla SELECT * FROM lh_olist.gold.tabla;
    IF @origen <> @destino THROW 50002, 'El conteo de filas no coincide con el origen', 1;
COMMIT;
```

**2. Control de calidad por capa.** Bronze falla si algún conteo difiere del esperado; Silver mide reglas (precio ≤ 0, huérfanos, fechas incoherentes); Gold cuadra importes contra Silver y verifica integridad referencial.

**3. `NULL` con significado.** `entrega_a_tiempo` es `NULL` cuando el pedido no se entregó: no cuenta ni como puntual ni como tardío.

**4. Direct Lake sobre el Warehouse**, con inteligencia de tiempo (`TOTALYTD`, `SAMEPERIODLASTYEAR`) sobre una tabla de fechas marcada.

## Resultados verificados

| Control | Resultado |
|---|---|
| Ventas Silver vs Gold | 13.591.643,70 en ambos (diferencia 0,00) |
| Integridad referencial (Gold) | 0 huérfanos en 7 reglas |
| Warehouse vs Gold | 8 tablas con idéntico número de filas |
| Carga del Warehouse repetida | Sin duplicados (3.095 filas en `dim_vendedor` tras 3 cargas) |
| Modelo semántico vs Gold | Ventas 13.591.643,70 · 98.666 pedidos |

## Hallazgos de negocio

- Las reseñas de entregas **a tiempo promedian 4,30**; con **retraso, 2,57**; sin entregar, 1,74.
- **92,1 %** de entregas a tiempo; Río de Janeiro (87,0 %) es la más baja entre los estados grandes.
- **São Paulo** concentra ~38 % de las ventas; las ventas crecieron **+19,99 %** en 2018.
- 775 pedidos nunca tuvieron líneas (cancelados o no disponibles): no cuentan como venta.

## Cómo reproducirlo

1. Descargar el dataset de Kaggle y subir los 9 CSV a `Files/olist/` de un Lakehouse con esquemas (`bronze`, `silver`, `gold`).
2. Importar y ejecutar los notebooks `01` → `02` → `03` (o el pipeline `pl_olist_diario`).
3. Crear el Warehouse, ejecutar los scripts de `warehouse/` y publicar `semantic_model/` y `report/`.

> Los notebooks y definiciones contienen identificadores (GUID) del entorno donde se construyó; hay que reemplazarlos por los del entorno propio.

## Lecciones aprendidas

- Detener la **sesión Spark con el botón rojo** antes de cerrar o recargar un notebook; si no, queda activa en el servidor y satura la capacidad (error 430).
- Un pipeline **orquesta**, no transforma: la transformación vive en notebooks o en el Warehouse.
- Una carga "anexar al destino" duplica datos al repetirse: preferir vaciar y recargar o `MERGE`.

## Stack técnico
Microsoft Fabric · Lakehouse · Delta Lake · PySpark · Spark SQL · Warehouse (T-SQL) · Direct Lake · DAX · Power BI (PBIR) · Data Pipelines
