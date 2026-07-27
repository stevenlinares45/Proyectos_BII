# Data Hub de Abastecimiento y Compras — Power BI

**Sector del cliente:** Corporativo — área de Compras y Abastecimiento
**Rol:** Levantamiento de requerimientos, modelado de datos, desarrollo del reporte

> ℹ️ Proyecto real para un cliente corporativo. Nombres de cliente, proveedores y cifras de compras **no se muestran** por confidencialidad — este caso de estudio describe el alcance y enfoque del proyecto.

## Contexto y problema

El área de Abastecimiento y Compras no tenía un punto único de consulta para el ciclo de solicitudes y órdenes de compra: la información vivía repartida entre distintos sistemas y hojas de cálculo, dificultando el seguimiento del estado de cada solicitud y el análisis de gasto por categoría/proveedor.

## Enfoque

1. **Levantamiento de necesidades** con el área de negocio: se documentaron los procesos de solicitud → aprobación → orden de compra, y los indicadores que gerencia necesitaba monitorear.
2. **Prototipado en HTML** de la experiencia del data hub antes de construir el modelo definitivo en Power BI, para validar con el usuario de negocio la navegación y las vistas clave sin comprometer tiempo de desarrollo del modelo.
3. **Modelo de datos** consolidando el ciclo completo de solicitudes y órdenes en un esquema analizable por proveedor, categoría y estado.

## Stack técnico
`Power BI (PBIP)` · `Modelado dimensional` · `Prototipado funcional (HTML)` · `Levantamiento de requerimientos`

## Resultado
Data hub único para el seguimiento del ciclo de compras, con vistas de estado de solicitudes/órdenes y análisis de gasto, reemplazando el seguimiento manual disperso entre archivos.
