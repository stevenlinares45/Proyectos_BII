#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crea un proyecto nuevo con la estructura estandar:

    <proyecto>/
    |-- .gitignore
    |-- README.md
    |-- 00_Backup/       Versiones anteriores, .pbix, artefactos legacy
    |   `-- Versiones_Anteriores/
    |-- 01_Docs/         Documentacion, mockups, plan de fases
    |   |-- 01_Proyecto.md
    |   |-- 02_Mapa_y_Plan.md
    |   |-- 03_Modelo_Datos.md
    |   `-- Documentacion/
    |-- 02_BigQuery/     Scripts SQL, datos fuente, validaciones
    `-- 03_PowerBI/      Proyecto Power BI (PBIP) -- Report + SemanticModel

Sirve para cualquier compania: solo cambia --cliente y --destino. No depende
de ninguna plantilla externa: todo el contenido vive en este mismo archivo.

Ejemplos
--------
    # Un proyecto para un cliente, en su propia carpeta de compania
    python nuevo_proyecto.py --nombre "01_Analisis_Ventas" --cliente "Cliente X" --area "Comercial" --destino "C:\\Proyectos\\Proyectos_ClienteX"

    # Otro proyecto dentro de esa misma carpeta de compania
    python nuevo_proyecto.py --nombre "02_Logistica" --cliente "Cliente X" --destino "C:\\Proyectos\\Proyectos_ClienteX"

    # Si no se indica --destino, se crea junto a este script
    python nuevo_proyecto.py --nombre "01_Piloto" --cliente "Otra Empresa"
"""

from __future__ import annotations
import argparse
import sys
from datetime import date
from pathlib import Path

README_TEMPLATE = """# {nombre} — BigQuery + Power BI

**Cliente:** {cliente} · **Área:** {area} · **Inicio:** {fecha}
**Fuente:** <sistema origen>
**Datos:** BigQuery · **Analítica:** Power BI

## Qué hace este proyecto

<Una o dos frases: qué reemplaza o resuelve, y para quién.>

## Estado actual: **Fase 1 · <nombre de la fase>**

## Estructura

```
{nombre}/
├── 00_Backup/      Proyecto anterior / versiones previas (solo lectura)
├── 01_Docs/        Requerimientos, mapa, plan, mockups y diseño
├── 02_BigQuery/    Scripts SQL — vistas, dimensiones, hechos (bronze → silver → gold)
└── 03_PowerBI/     Proyecto Power BI (PBIP) — Report + SemanticModel
```

## Por dónde empezar

| Si necesitás… | Andá a |
|---|---|
| Alcance, fuentes, KPIs y bloqueantes | [01_Docs/01_Proyecto.md](01_Docs/01_Proyecto.md) |
| Plan de trabajo por fases | [01_Docs/02_Mapa_y_Plan.md](01_Docs/02_Mapa_y_Plan.md) |
| Diseño del modelo de datos | [01_Docs/03_Modelo_Datos.md](01_Docs/03_Modelo_Datos.md) |

## Ambientes

| Ambiente | Proyecto GCP | Datasets |
|---|---|---|
| dev | `<cliente>-<proyecto>-dev` | `<prefijo>_bronze`, `<prefijo>_silver`, `<prefijo>_gold` |
| prd | `<cliente>-<proyecto>-prd` | `<prefijo>_bronze`, `<prefijo>_silver`, `<prefijo>_gold` |

## Reglas de trabajo

- No se commitean datos ni credenciales.
- Un archivo SQL = una responsabilidad = una tarea del orquestador.
- No se avanza de fase sin el entregable de la anterior.
- Los `.pbix` no viven en `03_PowerBI/` (esa carpeta es solo PBIP, versionable). Cualquier `.pbix` va a `00_Backup/Versiones_Anteriores/`.
- Toda decisión técnica no obvia se registra en `01_Docs/03_Modelo_Datos.md` §Decisiones.
"""

GITIGNORE_TEMPLATE = """# === Datos: nunca al repositorio ===
*.csv
*.xlsx
*.xls
*.parquet
*.json.gz

# === Power BI ===
*.pbix
**/.pbi/localSettings.json
**/.pbi/cache.abf
*.pbip.bak

# === Backup (historico pesado, se conserva fuera del repositorio) ===
00_Backup/PowerBI_Legacy/*.pbix
00_Backup/Datos_Origen_Historicos/
00_Backup/Versiones_Anteriores/

# === Credenciales y configuracion local ===
.env
.env.*
!.env.example
*-key.json
*credentials*.json
service-account*.json
.claude/settings.local.json

# === Python ===
__pycache__/
*.pyc
.venv/
venv/
.ipynb_checkpoints/

# === Salidas de ejecucion ===
logs/
*.log

# === Sistema ===
Thumbs.db
desktop.ini
.DS_Store
~$*
"""

README_BACKUP_TEMPLATE = """# 00_Backup — Activos previos congelados

**Fecha de congelamiento:** {fecha}

Esta carpeta conserva el estado del proyecto anterior tal como estaba antes
del rediseno. **No se modifica nada aqui.** Sirve como referencia de negocio
y como plan de vuelta atras mientras el nuevo tablero no este validado.

## Contenido

| Carpeta | Que contiene | Para que se consulta |
|---|---|---|
| `PowerBI_Legacy/` | Proyecto Power BI anterior completo (.pbip/.pbix/.Report/.SemanticModel) | Extraer definiciones DAX, relaciones y diseno previos |
| `Datos_Origen_Historicos/` | Exports crudos previos a la migracion | Perfilado y reconciliacion contra el tablero viejo |
| `Versiones_Anteriores/` | Copias `.pbix` fuera de uso (todo `.pbix` vive aqui, nunca en `03_PowerBI/`) | Comparar evolucion del modelo |
| `Documentacion_Previa/` | Documentacion heredada | Contexto historico |
"""

DOC_01_PROYECTO = """# 01 · Proyecto — Alcance, fuentes y KPIs

## Alcance
<Que incluye y que explicitamente no incluye este proyecto.>

## Fuentes de datos
| Fuente | Sistema | Proyecto/Dataset GCP | Contacto |
|---|---|---|---|

## KPIs objetivo
| KPI | Definicion | Fuente |
|---|---|---|

## Bloqueantes
| ID | Descripcion | Estado |
|---|---|---|
| B-01 | | abierto |
"""

DOC_02_MAPA = """# 02 · Mapa y Plan de trabajo por fases

| Fase | Entregable | Estado |
|---|---|---|
| 1 · Analisis del estado actual | | |
| 2 · Diseno del modelo BigQuery | | |
| 3 · Construccion SQL (bronze -> silver -> gold) | | |
| 4 · Modelo dimensional / semantico | | |
| 5 · Construccion Power BI | | |
| 6 · Validacion contra el sistema anterior | | |
| 7 · Publicacion y entrega | | |
"""

DOC_03_MODELO = """# 03 · Modelo de Datos

## Modelo dimensional propuesto
<Tablas de hechos y dimensiones, grano de cada una.>

## Decisiones
| Fecha | Decision | Por que |
|---|---|---|
"""


def write_utf8(path: Path, content: str) -> None:
    """Escribe siempre en UTF-8 explicito (evita mojibake con tildes en Windows)."""
    path.write_text(content, encoding="utf-8", newline="\n")


def crear_proyecto(nombre: str, cliente: str, area: str, destino: Path) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    proyecto = destino / nombre
    if proyecto.exists():
        raise FileExistsError(f"Ya existe un proyecto en: {proyecto}")

    fecha = date.today().isoformat()
    area_txt = area if area else "(sin definir)"

    # --- estructura de carpetas ---
    (proyecto / "00_Backup" / "Versiones_Anteriores").mkdir(parents=True)
    (proyecto / "01_Docs" / "Documentacion").mkdir(parents=True)
    (proyecto / "02_BigQuery").mkdir(parents=True)
    (proyecto / "03_PowerBI").mkdir(parents=True)

    # .gitkeep en carpetas vacias, para que Git (si algun dia se usa) las conserve
    (proyecto / "00_Backup" / "Versiones_Anteriores" / ".gitkeep").touch()
    (proyecto / "01_Docs" / "Documentacion" / ".gitkeep").touch()
    (proyecto / "02_BigQuery" / ".gitkeep").touch()
    (proyecto / "03_PowerBI" / ".gitkeep").touch()

    # --- archivos de contenido ---
    write_utf8(proyecto / "README.md", README_TEMPLATE.format(nombre=nombre, cliente=cliente, area=area_txt, fecha=fecha))
    write_utf8(proyecto / ".gitignore", GITIGNORE_TEMPLATE)
    write_utf8(proyecto / "00_Backup" / "README_BACKUP.md", README_BACKUP_TEMPLATE.format(fecha=fecha))
    write_utf8(proyecto / "01_Docs" / "01_Proyecto.md", DOC_01_PROYECTO)
    write_utf8(proyecto / "01_Docs" / "02_Mapa_y_Plan.md", DOC_02_MAPA)
    write_utf8(proyecto / "01_Docs" / "03_Modelo_Datos.md", DOC_03_MODELO)

    return proyecto


# Carpeta base donde viven todas las familias "Proyectos_<Compania>".
# Por defecto, la carpeta que contiene a esta (portable: no depende del usuario ni de la maquina).
# Si preferis una ruta fija, reemplaza la linea de abajo por, por ejemplo:
#     BASE_DIR = Path(r"C:\Users\TU_USUARIO\Documents\Claude")
BASE_DIR = Path(__file__).resolve().parent.parent


def slug_compania(cliente: str) -> str:
    """'Cliente X' -> 'Cliente_X', 'Banco de Bogota' -> 'Banco_De_Bogota' (para nombre de carpeta)."""
    limpio = "".join(c if c.isalnum() or c.isspace() else "" for c in cliente)
    return "_".join(p.capitalize() for p in limpio.split())


def reportar(proyecto: Path, cliente: str) -> None:
    print(f"\nProyecto creado: {proyecto}")
    print(f"Cliente: {cliente}")
    print("\nEstructura:")
    for item in sorted(proyecto.iterdir()):
        print(f"  {item.name}")
    print("\nSiguientes pasos:")
    print("  1. Revisar README.md (fuente de datos, fase 1)")
    print("  2. Completar 01_Docs/01_Proyecto.md, 02_Mapa_y_Plan.md, 03_Modelo_Datos.md")
    print("  3. Los .pbix SIEMPRE van a 00_Backup/Versiones_Anteriores, nunca a 03_PowerBI")
    print("  4. No se sube nada a git salvo que lo pidas explicitamente")


def pedir(prompt: str) -> str:
    """input() blindado: quita espacios y caracteres invisibles (BOM, etc.)
    que a veces mete la consola de Windows segun la codepage activa."""
    return input(prompt).strip().strip("﻿​")


def modo_interactivo() -> None:
    """Se activa al correr el script sin argumentos (ej. boton Run de VS Code)."""
    print("=== Crear proyecto nuevo ===\n")

    cliente = pedir("Cliente / compania (ej. Cliente X): ")
    while not cliente:
        cliente = pedir("El cliente no puede quedar vacio. Cliente / compania: ")

    carpeta_compania = f"Proyectos_{slug_compania(cliente)}"
    destino_sugerido = BASE_DIR / carpeta_compania
    destino_in = pedir(f"Carpeta destino [Enter = {destino_sugerido}]: ")
    destino = Path(destino_in).expanduser().resolve() if destino_in else destino_sugerido

    existentes = sorted(p.name for p in destino.glob("*") if p.is_dir()) if destino.exists() else []
    if existentes:
        print(f"\nProyectos que ya existen en {destino}:")
        for n in existentes:
            print(f"  - {n}")
        siguiente = 1
        for n in existentes:
            prefijo = n.split("_")[0]
            if prefijo.isdigit():
                siguiente = max(siguiente, int(prefijo) + 1)
        sugerido_nombre = f"{siguiente:02d}_"
    else:
        sugerido_nombre = "01_"

    nombre = pedir(f"Nombre del proyecto (ej. {sugerido_nombre}Marketplace_Ventas): ")
    while not nombre:
        nombre = pedir("El nombre no puede quedar vacio. Nombre del proyecto: ")

    area = pedir("Area o equipo (opcional, Enter para omitir): ")

    print(f"\nSe va a crear:  {destino / nombre}")
    confirmar = pedir("Confirmar? [S/n]: ").lower()
    if confirmar not in ("", "s", "si", "y", "yes"):
        print("Cancelado.")
        return

    try:
        proyecto = crear_proyecto(nombre, cliente, area, destino)
    except FileExistsError as e:
        print(f"\nERROR: {e}")
        return

    reportar(proyecto, cliente)


def modo_cli() -> None:
    """Modo por linea de comandos, para terminal o para automatizar."""
    parser = argparse.ArgumentParser(description="Crea un proyecto de datos con la estructura estandar (00_Backup/01_Docs/02_BigQuery/03_PowerBI).")
    parser.add_argument("--nombre", required=True, help='Nombre de la carpeta del proyecto, ej. "01_Marketplace_Ventas"')
    parser.add_argument("--cliente", required=True, help='Nombre del cliente/compania, ej. "Cliente X"')
    parser.add_argument("--area", default="", help='Area o equipo dentro del cliente (opcional)')
    parser.add_argument("--destino", default=None, help="Carpeta donde se crea el proyecto (por defecto Proyectos_<Cliente> junto a BASE_DIR)")
    args = parser.parse_args()

    destino = Path(args.destino).expanduser().resolve() if args.destino else BASE_DIR / f"Proyectos_{slug_compania(args.cliente)}"

    try:
        proyecto = crear_proyecto(args.nombre, args.cliente, args.area, destino)
    except FileExistsError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    reportar(proyecto, args.cliente)


def main() -> None:
    # Sin argumentos (ej. boton "Run Python File" en VS Code) -> asistente interactivo.
    # Con argumentos (--nombre --cliente ...) -> modo terminal/script.
    if len(sys.argv) == 1:
        modo_interactivo()
    else:
        modo_cli()


if __name__ == "__main__":
    main()
