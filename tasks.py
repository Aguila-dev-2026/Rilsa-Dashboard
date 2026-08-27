"""Atajos de desarrollo para el dashboard de Planta RILES.

Ejecuta desde la raíz del repositorio:
    python tasks.py dev
    python tasks.py actualizar
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent


def ejecutar(comando: list[str], variables: dict[str, str] | None = None) -> None:
    """Ejecuta un comando con el mismo intérprete del entorno virtual activo."""
    entorno = os.environ.copy()
    entorno.update(variables or {})
    subprocess.run(comando, cwd=RAIZ_PROYECTO, env=entorno, check=True)


def tarea_dev() -> None:
    ejecutar(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            "--server.runOnSave",
            "true",
        ],
        {"RILSA_APP_ENV": "local"},
    )


def tarea_dev_nube() -> None:
    ejecutar(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            "--server.runOnSave",
            "true",
        ],
        {"RILSA_APP_ENV": "cloud"},
    )


def tarea_actualizar() -> None:
    from actualizar_datos import actualizar_datos

    resultado = actualizar_datos()
    if resultado["estado"] == "sin_cambios":
        print(f"Las planillas no cambiaron. Se conservan {resultado['registros']:,} registros.")
        return

    print(f"Datos actualizados: {resultado['registros']:,} registros.")
    for area, registros in resultado["areas"].items():
        print(f"- {area}: {registros:,}")


def tarea_importar_fisico() -> None:
    ejecutar([sys.executable, "importar.py"])


def tarea_importar_aerobico() -> None:
    ejecutar([sys.executable, "importar_analisis_aerobico.py"])


def tarea_instalar() -> None:
    ejecutar([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def tarea_sincronizar_nube() -> None:
    ejecutar(
        [sys.executable, "sincronizar_nube.py"],
        {"RILSA_APP_ENV": "cloud"},
    )


def tarea_validar_configuracion() -> None:
    from funciones.configuracion import obtener_configuracion

    configuracion = obtener_configuracion()
    print(f"Entorno activo: {configuracion.entorno}")
    if not configuracion.es_nube:
        print("Configuración local lista: SQLite y planillas de datos/.")
        return

    faltantes = (
        configuracion.faltantes_base_datos()
        + configuracion.faltantes_sharepoint()
    )
    if faltantes:
        print("Configuración de nube incompleta:")
        for nombre in faltantes:
            print(f"- {nombre}")
        raise SystemExit(1)
    print("Configuración de nube completa.")


def tarea_comprobar() -> None:
    ejecutar([sys.executable, "-m", "compileall", "-q", "."])
    ejecutar([sys.executable, "-m", "unittest", "discover", "-s", "tests"])


TAREAS = {
    "dev": tarea_dev,
    "dev-nube": tarea_dev_nube,
    "actualizar": tarea_actualizar,
    "importar-fisico": tarea_importar_fisico,
    "importar-aerobico": tarea_importar_aerobico,
    "instalar": tarea_instalar,
    "sincronizar-nube": tarea_sincronizar_nube,
    "validar-config": tarea_validar_configuracion,
    "comprobar": tarea_comprobar,
}


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Atajos de desarrollo para el dashboard Planta RILES."
    )
    parser.add_argument("tarea", choices=TAREAS, help="Tarea que deseas ejecutar.")
    return parser.parse_args()


if __name__ == "__main__":
    opciones = argumentos()
    TAREAS[opciones.tarea]()
