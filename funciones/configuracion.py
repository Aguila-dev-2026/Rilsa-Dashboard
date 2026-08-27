"""Configuración central para ejecución local y despliegue en Azure.

El modo local es siempre el valor predeterminado. El modo nube se activa de
forma explícita con ``RILSA_APP_ENV=cloud`` para evitar que una prueba local
use por accidente recursos de producción.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _es_verdadero(valor: str | None) -> bool:
    return (valor or "").strip().casefold() in {"1", "true", "yes", "si", "sí", "on"}


def _normalizar_database_url(valor: str | None) -> str | None:
    url = (valor or "").strip()
    if not url:
        return None
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


@dataclass(frozen=True)
class Configuracion:
    entorno: str
    database_url: str | None
    sincronizacion_manual: bool
    tenant_id: str | None
    client_id: str | None
    client_secret: str | None
    sharepoint_drive_id: str | None
    sharepoint_fisico_item_id: str | None
    sharepoint_aerobico_item_id: str | None

    @property
    def es_nube(self) -> bool:
        return self.entorno == "cloud"

    @property
    def usa_postgres(self) -> bool:
        return self.es_nube and bool(self.database_url)

    def faltantes_base_datos(self) -> list[str]:
        return [] if self.database_url else ["DATABASE_URL"]

    def faltantes_sharepoint(self) -> list[str]:
        valores = {
            "AZURE_TENANT_ID": self.tenant_id,
            "AZURE_CLIENT_ID": self.client_id,
            "AZURE_CLIENT_SECRET": self.client_secret,
            "SHAREPOINT_DRIVE_ID": self.sharepoint_drive_id,
            "SHAREPOINT_FISICO_ITEM_ID": self.sharepoint_fisico_item_id,
            "SHAREPOINT_AEROBICO_ITEM_ID": self.sharepoint_aerobico_item_id,
        }
        return [nombre for nombre, valor in valores.items() if not valor]


@lru_cache(maxsize=1)
def obtener_configuracion() -> Configuracion:
    entorno = os.getenv("RILSA_APP_ENV", "local").strip().casefold()
    if entorno not in {"local", "cloud"}:
        raise ValueError("RILSA_APP_ENV debe ser 'local' o 'cloud'.")

    def variable(nombre: str) -> str | None:
        valor = os.getenv(nombre, "").strip()
        return valor or None

    return Configuracion(
        entorno=entorno,
        database_url=_normalizar_database_url(variable("DATABASE_URL")),
        sincronizacion_manual=_es_verdadero(
            variable("RILSA_ENABLE_MANUAL_SYNC")
        ),
        tenant_id=variable("AZURE_TENANT_ID"),
        client_id=variable("AZURE_CLIENT_ID"),
        client_secret=variable("AZURE_CLIENT_SECRET"),
        sharepoint_drive_id=variable("SHAREPOINT_DRIVE_ID"),
        sharepoint_fisico_item_id=variable("SHAREPOINT_FISICO_ITEM_ID"),
        sharepoint_aerobico_item_id=variable("SHAREPOINT_AEROBICO_ITEM_ID"),
    )


def limpiar_cache_configuracion() -> None:
    """Permite cambiar variables de entorno dentro de pruebas automatizadas."""
    obtener_configuracion.cache_clear()
