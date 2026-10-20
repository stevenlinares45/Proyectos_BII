-- Fase 5 · Carga idempotente Gold -> Warehouse, con controles y bitácora.
-- Cada bloque separado por "GO" se ejecuta como un lote independiente.

CREATE TABLE dwh.control_cargas (
    fecha_carga   DATETIME2(6)  NOT NULL,
    tabla         VARCHAR(100)  NOT NULL,
    filas_origen  BIGINT        NULL,
    filas_destino BIGINT        NULL,
    estado        VARCHAR(20)   NOT NULL,
    mensaje       VARCHAR(500)  NULL,
    duracion_seg  INT           NULL
)
GO
CREATE PROCEDURE dwh.sp_recargar_tabla @tabla VARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;

    -- Control 1: solo tablas permitidas (evita inyección SQL en el SQL dinámico).
    IF @tabla NOT IN ('dim_fecha','dim_cliente','dim_producto','dim_vendedor',
                      'dim_pedido','fact_ventas','fact_pagos','fact_resenas')
        THROW 50001, 'Tabla no permitida para recarga', 1;

    DECLARE @sql NVARCHAR(MAX), @origen BIGINT, @destino BIGINT,
            @inicio DATETIME2(6) = SYSDATETIME(), @msg VARCHAR(500);

    BEGIN TRY
        -- Control 2: filas esperadas en el origen (Lakehouse Gold).
        SET @sql = N'SELECT @n = COUNT_BIG(*) FROM lh_olist.gold.' + QUOTENAME(@tabla);
        EXEC sp_executesql @sql, N'@n BIGINT OUTPUT', @n = @origen OUTPUT;

        BEGIN TRAN;
            -- Idempotencia: vaciar y recargar, nunca anexar.
            SET @sql = N'TRUNCATE TABLE dwh.' + QUOTENAME(@tabla);
            EXEC (@sql);
            SET @sql = N'INSERT INTO dwh.' + QUOTENAME(@tabla)
                     + N' SELECT * FROM lh_olist.gold.' + QUOTENAME(@tabla);
            EXEC (@sql);
            SET @sql = N'SELECT @n = COUNT_BIG(*) FROM dwh.' + QUOTENAME(@tabla);
            EXEC sp_executesql @sql, N'@n BIGINT OUTPUT', @n = @destino OUTPUT;

            -- Control 3: si no cuadran los conteos, se deshace todo (ROLLBACK).
            IF @origen <> @destino
                THROW 50002, 'El conteo de filas no coincide con el origen', 1;
        COMMIT;

        INSERT INTO dwh.control_cargas
        VALUES (@inicio, @tabla, @origen, @destino, 'OK', NULL,
                DATEDIFF(SECOND, @inicio, SYSDATETIME()));
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK;
        SET @msg = LEFT(ERROR_MESSAGE(), 500);
        INSERT INTO dwh.control_cargas
        VALUES (@inicio, @tabla, @origen, @destino, 'ERROR', @msg,
                DATEDIFF(SECOND, @inicio, SYSDATETIME()));
        THROW;
    END CATCH
END
GO
CREATE PROCEDURE dwh.sp_recargar_todo
AS
BEGIN
    EXEC dwh.sp_recargar_tabla 'dim_fecha';
    EXEC dwh.sp_recargar_tabla 'dim_cliente';
    EXEC dwh.sp_recargar_tabla 'dim_producto';
    EXEC dwh.sp_recargar_tabla 'dim_vendedor';
    EXEC dwh.sp_recargar_tabla 'dim_pedido';
    EXEC dwh.sp_recargar_tabla 'fact_ventas';
    EXEC dwh.sp_recargar_tabla 'fact_pagos';
    EXEC dwh.sp_recargar_tabla 'fact_resenas';
END
