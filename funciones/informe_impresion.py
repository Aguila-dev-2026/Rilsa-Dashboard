"""Vista HTML completa que se activa únicamente al usar Print del navegador."""

from __future__ import annotations

from html import escape

import pandas as pd


def _texto(valor) -> str:
    if pd.isna(valor) or valor is None:
        return "-"
    return escape(str(valor).strip() or "-")


def _numero(valor) -> str:
    return "-" if pd.isna(valor) else f"{float(valor):,.2f}"


def _grafico_svg(datos: pd.DataFrame) -> str:
    serie = datos[["Fecha", "Valor"]].dropna().sort_values("Fecha")
    if len(serie) > 80:
        serie = serie.iloc[:: max(1, len(serie) // 80)]
    valores = serie["Valor"].astype(float).tolist()
    if not valores:
        return "<p>Sin valores numéricos para el gráfico.</p>"
    minimo, maximo = min(valores), max(valores)
    rango = max(maximo - minimo, 1)
    puntos = []
    for indice, valor in enumerate(valores):
        x = 8 + (indice * 584 / max(len(valores) - 1, 1))
        y = 112 - ((valor - minimo) / rango * 96)
        puntos.append(f"{x:.1f},{y:.1f}")
    return (
        '<svg viewBox="0 0 600 130" role="img" aria-label="Evolución del parámetro">'
        '<line x1="8" y1="112" x2="592" y2="112" class="eje"/>'
        '<polyline fill="none" points="' + " ".join(puntos) + '" class="serie"/>'
        f'<text x="8" y="126">{escape(serie["Fecha"].iloc[0].strftime("%d/%m/%Y"))}</text>'
        f'<text x="510" y="126">{escape(serie["Fecha"].iloc[-1].strftime("%d/%m/%Y"))}</text>'
        "</svg>"
    )


def generar_informe_impresion(datos: pd.DataFrame) -> str:
    """Devuelve HTML con todas las mediciones para el Print nativo de Streamlit."""
    datos = datos.copy()
    for columna in ("Punto", "Turno", "TipoDato", "Calificador", "Fuente", "Hoja"):
        if columna not in datos:
            datos[columna] = ""
    datos["Fecha"] = pd.to_datetime(datos["Fecha"], errors="coerce")
    datos["Valor"] = pd.to_numeric(datos["Valor"], errors="coerce")
    datos = datos.dropna(subset=["Fecha", "Valor", "Area", "Parametro"])
    if datos.empty:
        return ""

    partes = [
        "<style>"
        ".riles-print-report{display:none}.riles-print-report table{width:100%;border-collapse:collapse;font-size:8pt}.riles-print-report th{background:#6d1f2b;color:#fff}.riles-print-report th,.riles-print-report td{border:1px solid #ddd5ca;padding:4px;text-align:left}.riles-print-report tr:nth-child(even){background:#f4f0e9}.riles-print-report .ficha{max-width:680px}.riles-print-report .bloque{break-inside:avoid;margin:16px 0 25px}.riles-print-report svg{width:100%;max-width:600px;height:auto}.riles-print-report .serie{stroke:#6d1f2b;stroke-width:2}.riles-print-report .eje{stroke:#756e67;stroke-width:.7}.riles-print-report svg text{font-size:8px;fill:#756e67}"
        "@media print{@page{size:auto;margin:14mm}html,body{background:#fff!important;color:#171514!important;color-scheme:light!important;-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}header,[data-testid='stSidebar'],[data-testid='stToolbar'],footer{display:none!important}.stElementContainer:not(:has(.riles-print-report)){display:none!important}.stElementContainer:has(.riles-print-report){display:block!important}.riles-print-report{display:block!important;background:#fff!important;color:#171514!important;font-family:Arial,sans-serif}.riles-print-report h1{color:#48121a!important;font-size:22pt}.riles-print-report h2{color:#6d1f2b!important;margin-top:22px}.riles-print-report h3{margin-bottom:6px}.riles-print-report .salto-area{break-before:page}.riles-print-report table{font-size:7pt;background:#fff!important}.riles-print-report thead{display:table-header-group}.riles-print-report tr{break-inside:avoid}}"
        "</style><section class='riles-print-report'><h1>Informe operacional completo</h1>"
        "<p>Generado para impresión desde el Dashboard Operacional Planta RILES. Incluye exactamente los datos del filtro activo al momento de imprimir.</p>"
        "<h2>Resumen por área</h2><table class='ficha'><thead><tr><th>Área</th><th>Registros</th><th>Parámetros</th><th>Desde</th><th>Hasta</th></tr></thead><tbody>"
    ]
    resumen = datos.groupby("Area").agg(Registros=("Valor", "size"), Parametros=("Parametro", "nunique"), Desde=("Fecha", "min"), Hasta=("Fecha", "max")).reset_index()
    for fila in resumen.itertuples(index=False):
        partes.append(f"<tr><td>{_texto(fila.Area)}</td><td>{fila.Registros}</td><td>{fila.Parametros}</td><td>{fila.Desde:%d/%m/%Y}</td><td>{fila.Hasta:%d/%m/%Y}</td></tr>")
    partes.append("</tbody></table>")

    area_anterior = None
    for (area, punto, parametro, unidad), grupo in datos.groupby(["Area", "Punto", "Parametro", "Unidad"], dropna=False, sort=True):
        if area != area_anterior:
            partes.append(f"<h2 class='salto-area'>Área: {_texto(area)}</h2>")
            area_anterior = area
        detalle = grupo.sort_values("Fecha", ascending=False)
        partes.append(f"<article class='bloque'><h3>{_texto(parametro)} · Punto: {_texto(punto)}</h3><p><b>Registros:</b> {len(detalle)} &nbsp; <b>Promedio:</b> {_numero(detalle['Valor'].mean())} {_texto(unidad)} &nbsp; <b>Mínimo:</b> {_numero(detalle['Valor'].min())} &nbsp; <b>Máximo:</b> {_numero(detalle['Valor'].max())}</p>{_grafico_svg(detalle)}<table><thead><tr><th>Fecha</th><th>Turno</th><th>Tipo</th><th>Valor</th><th>Unidad</th><th>Cal.</th><th>Fuente</th><th>Hoja</th></tr></thead><tbody>")
        for fila in detalle.itertuples(index=False):
            partes.append(f"<tr><td>{fila.Fecha:%d/%m/%Y}</td><td>{_texto(fila.Turno)}</td><td>{_texto(fila.TipoDato)}</td><td>{_numero(fila.Valor)}</td><td>{_texto(fila.Unidad)}</td><td>{_texto(fila.Calificador)}</td><td>{_texto(fila.Fuente)}</td><td>{_texto(fila.Hoja)}</td></tr>")
        partes.append("</tbody></table></article>")
    return "".join(partes) + "</section>"
