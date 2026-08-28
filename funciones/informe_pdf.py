"""Generación de informes PDF completos para el dashboard operacional."""

from __future__ import annotations

from datetime import datetime
from html import escape
from io import BytesIO

import pandas as pd
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing, Line, String
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from funciones.ui.tema import (
    COBRE as COBRE_HEX,
    TINTA_PDF as TINTA_HEX,
    VINO as VINO_HEX,
    VINO_PROFUNDO as VINO_PROFUNDO_HEX,
)

VINO = HexColor(VINO_HEX)
VINO_PROFUNDO = HexColor(VINO_PROFUNDO_HEX)
COBRE = HexColor(COBRE_HEX)
TINTA = HexColor(TINTA_HEX)
GRIS = HexColor("#756E67")
PAPEL = HexColor("#F4F0E9")
LINEA = HexColor("#DDD5CA")
VERDE = HexColor("#2E6A4D")

COLUMNAS_DETALLE = (
    ("Fecha", "Fecha", 57),
    ("Turno", "Turno", 39),
    ("TipoDato", "Tipo", 54),
    ("Valor", "Valor", 55),
    ("Unidad", "Unidad", 42),
    ("Calificador", "Cal.", 34),
    ("Fuente", "Fuente", 110),
    ("Hoja", "Hoja", 94),
)


def _texto(valor) -> str:
    if pd.isna(valor) or valor is None:
        return "-"
    texto = str(valor).strip()
    return texto or "-"


def _numero(valor) -> str:
    if pd.isna(valor):
        return "-"
    return f"{float(valor):,.2f}".replace(",", " ")


def _fecha(valor) -> str:
    if pd.isna(valor):
        return "-"
    return pd.Timestamp(valor).strftime("%d/%m/%Y")


def _parrafo(texto: str, estilo: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(texto).replace("\n", "<br/>"), estilo)


def _estilos() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "InformeTitulo",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            textColor=VINO_PROFUNDO,
            spaceAfter=8,
        ),
        "subtitulo": ParagraphStyle(
            "InformeSubtitulo",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=GRIS,
        ),
        "h1": ParagraphStyle(
            "InformeH1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=VINO_PROFUNDO,
            spaceBefore=12,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "InformeH2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=TINTA,
            spaceBefore=10,
            spaceAfter=5,
        ),
        "normal": ParagraphStyle(
            "InformeNormal",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=TINTA,
        ),
        "tabla": ParagraphStyle(
            "InformeTabla",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.9,
            leading=8.3,
            textColor=TINTA,
        ),
        "nota": ParagraphStyle(
            "InformeNota",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            leading=10,
            textColor=GRIS,
        ),
    }


def _pie_pagina(canvas, documento) -> None:
    canvas.saveState()
    ancho, _alto = A4
    canvas.setStrokeColor(LINEA)
    canvas.line(documento.leftMargin, 15 * mm, ancho - documento.rightMargin, 15 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GRIS)
    canvas.drawString(documento.leftMargin, 10 * mm, "Planta RILES - Informe operacional")
    canvas.drawRightString(ancho - documento.rightMargin, 10 * mm, f"Pagina {documento.page}")
    canvas.restoreState()


def _tabla_resumen(datos: pd.DataFrame, estilos: dict[str, ParagraphStyle]) -> Table:
    resumen = (
        datos.groupby("Area", dropna=False)
        .agg(
            Registros=("Valor", "size"),
            Parametros=("Parametro", "nunique"),
            Puntos=("Punto", "nunique"),
            Desde=("Fecha", "min"),
            Hasta=("Fecha", "max"),
        )
        .reset_index()
        .sort_values("Area")
    )
    filas = [["Area", "Registros", "Parametros", "Puntos", "Desde", "Hasta"]]
    for fila in resumen.itertuples(index=False):
        filas.append(
            [
                _texto(fila.Area),
                f"{int(fila.Registros):,}".replace(",", " "),
                str(int(fila.Parametros)),
                str(int(fila.Puntos)),
                _fecha(fila.Desde),
                _fecha(fila.Hasta),
            ]
        )
    tabla = Table(filas, colWidths=[100, 70, 72, 55, 90, 90], repeatRows=1)
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), VINO_PROFUNDO),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.35, LINEA),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PAPEL]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return tabla


def _grafico(datos: pd.DataFrame, titulo: str) -> Drawing:
    serie = datos[["Fecha", "Valor"]].dropna().sort_values("Fecha")
    if len(serie) > 120:
        posiciones = pd.Series(range(len(serie))).sample(120, random_state=7).sort_values()
        serie = serie.iloc[posiciones.to_list()]

    dibujo = Drawing(510, 160)
    dibujo.add(String(42, 145, titulo[:76], fontName="Helvetica-Bold", fontSize=8, fillColor=TINTA))
    dibujo.add(Line(42, 137, 468, 137, strokeColor=LINEA, strokeWidth=0.4))
    if serie.empty:
        dibujo.add(String(42, 78, "No hay valores numéricos para graficar.", fontName="Helvetica", fontSize=8, fillColor=GRIS))
        return dibujo

    valores = serie["Valor"].astype(float).to_list()
    if len(valores) == 1:
        grafico = VerticalBarChart()
        grafico.data = [[valores[0]]]
        grafico.bars[0].fillColor = VINO
        grafico.categoryAxis.categoryNames = ["Medición"]
        grafico.categoryAxis.labels.fontSize = 7
    else:
        grafico = LinePlot()
        grafico.data = [[(indice, valor) for indice, valor in enumerate(valores)]]
        grafico.lines[0].strokeColor = VINO
        grafico.lines[0].strokeWidth = 1.7
        grafico.joinedLines = 1
        grafico.xValueAxis.valueMin = 0
        grafico.xValueAxis.valueMax = max(len(valores) - 1, 1)
        grafico.xValueAxis.visible = False
    grafico.x = 42
    grafico.y = 33
    grafico.width = 426
    grafico.height = 92
    minimo, maximo = min(valores), max(valores)
    margen = max((maximo - minimo) * 0.12, abs(maximo) * 0.03, 1)
    eje_valores = (
        grafico.yValueAxis if isinstance(grafico, LinePlot) else grafico.valueAxis
    )
    eje_valores.valueMin = minimo - margen
    eje_valores.valueMax = maximo + margen
    eje_valores.labels.fontSize = 6.5
    eje_valores.strokeColor = LINEA
    eje_valores.gridStrokeColor = LINEA
    dibujo.add(grafico)
    dibujo.add(String(42, 16, _fecha(serie["Fecha"].iloc[0]), fontName="Helvetica", fontSize=6.5, fillColor=GRIS))
    dibujo.add(String(402, 16, _fecha(serie["Fecha"].iloc[-1]), fontName="Helvetica", fontSize=6.5, fillColor=GRIS))
    return dibujo


def _tabla_detalle(datos: pd.DataFrame, estilos: dict[str, ParagraphStyle]) -> LongTable:
    cabecera = [etiqueta for _columna, etiqueta, _ancho in COLUMNAS_DETALLE]
    filas = [cabecera]
    for fila in datos.sort_values("Fecha", ascending=False).itertuples(index=False):
        mapa = fila._asdict()
        filas.append(
            [
                _parrafo(_fecha(mapa.get(columna)) if columna == "Fecha" else (_numero(mapa.get(columna)) if columna == "Valor" else _texto(mapa.get(columna))), estilos["tabla"])
                for columna, _etiqueta, _ancho in COLUMNAS_DETALLE
            ]
        )
    tabla = LongTable(
        filas,
        colWidths=[ancho for _columna, _etiqueta, ancho in COLUMNAS_DETALLE],
        repeatRows=1,
        splitByRow=1,
    )
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), VINO),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, LINEA),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PAPEL]),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return tabla


def generar_informe_pdf(
    datos: pd.DataFrame,
    *,
    entorno: str,
    origen: str,
    titulo: str = "Informe operacional completo",
) -> bytes:
    """Genera un PDF con el resumen, gráficos y todas las mediciones del dashboard."""
    if datos.empty:
        raise ValueError("No hay datos disponibles para incluir en el informe PDF.")

    requeridas = {"Fecha", "Area", "Parametro", "Valor", "Unidad"}
    faltantes = requeridas.difference(datos.columns)
    if faltantes:
        raise ValueError("Faltan columnas para el informe: " + ", ".join(sorted(faltantes)))

    datos = datos.copy()
    for columna in ("Punto", "Turno", "TipoDato", "Calificador", "Fuente", "Hoja"):
        if columna not in datos.columns:
            datos[columna] = ""
    datos["Fecha"] = pd.to_datetime(datos["Fecha"], errors="coerce")
    datos["Valor"] = pd.to_numeric(datos["Valor"], errors="coerce")
    datos = datos.dropna(subset=["Fecha", "Valor", "Area", "Parametro"])
    if datos.empty:
        raise ValueError("No quedaron mediciones válidas para incluir en el informe PDF.")

    estilos = _estilos()
    salida = BytesIO()
    documento = SimpleDocTemplate(
        salida,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=18 * mm,
        bottomMargin=21 * mm,
        title=titulo,
        author="Planta RILES",
    )
    historia = [
        _parrafo(titulo, estilos["titulo"]),
        _parrafo(
            "Resumen integral de todas las áreas, parámetros, gráficos y registros disponibles en el dashboard.",
            estilos["subtitulo"],
        ),
        Spacer(1, 8 * mm),
    ]
    fecha_actualizacion = datetime.now().strftime("%d/%m/%Y %H:%M")
    ficha = [
        ["Generado", fecha_actualizacion],
        ["Entorno", entorno],
        ["Origen de datos", origen],
        ["Registros incluidos", f"{len(datos):,}".replace(",", " ")],
        ["Período", f"{_fecha(datos['Fecha'].min())} al {_fecha(datos['Fecha'].max())}"],
    ]
    tabla_ficha = Table(ficha, colWidths=[120, 390])
    tabla_ficha.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), PAPEL),
                ("TEXTCOLOR", (0, 0), (0, -1), VINO_PROFUNDO),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.35, LINEA),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    historia.extend([tabla_ficha, Spacer(1, 7 * mm), _parrafo("Resumen por área", estilos["h1"]), _tabla_resumen(datos, estilos), PageBreak()])

    grupos = datos.groupby(["Area", "Punto", "Parametro", "Unidad"], dropna=False, sort=True)
    area_actual = None
    for (area, punto, parametro, unidad), grupo in grupos:
        if area != area_actual:
            if area_actual is not None:
                historia.append(PageBreak())
            historia.append(_parrafo(f"Área: {_texto(area)}", estilos["h1"]))
            area_actual = area
        nombre = f"{_texto(parametro)} | Punto: {_texto(punto)}"
        historia.append(_parrafo(nombre, estilos["h2"]))
        estadisticas = [
            ["Registros", f"{len(grupo):,}".replace(",", " "), "Promedio", _numero(grupo["Valor"].mean())],
            ["Mínimo", _numero(grupo["Valor"].min()), "Máximo", _numero(grupo["Valor"].max())],
            ["Último", _numero(grupo.sort_values("Fecha")["Valor"].iloc[-1]), "Unidad", _texto(unidad)],
            ["Período", f"{_fecha(grupo['Fecha'].min())} al {_fecha(grupo['Fecha'].max())}", "Turnos", ", ".join(sorted({_texto(valor) for valor in grupo["Turno"]}))],
        ]
        tabla_estadisticas = Table(estadisticas, colWidths=[62, 188, 62, 188])
        tabla_estadisticas.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), PAPEL),
                    ("BACKGROUND", (2, 0), (2, -1), PAPEL),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("GRID", (0, 0), (-1, -1), 0.3, LINEA),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        historia.extend(
            [
                tabla_estadisticas,
                Spacer(1, 3 * mm),
                _grafico(grupo, f"Evolución de {parametro}"),
                _parrafo("Detalle completo de mediciones", estilos["nota"]),
                Spacer(1, 1.5 * mm),
                _tabla_detalle(grupo, estilos),
                Spacer(1, 5 * mm),
            ]
        )

    documento.build(historia, onFirstPage=_pie_pagina, onLaterPages=_pie_pagina)
    return salida.getvalue()
