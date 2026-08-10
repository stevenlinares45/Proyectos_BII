# Generador de Estructura Estándar de Proyectos — Python

**Tipo:** herramienta interna de productividad (no es un caso de cliente — sin datos ni información de terceros)
**Rol:** diseño y desarrollo completo

## Contexto y problema

Manejo varios proyectos de datos en paralelo (BigQuery + Power BI), cada uno para un cliente distinto. Sin una convención fija, cada proyecto terminaba organizado a criterio del momento: un `.pbix` viejo mezclado con el `.pbip` vigente, documentación repartida entre `docs/`, `Documentacion/` y `Mockups/` según el día, y retomar un proyecto de hace tres meses implicaba primero entender *dónde había quedado cada cosa* antes de poder trabajar.

## Qué hace

Un script en Python crea, en segundos, la misma estructura de carpetas para cualquier proyecto nuevo — sin depender de copiar y pegar una plantilla a mano:

```
<proyecto>/
├── .gitignore
├── README.md
├── 00_Backup/       Versiones anteriores, .pbix, artefactos legacy (solo lectura)
│   └── Versiones_Anteriores/
├── 01_Docs/         Requerimientos, mapa de fases, modelo de datos, mockups
│   ├── 01_Proyecto.md
│   ├── 02_Mapa_y_Plan.md
│   └── 03_Modelo_Datos.md
├── 02_BigQuery/     Scripts SQL — bronze → silver → gold
└── 03_PowerBI/      Proyecto Power BI (PBIP) — Report + SemanticModel
```

Una regla fija evita el error más común: **los `.pbix` nunca viven en `03_PowerBI/`** — esa carpeta es solo el PBIP versionable; cualquier `.pbix` (export binario) va a `00_Backup/Versiones_Anteriores/`.

## Interfaz

Dos formas de uso, según el contexto:

**Asistente interactivo** (`Crear Proyecto Nuevo.bat`, doble clic, sin terminal): pregunta cliente, carpeta destino, nombre del proyecto y área. Si ya existen proyectos para ese cliente, detecta la carpeta y sugiere el siguiente número automáticamente (`01_`, `02_`, `03_`...).

**Línea de comandos** (para automatizar):
```bash
python nuevo_proyecto.py --nombre "01_Analisis_Ventas" --cliente "Cliente X" --area "Comercial"
```

## Técnicas destacadas

- **Escritura explícita en UTF-8** en cada archivo generado — evita la corrupción de tildes (`Ã¡` en vez de `á`) típica de la code page por defecto de la consola de Windows al mezclar `Get-Content`/`Set-Content` sin especificar codificación.
- **Sanitización de entrada** contra caracteres invisibles (BOM `U+FEFF`) que a veces inyecta la consola según la code page activa, para que el nombre del cliente quede siempre limpio en el `README.md` generado.
- **Ruta base portable**: se calcula relativa a la ubicación del propio script (`Path(__file__).resolve().parent`), no depende del usuario ni de la máquina donde se ejecute.
- **Idempotente por diseño**: si el proyecto destino ya existe, no sobreescribe nada — falla con un mensaje claro en vez de arriesgar datos.

## Stack técnico
`Python 3` (estándar, sin dependencias externas) · `Batch script` (lanzador para Windows)

## Resultado
Un proyecto nuevo queda con la estructura completa y documentación base en segundos, siempre igual sin importar el cliente — elimina la deriva de organización ad-hoc que antes hacía que retomar un proyecto viejo costara más tiempo que avanzar uno nuevo.
