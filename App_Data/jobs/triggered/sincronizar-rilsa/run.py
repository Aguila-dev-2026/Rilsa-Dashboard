"""Punto de entrada del WebJob programado de Azure App Service."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[4]
os.chdir(RAIZ_PROYECTO)
sys.path.insert(0, str(RAIZ_PROYECTO))
runpy.run_path(str(RAIZ_PROYECTO / "sincronizar_nube.py"), run_name="__main__")
