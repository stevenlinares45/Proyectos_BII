# Proyecto Olist en Microsoft Fabric: resumen final

Plataforma de datos de punta a punta sobre el dataset público de e-commerce de Olist (Brasil, 2016-2018, ~99 mil pedidos).

## Arquitectura

```
CSV (Files/olist) -> BRONZE -> SILVER -> GOLD (modelo estrella) -> WAREHOUSE (dwh) -> Modelo semantico -> Informe Power BI
                      Delta     Delta    Delta + Spark SQL         T-SQL            Direct Lake          rpt_olist
        orquestado por el pipeline pl_olist_diario (01_bronze -> 02_silver -> 03_gold)
```

Todo vive en el workspace `ws_olist`.

## Elementos creados

| Elemento | Tipo | Función |
|---|---|---|
| `lh_olist` | Lakehouse (con esquemas) | `bronze`, `silver`, `gold` |
| `01_bronze` | Notebook PySpark | Ingesta de los 9 CSV como texto, con trazabilidad y control de conteos |
| `02_silver` | Notebook Spark SQL | Tipos, deduplicación, texto normalizado, códigos postales a 5 dígitos |
| `03_gold` | Notebook Spark SQL | Modelo estrella: 5 dimensiones y 3 hechos, con verificaciones |
| `wh_olist` | Warehouse | Esquema `dwh` con las 8 tablas Gold, bitácora y vistas |
| `sm_olist` | Modelo semántico (Direct Lake) | 8 tablas, 7 relaciones, 12 medidas DAX |
| `rpt_olist` | Informe Power BI | Panel ejecutivo de 1 página |
| `pl_olist_diario` | Data Pipeline | Encadena los 3 notebooks; cada paso solo corre si el anterior terminó bien |

El código fuente está en las carpetas del proyecto: `notebooks/`, `warehouse/`, `semantic_model/`, `report/`, `pipelines/`.

## Modelo de datos (Gold)

- Grano de `fact_ventas`: **una línea de pedido** (112.650 filas).
- `fact_pagos` y `fact_resenas` van aparte: mezclar hechos de distinto grano duplicaría importes.
- `dim_pedido` es el puente: `order_id` no es único en `fact_ventas`.

## Resultados verificados

| Control | Resultado |
|---|---|
| Ventas Silver vs Gold | 13.591.643,70 en ambos, diferencia 0,00 |
| Integridad referencial en Gold | 0 huérfanos en las 7 reglas |
| Warehouse vs Gold | Las 8 tablas con el mismo número de filas |
| Carga del Warehouse repetida 3 veces | `dim_vendedor` sigue en 3.095 filas (idempotente) |
| Modelo semántico vs Gold | Ventas 13.591.643,70; pedidos 98.666 |

## Hallazgos de negocio

- **La puntualidad pesa en la satisfacción:** reseñas de entregas a tiempo promedian **4,30**; con retraso, **2,57**; sin entregar, **1,74**.
- Entregas a tiempo: **92,1 %** en total; Río de Janeiro es la más baja entre los grandes estados (87,0 %).
- **São Paulo** concentra ~38 % de las ventas.
- Las ventas crecieron **+19,99 %** en 2018 frente a 2017.
- 775 pedidos nunca tuvieron líneas (cancelados o no disponibles); no cuentan como venta.
- Top categorías: health_beauty, watches_gifts, bed_bath_table.

## Controles de calidad implementados

1. Bronze falla si algún conteo no coincide con el esperado.
2. Silver mide reglas de calidad (precio <= 0, huérfanos, fechas incoherentes).
3. Gold cuadra importes contra Silver y comprueba integridad referencial.
4. El Warehouse carga con `TRUNCATE + INSERT` dentro de una transacción, compara conteos origen/destino, hace ROLLBACK si no cuadran y registra todo en `dwh.control_cargas`.

## Lecciones técnicas

- **Detén la sesión Spark con el botón rojo** antes de cerrar o recargar un notebook; si no, la sesión queda activa en el servidor y satura la capacidad (error 430 `TooManyRequestsForCapacity`).
- "Load to Tables" lanza un trabajo Spark por tabla; encadenar muchas cargas puede agotar la capacidad.
- Un pipeline no transforma: orquesta. La transformación vive en notebooks o en el Warehouse.
- Las cargas "Anexar al destino" duplican datos si se repiten; usar vaciar y recargar, o `MERGE`.

## Pendiente (requiere decisión o permiso del propietario)

| Tema | Motivo |
|---|---|
| Conexión de `pl_gold_a_warehouse` (Copy Job) | Requiere iniciar sesión y conceder permisos OAuth. El pipeline no se guardó |
| Llamar a `dwh.sp_recargar_todo` desde el pipeline | Necesita una conexión al Warehouse (mismo permiso) |
| Programación diaria de `pl_olist_diario` | Crea una ejecución automática persistente; se activa solo con confirmación |
| Fase 9, Real-Time Intelligence (Eventstream + Eventhouse) | No se construyó |
| Fase 10, Git y Deployment Pipelines | Requiere un repositorio y credenciales del propietario |
| Seguridad (RLS, etiquetas de sensibilidad) | No configurado |

## Nota sobre costos y vigencia

El workspace usa una **prueba de Fabric**; al momento de este resumen quedaban **7 días**. Al vencer, los elementos dejan de ejecutarse hasta contar con capacidad.
