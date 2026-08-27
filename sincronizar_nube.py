"""Sincroniza SharePoint con PostgreSQL para el despliegue multiusuario."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from actualizar_datos import huella_archivo, preparar_datos, validar_datos
from funciones.configuracion import obtener_configuracion
from funciones.postgres import (
    base_vigente_y_sin_cambios,
    conteos_por_area,
    reemplazar_mediciones,
)
from funciones.sharepoint import descargar_planillas_sharepoint
from importar import importar_fisico_quimico
from importar_analisis_aerobico import importar_analisis_aerobico


def sincronizar_datos_nube() -> dict:
    configuracion = obtener_configuracion()
    if not configuracion.es_nube:
        raise RuntimeError(
            "La sincronización remota requiere RILSA_APP_ENV=cloud."
        )
    faltantes = (
        configuracion.faltantes_base_datos()
        + configuracion.faltantes_sharepoint()
    )
    if faltantes:
        raise RuntimeError("Faltan variables de nube: " + ", ".join(faltantes))

    with TemporaryDirectory(prefix="rilsa-sharepoint-") as temporal:
        carpeta = Path(temporal)
        entrada_fisico, entrada_aerobico = descargar_planillas_sharepoint(
            carpeta / "entradas",
            configuracion,
        )
        huellas = [huella_archivo(entrada_fisico), huella_archivo(entrada_aerobico)]
        if base_vigente_y_sin_cambios(configuracion.database_url, huellas):
            registros = sum(conteos_por_area(configuracion.database_url).values())
            return {"estado": "sin_cambios", "registros": registros}

        carpeta_salida = carpeta / "generados"
        fisico = importar_fisico_quimico(
            entrada_fisico,
            carpeta_salida / "fisico_quimico.xlsx",
        )
        aerobico = importar_analisis_aerobico(
            entrada_aerobico,
            carpeta_salida / "analisis_planta_aerobica.xlsx",
        )
        datos = preparar_datos(fisico, aerobico)
        validar_datos(datos, conteos_por_area(configuracion.database_url))
        reemplazar_mediciones(configuracion.database_url, datos, huellas)

    return {
        "estado": "actualizado",
        "registros": len(datos),
        "areas": datos.groupby("Area").size().to_dict(),
    }


if __name__ == "__main__":
    resultado = sincronizar_datos_nube()
    if resultado["estado"] == "sin_cambios":
        print(
            "Las planillas de SharePoint no cambiaron. "
            f"Se conservan {resultado['registros']:,} registros."
        )
    else:
        print(f"PostgreSQL actualizado: {resultado['registros']:,} registros.")
