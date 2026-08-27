"""Descarga segura de las planillas operacionales desde SharePoint."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

import requests
from azure.identity import ClientSecretCredential

from funciones.configuracion import Configuracion, obtener_configuracion

GRAPH_ROOT = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"


def _validar(configuracion: Configuracion) -> None:
    faltantes = configuracion.faltantes_sharepoint()
    if faltantes:
        raise RuntimeError(
            "Faltan variables para conectar SharePoint: " + ", ".join(faltantes)
        )


def _token(configuracion: Configuracion) -> str:
    _validar(configuracion)
    credencial = ClientSecretCredential(
        tenant_id=configuracion.tenant_id,
        client_id=configuracion.client_id,
        client_secret=configuracion.client_secret,
    )
    return credencial.get_token(GRAPH_SCOPE).token


def descargar_item(
    *,
    drive_id: str,
    item_id: str,
    destino: Path,
    token: str,
) -> Path:
    """Descarga un DriveItem y lo publica localmente de forma atómica."""
    drive_seguro = quote(drive_id, safe="")
    item_seguro = quote(item_id, safe="")
    url = f"{GRAPH_ROOT}/drives/{drive_seguro}/items/{item_seguro}/content"
    temporal = destino.with_suffix(destino.suffix + ".descarga")
    destino.parent.mkdir(parents=True, exist_ok=True)

    try:
        with requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=(15, 120),
            stream=True,
        ) as respuesta:
            respuesta.raise_for_status()
            with temporal.open("wb") as archivo:
                for bloque in respuesta.iter_content(chunk_size=1024 * 1024):
                    if bloque:
                        archivo.write(bloque)
        os.replace(temporal, destino)
    finally:
        temporal.unlink(missing_ok=True)

    return destino


def descargar_planillas_sharepoint(
    directorio: Path,
    configuracion: Configuracion | None = None,
) -> tuple[Path, Path]:
    configuracion = configuracion or obtener_configuracion()
    token = _token(configuracion)
    fisico = descargar_item(
        drive_id=configuracion.sharepoint_drive_id,
        item_id=configuracion.sharepoint_fisico_item_id,
        destino=directorio / "Planilla Procesos RILES.xlsx",
        token=token,
    )
    aerobico = descargar_item(
        drive_id=configuracion.sharepoint_drive_id,
        item_id=configuracion.sharepoint_aerobico_item_id,
        destino=directorio / "Análisis Planta Aeróbica.xlsx",
        token=token,
    )
    return fisico, aerobico
