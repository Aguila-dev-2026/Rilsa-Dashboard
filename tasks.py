"""Atajos de desarrollo para el dashboard de Planta RILES.

Ejecuta desde la raíz del repositorio:
    python tasks.py dev
    python tasks.py actualizar
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent


def ejecutar(comando: list[str]) -> None:
    """Ejecuta un comando con el mismo intérprete del entorno virtual activo."""
    subprocess.run(comando, cwd=RAIZ_PROYECTO, check=True)


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
        ]
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


TAREAS = {
    "dev": tarea_dev,
    "actualizar": tarea_actualizar,
    "importar-fisico": tarea_importar_fisico,
    "importar-aerobico": tarea_importar_aerobico,
    "instalar": tarea_instalar,
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
