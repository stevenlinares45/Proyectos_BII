# Portafolio de Proyectos de Business Intelligence

Portafolio de proyectos reales de **Business Intelligence, modelado de datos y analítica**, desarrollados para clientes corporativos en sectores como servicios industriales/ambientales, alimentos y bebidas, y logística.

> 🔒 **Nota de confidencialidad:** todos los proyectos de este repositorio corresponden a trabajo real para clientes corporativos bajo relaciones de confidencialidad. Por esa razón, **los nombres de las empresas, cifras, datos operativos y capturas de pantalla reales no se publican**. Cada caso de estudio describe el problema de negocio, la arquitectura y las técnicas aplicadas, usando datos de ejemplo ficticios cuando se incluye código.

## Sobre este portafolio

Trabajo end-to-end en proyectos de BI: desde el levantamiento de requerimientos con el área de negocio, pasando por el modelado dimensional y la integración de fuentes (BigQuery, Google Sheets, CSV), hasta el desarrollo de medidas DAX y dashboards ejecutivos en Power BI — incluyendo auditoría y corrección de modelos existentes.

**Stack principal:** Power BI (PBIP/TMDL) · DAX · SQL · BigQuery · Power Query (M) · Modelado dimensional

## Proyectos

| # | Proyecto | Enfoque | Stack |
|---|---|---|---|
| 01 | [Modelo de Costos Unitarios](proyectos/01-modelo-costos-unitarios/) | Migración de lógica de negocio de SQL legacy a modelo semántico; asignación de overhead con DAX | Power BI · DAX · BigQuery |
| 02 | [Data Hub de Abastecimiento y Compras](proyectos/02-data-hub-abastecimiento-compras/) | Consolidación del ciclo de solicitudes/órdenes de compra | Power BI · Prototipado HTML |
| 03 | [Data Hub Financiero (LATAM)](proyectos/03-data-hub-financiero-latam/) | Auditoría de modelo DAX: convenciones de signo, medidas defensivas, validación cruzada | Power BI · DAX · BigQuery |
| 04 | [Panel de Gestión de Flota y Combustible](proyectos/04-panel-gestion-flota-combustible/) | Cálculo de huella de carbono (CO₂e, IPCC 2006) y reconciliación BigQuery ↔ Power BI | Power BI · DAX · SQL · BigQuery |
| 05 | [Tablero de Gestión de Activos y Servicio Técnico](proyectos/05-tablero-gestion-activos-mantenimiento/) | Consolidación analítica de un sistema de gestión de activos | Power BI |
| 06 | [Data Hub de Marketing](proyectos/06-data-hub-marketing/) | En fase de levantamiento de requerimientos | — |
| 07 | [Dashboard — Sector Alimentos y Bebidas](proyectos/07-dashboard-sector-alimentos/) | Reporte Power BI | Power BI |

## Recursos técnicos

- 📘 [Playbook Operativo de Ingeniería de Datos](playbook-operativo-v2.html) — guía de referencia personal (no un caso de cliente) con metodología de proyecto, estrategias de carga e idempotencia, SQL, Databricks, GCP/BigQuery y Microsoft Fabric.

## Cómo sigo alimentando este portafolio

Cada vez que cierro un proyecto nuevo, agrego una carpeta en `proyectos/` siguiendo esta plantilla mínima:

```markdown
# Nombre genérico del proyecto

**Sector del cliente:** ...
**Rol:** ...

> 🔒 Nota de confidencialidad (siempre presente)

## Contexto y problema
## Arquitectura (diagrama Mermaid si aplica)
## Técnicas destacadas (código genérico, sin datos/nombres reales)
## Stack técnico
## Resultado
```

**Checklist antes de publicar un proyecto nuevo:**
- [ ] ¿El nombre del cliente aparece en algún lado (texto, código, nombre de archivo)? → quitarlo.
- [ ] ¿Hay cifras reales (montos, volúmenes, conteos)? → reemplazar por ejemplos ficticios o quitar.
- [ ] ¿Hay nombres reales de tablas/esquemas/proyectos de BigQuery, servidores o sistemas internos? → reemplazarlos por nombres genéricos (`fact_x`, `dim_y`).
- [ ] ¿Las capturas de pantalla muestran datos reales? → no incluir, o recrear con datos ficticios.
- [ ] ¿El código (SQL/DAX/M) es una copia literal de un archivo real? → reescribirlo desde cero con nombres genéricos, no solo "limpiarlo".

## Contacto
_(agrega aquí tu LinkedIn / correo de contacto profesional)_
