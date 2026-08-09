# Generador de estructura estándar para proyectos de datos

**Rol:** diseño y desarrollo de la herramienta (uso personal, no es un caso de cliente)

Script de utilidad que crea, con un solo comando, la estructura de carpetas que uso en todos mis proyectos de BigQuery + Power BI. Nació de estandarizar manualmente 7 proyectos de un mismo cliente que habían crecido cada uno con su propia organización ad-hoc (`Exports/`, `Mockups/`, `Documentacion/`, `SQL/`, `Datos/`... cada uno distinto) — y de la necesidad de que el próximo proyecto naciera bien organizado desde el primer commit, sin repetir ese trabajo de orden a mano.

## Qué resuelve

Sin esto, cada proyecto nuevo arranca con una carpeta vacía y termina organizado a criterio del momento. Con el tiempo eso hace que:

- Un `.pbix` viejo y el `.pbip` vigente terminen mezclados en la misma carpeta.
- La documentación quede repartida entre `docs/`, `Documentacion/` y `Mockups/` según el día.
- Retomar un proyecto de hace 3 meses implique primero entender *dónde quedó cada cosa*, antes de poder trabajar.

El script fija una convención única y la aplica en segundos, para cualquier cliente:

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

## Cómo se usa

**Opción 1 — doble clic (sin terminal):**
`Crear Proyecto Nuevo.bat` abre un asistente por consola que pregunta cliente, carpeta destino, nombre del proyecto y área. Si ya existen proyectos para ese cliente, detecta la carpeta y sugiere el siguiente número automáticamente (`01_`, `02_`, `03_`...).

**Opción 2 — línea de comandos:**
```bash
python nuevo_proyecto.py --nombre "01_Analisis_Ventas" --cliente "Cliente X" --area "Comercial"
```

Sin `--destino`, arma solo `Proyectos_<Cliente>/` junto a la carpeta base (configurable en una sola línea al inicio del script — por defecto, portable: se calcula relativa a la ubicación del propio archivo, no depende del usuario ni de la máquina).

## Detalles técnicos

- **Sin dependencias externas** — únicamente librería estándar de Python (`argparse`, `pathlib`, `datetime`).
- **Escritura explícita en UTF-8** en cada archivo generado, para evitar la corrupción de tildes (`Ã¡` en vez de `á`) típica de la code page por defecto de la consola de Windows.
- **Idempotente por diseño**: si el proyecto destino ya existe, no sobreescribe nada — falla con un mensaje claro.

## Stack técnico
`Python 3` (estándar, sin dependencias) · `Batch script` (lanzador para Windows)
