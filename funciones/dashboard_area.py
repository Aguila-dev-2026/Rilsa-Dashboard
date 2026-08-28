import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from funciones.cargar_datos import (
    cargar_catalogo_operacional,
    cargar_datos_operacionales,
)
from funciones.filtros import (
    filtrar_contexto_operacional,
    filtrar_por_parametro,
    seleccionar_rango_fecha,
)
from funciones.tablas import preparar_columnas_visibles


CONFIGURACION_GRAFICO = {
    "displayModeBar": False,
    "scrollZoom": False,
    "responsive": True,
}

VINO = "#6D1F2B"
COBRE = "#B36F3D"
AZUL_CORPORATIVO = "#147EAF"
ROJO_ALERTA = "#A12C32"
TINTA = "#282422"
LINEA_SUAVE = "rgba(117,110,103,0.16)"

TIPO_GRAFICO_RECOMENDADO = {
    "Ingresos [Ton]": "Barras",
    "Consumo P. Catiónico [kg]": "Barras",
    "Consumo P. Aniónico [kg]": "Barras",
    "Consumo PAC [kg]": "Barras",
    "Consumo Cal [kg]": "Barras",
    "% Humedad Lodo 1": "Líneas",
    "% Humedad Lodo 2": "Líneas",
    "Energía eléctrica consumida": "Barras",
    "Volumen TK3 [m3]": "Barras",
    "DQO TK3 [mg/l]": "Barras",
    "pH": "Líneas",
    "Conductividad [mS]": "Líneas",
    "Conductividad": "Líneas",
    "Turbiedad [NTU]": "Líneas",
    "Turbidez": "Líneas",
}

# Los acumulativos se suman por mes. Todos los demás parámetros activos
# se resumen mediante promedio mensual.
PARAMETROS_ACUMULATIVOS = {
    "Ingresos [Ton]",
    "Consumo P. Catiónico [kg]",
    "Consumo P. Aniónico [kg]",
    "Consumo PAC [kg]",
    "Consumo Cal [kg]",
    "Energía eléctrica consumida",
    "Descarga a Reactor N°1",
    "Carga DBO5",
    "Carga de nitrógeno total",
    "Carga de fósforo total",
}

TIPO_TENDENCIA_RECOMENDADA = {
    "Ingresos [Ton]": "EWMA adaptativa",
    "Consumo P. Catiónico [kg]": "EWMA adaptativa",
    "Consumo P. Aniónico [kg]": "EWMA adaptativa",
    "Consumo PAC [kg]": "EWMA adaptativa",
    "Consumo Cal [kg]": "EWMA adaptativa",
    "Energía eléctrica consumida": "EWMA adaptativa",
    "% Humedad Lodo 1": "Theil–Sen",
    "% Humedad Lodo 2": "Theil–Sen",
    "Volumen TK3 [m3]": "EWMA adaptativa",
    "DQO TK3 [mg/l]": "Theil–Sen",
    "Conductividad [mS]": "Theil–Sen",
    "Turbiedad [NTU]": "Theil–Sen",
    "pH": "Theil–Sen",
}

# Referencias NCh 1333 para uso de agua de riego. Boro se presenta con el
# valor conservador para cultivos sensibles; puede ajustarse según el cultivo.
BANDAS_NCH1333_RIEGO = {
    "pH": {"inferior": 5.5, "superior": 9.0, "etiqueta": "Límite NCh 1333 · pH 5,5–9,0"},
    "Conductividad": {"superior": 0.75, "etiqueta": "Límite NCh 1333 · CE ≤ 0,75 mS/cm"},
    "Conductividad [mS]": {"superior": 0.75, "etiqueta": "Límite NCh 1333 · CE ≤ 0,75 mS/cm"},
    "Sulfato": {"superior": 250.0, "etiqueta": "Límite NCh 1333 · Sulfato ≤ 250 mg/L"},
    "Boro total": {"superior": 0.75, "etiqueta": "Límite NCh 1333 · Boro ≤ 0,75 mg/L"},
    "Sólidos disueltos": {"superior": 500.0, "etiqueta": "Límite NCh 1333 · Sólidos disueltos ≤ 500 mg/L"},
    "Cloruro": {"superior": 200.0, "etiqueta": "Límite NCh 1333 · Cloruro ≤ 200 mg/L"},
}


def tema_nativo_oscuro():
    """Consulta el tema elegido en el selector nativo de Streamlit."""
    try:
        return st.context.theme.type == "dark"
    except (AttributeError, RuntimeError):
        return False


def paleta_grafico(oscuro):
    """Devuelve los colores necesarios para gráficos fuera del DOM principal."""
    if oscuro:
        return {
            "template": "plotly_dark",
            "texto": "#FAFAFA",
            "texto_eje": "#C8CBD4",
            "cuadricula": "rgba(250,250,250,0.14)",
            "borde_marcador": "#0E1117",
            "fin_semana": "#72B7E3",
        }
    return {
        "template": "plotly_white",
        "texto": "#171514",
        "texto_eje": "#332E2A",
        "cuadricula": "rgba(23,21,20,0.24)",
        "borde_marcador": "#FFFDF8",
        "fin_semana": "#4F92BD",
    }


def obtener_banda_normativa(parametro):
    return BANDAS_NCH1333_RIEGO.get(parametro)


def obtener_limites_activos(parametro, limites_internos=None):
    """Devuelve el rango más restrictivo de las bandas actualmente visibles."""
    inferiores = []
    superiores = []
    mostrar_normativa = (
        limites_internos is None
        or limites_internos.get("normativa", True)
    )
    normativa = obtener_banda_normativa(parametro)
    if normativa and mostrar_normativa:
        if normativa.get("inferior") is not None:
            inferiores.append(float(normativa["inferior"]))
        if normativa.get("superior") is not None:
            superiores.append(float(normativa["superior"]))

    if limites_internos is not None:
        if limites_internos.get("inferior") is not None:
            inferiores.append(float(limites_internos["inferior"]))
        if limites_internos.get("superior") is not None:
            superiores.append(float(limites_internos["superior"]))

    return (
        max(inferiores) if inferiores else None,
        min(superiores) if superiores else None,
    )


def resaltar_valores_fuera_de_rango(
    fig,
    tipo_grafico,
    datos,
    limites_activos,
    columna_medicion=None,
):
    """Destaca en rojo las mediciones reales que exceden una banda activa."""
    limite_inferior, limite_superior = limites_activos
    if limite_inferior is None and limite_superior is None:
        return

    serie = datos[["Fecha", "Valor"]].copy().reset_index(drop=True)
    valores = pd.to_numeric(serie["Valor"], errors="coerce")
    fuera_de_rango = pd.Series(False, index=serie.index)
    if limite_inferior is not None:
        fuera_de_rango |= valores.lt(limite_inferior)
    if limite_superior is not None:
        fuera_de_rango |= valores.gt(limite_superior)
    fuera_de_rango &= valores.notna()
    if columna_medicion is not None:
        fuera_de_rango &= datos[columna_medicion].reset_index(drop=True).astype(bool)

    if tipo_grafico == "Barras":
        colores = [
            ROJO_ALERTA if alerta else AZUL_CORPORATIVO
            for alerta in fuera_de_rango
        ]
        fig.update_traces(marker_color=colores)
        return

    # La línea azul permanece como contexto; solo los tramos y puntos fuera de
    # rango se superponen en rojo para no sugerir que los datos faltantes alertan.
    serie["FueraDeRango"] = fuera_de_rango
    serie["Tramo"] = serie["FueraDeRango"].ne(
        serie["FueraDeRango"].shift()
    ).cumsum()
    primer_tramo = True
    for _, tramo in serie[serie["FueraDeRango"]].groupby("Tramo"):
        fig.add_scatter(
            x=tramo["Fecha"],
            y=tramo["Valor"],
            mode="lines+markers",
            name="Fuera de rango" if primer_tramo else None,
            showlegend=primer_tramo,
            line=dict(color=ROJO_ALERTA, width=3.8),
            marker=dict(
                color=ROJO_ALERTA,
                size=8,
                line=dict(color="#FFFFFF", width=1.4),
            ),
            hovertemplate="<b>%{x|%d/%m/%Y}</b><br>"
            "Valor fuera de rango: %{y:,.2f}<extra></extra>",
        )
        primer_tramo = False


def tipo_grafico_recomendado(parametro):
    """Usa barras para acumulados y líneas para mediciones de calidad."""
    if parametro in PARAMETROS_ACUMULATIVOS:
        return "Barras"
    return TIPO_GRAFICO_RECOMENDADO.get(parametro, "Líneas")


def metodo_tendencia_recomendado(parametro, unidad):
    unidades_ewma = {"kg", "kg/día", "ton", "m3", "m3/día", "m³", "m³/día"}
    if parametro in TIPO_TENDENCIA_RECOMENDADA:
        return TIPO_TENDENCIA_RECOMENDADA[parametro]
    return "EWMA adaptativa" if unidad in unidades_ewma else "Theil–Sen"


def calcular_tendencia(datos, parametro, unidad=""):
    """Calcula la tendencia recomendada usando solo valores válidos del filtro."""
    validos = (
        datos.loc[
            datos["Valor"].notna() & datos["Valor"].ne(0),
            ["Fecha", "Valor"],
        ]
        .sort_values("Fecha")
        .copy()
    )
    if len(validos) < 2:
        return None, metodo_tendencia_recomendado(parametro, unidad)

    metodo = metodo_tendencia_recomendado(parametro, unidad)

    if metodo == "EWMA adaptativa":
        cantidad = len(validos)
        if cantidad <= 7:
            ventana = 3
        elif cantidad <= 31:
            ventana = 7
        elif cantidad <= 90:
            ventana = 14
        else:
            ventana = 30

        tendencia = validos.copy()
        tendencia["Tendencia"] = (
            tendencia["Valor"]
            .ewm(span=min(ventana, cantidad), adjust=False)
            .mean()
        )
        return tendencia[["Fecha", "Tendencia"]], metodo

    origen = validos["Fecha"].iloc[0]
    x = (validos["Fecha"] - origen).dt.total_seconds().to_numpy() / 86400
    y = validos["Valor"].to_numpy(dtype=float)
    pendientes = [
        (y[j] - y[i]) / (x[j] - x[i])
        for i in range(len(x) - 1)
        for j in range(i + 1, len(x))
        if x[j] != x[i]
    ]
    if not pendientes:
        return None, metodo

    pendiente = float(np.median(pendientes))
    intercepto = float(np.median(y - pendiente * x))
    tendencia = validos[["Fecha"]].copy()
    tendencia["Tendencia"] = intercepto + pendiente * x
    return tendencia, metodo


def agregar_tendencia(fig, datos, parametro, unidad):
    tendencia, metodo = calcular_tendencia(datos, parametro, unidad)
    if tendencia is None:
        return metodo

    sufijo_unidad = f" {unidad}" if unidad else ""
    fig.add_scatter(
        x=tendencia["Fecha"],
        y=tendencia["Tendencia"],
        mode="lines",
        name=f"Tendencia · {metodo}",
        line=dict(color=COBRE, width=3.2, dash="dot"),
        hovertemplate=(
            "<b>%{x|%d/%m/%Y}</b><br>"
            f"Tendencia: %{{y:,.2f}}{sufijo_unidad}<extra></extra>"
        ),
    )
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="right",
            x=0.99,
        )
    )
    return metodo


def agregar_bandas(fig, parametro, limites_internos=None):
    """Añade bandas normativas e internas sin depender de la tendencia."""
    mostrar_normativa = (
        limites_internos is None
        or limites_internos.get("normativa", True)
    )
    normativa = obtener_banda_normativa(parametro)
    if normativa and mostrar_normativa:
        limite_inferior_norma = normativa.get("inferior")
        limite_superior_norma = normativa.get("superior")
        if limite_inferior_norma is not None and limite_superior_norma is not None:
            fig.add_hrect(
                y0=limite_inferior_norma,
                y1=limite_superior_norma,
                fillcolor="rgba(46,106,77,0.14)",
                line_width=0,
                layer="below",
                annotation_text=normativa["etiqueta"],
                annotation_position="top left",
                annotation_font=dict(color="#4F9A75", size=12),
            )
        for limite in (limite_inferior_norma, limite_superior_norma):
            if limite is None:
                continue
            opciones_linea = {
                "y": limite,
                "line": dict(
                    color="rgba(79,154,117,0.78)",
                    width=1.2,
                    dash="dash",
                ),
            }
            if limite_inferior_norma is None:
                opciones_linea.update(
                    annotation_text=normativa["etiqueta"],
                    annotation_position="bottom left",
                    annotation_font=dict(color="#4F9A75", size=12),
                    annotation_bgcolor="rgba(247,249,252,0.94)",
                    annotation_bordercolor="rgba(79,154,117,0.45)",
                    annotation_borderpad=4,
                )
            fig.add_hline(**opciones_linea)

    if limites_internos is None:
        return

    limite_inferior = limites_internos.get("inferior")
    limite_superior = limites_internos.get("superior")
    if limite_inferior is not None and limite_superior is not None:
        fig.add_hrect(
            y0=limite_inferior,
            y1=limite_superior,
            fillcolor="rgba(161,44,50,0.075)",
            line_width=0,
            layer="below",
            annotation_text=(
                "Bandas internas · "
                f"{limite_inferior:,.2f}–{limite_superior:,.2f}"
            ),
            annotation_position="bottom right",
            annotation_font=dict(color=ROJO_ALERTA, size=12),
        )

    bandas_activas = (
        ("Banda inferior", limite_inferior),
        ("Banda superior", limite_superior),
    )
    for nombre, limite in bandas_activas:
        if limite is None:
            continue
        fig.add_hline(
            y=limite,
            line=dict(color=ROJO_ALERTA, width=2.4),
            annotation_text=(f"{nombre} · {limite:,.2f}")
            if limite_inferior is None or limite_superior is None
            else None,
            annotation_position="bottom right",
            annotation_font=dict(color=ROJO_ALERTA, size=12),
        )


def configurar_bandas(datos, clave, tiene_bandas_normativas=False):
    """Recoge bandas independientes y las conserva durante la sesión."""
    valores = datos["Valor"].dropna().astype(float)
    if valores.empty:
        return None

    minimo_observado = float(valores.min())
    maximo_observado = float(valores.max())
    amplitud = max(maximo_observado - minimo_observado, abs(valores.mean()) * 0.1, 1)
    paso = max(amplitud / 100, 0.01)
    superior_inicial = max(maximo_observado, minimo_observado + paso)

    with st.sidebar.expander("Bandas", expanded=False):
        st.caption("Referencias normativas e internas para control operacional.")
        mostrar_normativa = True
        if tiene_bandas_normativas:
            mostrar_normativa = st.toggle(
                "Mostrar bandas normativas",
                value=True,
                key=f"mostrar_bandas_normativas_{clave}",
            )
        mostrar_inferior = st.toggle(
            "Añadir banda inferior",
            value=False,
            key=f"mostrar_banda_inferior_{clave}",
        )
        limite_inferior = None
        if mostrar_inferior:
            limite_inferior = st.number_input(
                "Límite inferior",
                value=minimo_observado,
                step=paso,
                format="%.3f",
                key=f"limite_interno_inferior_{clave}",
            )

        mostrar_superior = st.toggle(
            "Añadir banda superior",
            value=False,
            key=f"mostrar_banda_superior_{clave}",
        )
        limite_superior = None
        if mostrar_superior:
            limite_superior = st.number_input(
                "Límite superior",
                value=superior_inicial,
                step=paso,
                format="%.3f",
                key=f"limite_interno_superior_{clave}",
            )

        if (
            limite_inferior is None
            and limite_superior is None
            and not tiene_bandas_normativas
        ):
            return None
        if (
            limite_inferior is not None
            and limite_superior is not None
            and limite_inferior >= limite_superior
        ):
            st.warning("El límite inferior debe ser menor que el superior.")
            return None
        return {
            "normativa": mostrar_normativa,
            "inferior": float(limite_inferior)
            if limite_inferior is not None
            else None,
            "superior": float(limite_superior)
            if limite_superior is not None
            else None,
        }


def aplicar_estilo_premium(fig, tipo_grafico, parametro, unidad):
    azul_borde = "#0C638D"
    cobre = "#D99A68"
    borde_marcador = paleta_grafico(tema_nativo_oscuro())["borde_marcador"]

    etiqueta_valor = f"%{{y:,.2f}} {unidad}".strip()
    fig.update_traces(
        hovertemplate=(
            "<b>%{x|%d/%m/%Y}</b><br>"
            f"{parametro}: {etiqueta_valor}<extra></extra>"
        )
    )

    if tipo_grafico == "Barras":
        fig.update_traces(
            marker=dict(
                color=AZUL_CORPORATIVO,
                line=dict(color=azul_borde, width=0.7),
            ),
            opacity=0.94,
        )
    else:
        fig.update_traces(
            line=dict(color=AZUL_CORPORATIVO, width=3.2),
            marker=dict(
                color="#67C5E8",
                size=7,
                line=dict(color=borde_marcador, width=1.4),
            ),
            fill="tozeroy",
            fillcolor="rgba(20,126,175,0.10)",
        )

    fig.update_layout(
        title=dict(
            text=f"<b>{parametro}</b>",
            x=0.015,
            xanchor="left",
            font=dict(size=21),
        ),
        font=dict(family='"Source Sans Pro", sans-serif'),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor="#40566C",
            bordercolor="#172C50",
            font=dict(color="#FFFFFF", size=13),
            align="left",
            namelength=-1,
        ),
        hovermode="x unified",
        bargap=0.28,
        barcornerradius=6,
        margin=dict(l=82, r=18, t=78, b=92),
    )
    fig.update_xaxes(
        title=None,
        showgrid=False,
        showline=True,
        linewidth=1,
        tickfont=dict(size=12),
    )
    fig.update_yaxes(
        title=f"Valor ({unidad})" if unidad else "Valor",
        showgrid=True,
        gridwidth=1,
        zeroline=False,
        showline=False,
        tickfont=dict(size=12),
        title_font=dict(size=12),
        title_standoff=22,
        automargin=True,
    )

def mostrar_grafico_desplazable(fig, cantidad_periodos):
    """Replica el tema nativo dentro del iframe y añade scroll horizontal."""
    ancho_grafico = cantidad_periodos * 24
    oscuro = tema_nativo_oscuro()
    paleta = paleta_grafico(oscuro)

    fig.update_layout(
        template=paleta["template"],
        font=dict(
            family='"Source Sans Pro", sans-serif',
            color=paleta["texto"],
        ),
        width=ancho_grafico,
        height=480,
        autosize=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(tickfont=dict(size=12, color=paleta["texto_eje"]))
    fig.update_yaxes(
        tickfont=dict(size=12, color=paleta["texto_eje"]),
        title_font=dict(size=12, color=paleta["texto_eje"]),
        gridcolor=paleta["cuadricula"],
    )

    grafico_html = fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        config=CONFIGURACION_GRAFICO,
    )
    ancho_contenido = f"{ancho_grafico}px"
    desbordamiento = "auto"

    html = f"""
    <!doctype html>
    <html>
    <head>
      <style>
        html, body {{
          width: 100%;
          margin: 0;
          padding: 0;
          background: transparent;
          color-scheme: {"dark" if oscuro else "light"};
          overflow: hidden;
        }}
        .contenedor-grafico {{
          width: 100%;
          overflow-x: {desbordamiento};
          overflow-y: hidden;
          padding-bottom: 8px;
          scrollbar-gutter: stable;
        }}
        .contenido-grafico {{
          width: {ancho_contenido};
          min-width: {ancho_contenido};
        }}
      </style>
    </head>
    <body>
      <div class="contenedor-grafico">
        <div class="contenido-grafico">{grafico_html}</div>
      </div>
    </body>
    </html>
    """
    components.html(html, height=530, scrolling=False)





def preparar_tabla_premium(datos):
    tabla = (
        preparar_columnas_visibles(datos)
        .sort_values("Fecha", ascending=False)
        .rename(
            columns={
                "Area": "Área",
                "Parametro": "Parámetro",
            }
        )
        .reset_index(drop=True)
    )

    # Los fondos y encabezados quedan a cargo del tema nativo de Streamlit.
    return (
        tabla.style
        .set_properties(
            subset=["Valor"],
            **{"font-weight": "700"},
        )
        .format({"Valor": "{:,.2f}"}, na_rep="—")
    )


def mostrar_dashboard_area(nombre_area, titulo):
    st.header(titulo)

    catalogo = cargar_catalogo_operacional(nombre_area=nombre_area)
    catalogo = catalogo[catalogo["Area"].eq(nombre_area)].copy()

    if catalogo.empty:
        st.warning(f"No hay datos disponibles para {nombre_area}.")
        return

    clave_area = (
        nombre_area.casefold()
        .replace(" ", "_")
        .replace("í", "i")
        .replace("ó", "o")
    )
    catalogo = filtrar_contexto_operacional(catalogo, clave_area)
    if catalogo.empty:
        st.info("No hay datos para la selección de proceso indicada.")
        return

    partes_clave = [clave_area]
    if "Punto" in catalogo.columns:
        valores = catalogo["Punto"].fillna("").astype(str).unique()
        if len(valores) == 1:
            partes_clave.append(valores[0].casefold().replace(" ", "_"))
    clave_contexto = "_".join(partes_clave)

    catalogo_parametro = filtrar_por_parametro(
        catalogo,
        clave=clave_contexto,
    )
    if catalogo_parametro.empty:
        st.info("No hay datos para el parámetro seleccionado.")
        return

    parametro = catalogo_parametro["Parametro"].iat[0]
    unidades = (
        catalogo_parametro["Unidad"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    unidades = unidades[unidades.ne("")]
    unidad = unidades.iat[0] if not unidades.empty else ""
    punto = (
        catalogo_parametro["Punto"]
        .fillna("")
        .astype(str)
        .str.strip()
        .iat[0]
    )

    clave_fechas = f"{clave_contexto}_{parametro.casefold()}"
    fecha_inicio_seleccionada, fecha_fin_seleccionada = seleccionar_rango_fecha(
        catalogo_parametro["FechaMin"].min(),
        catalogo_parametro["FechaMax"].max(),
        clave=clave_fechas,
    )
    if fecha_inicio_seleccionada is None:
        return

    datos_filtrados = cargar_datos_operacionales(
        nombre_area=nombre_area,
        punto=punto,
        parametro=parametro,
        fecha_inicio=fecha_inicio_seleccionada,
        fecha_fin=fecha_fin_seleccionada,
    )
    if datos_filtrados.empty:
        st.info("No hay datos para el rango de fechas seleccionado.")
        return

    datos_filtrados = datos_filtrados.sort_values("Fecha")
    # El Print nativo lee esta selección durante el mismo rerun de Streamlit.
    # Así el informe respeta área, punto, parámetro y fechas visibles.
    st.session_state["datos_para_impresion"] = datos_filtrados.copy()

    tipo_recomendado = tipo_grafico_recomendado(parametro)
    clave_tipo = f"tipo_grafico_{clave_contexto}"
    clave_parametro_tipo = f"parametro_tipo_grafico_{clave_contexto}"
    if st.session_state.get(clave_parametro_tipo) != parametro:
        st.session_state[clave_tipo] = tipo_recomendado
        st.session_state[clave_parametro_tipo] = parametro

    tipo_grafico = st.sidebar.selectbox(
        "Tipo de gráfico",
        ["Líneas", "Barras"],
        key=clave_tipo,
    )
    st.sidebar.caption(f"Gráfico recomendado: {tipo_recomendado}.")

    mostrar_tendencia = st.sidebar.toggle(
        "Mostrar tendencia",
        value=True,
        key=f"mostrar_tendencia_{clave_contexto}",
    )
    clave_banda = f"{clave_contexto}_{parametro.casefold()}"
    limites_internos = configurar_bandas(
        datos_filtrados,
        clave=clave_banda,
        tiene_bandas_normativas=obtener_banda_normativa(parametro) is not None,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Registros", len(datos_filtrados))
    col2.metric("Promedio", f"{datos_filtrados['Valor'].mean():.2f} {unidad}".strip())
    col3.metric(
        "Último valor",
        f"{datos_filtrados['Valor'].iloc[-1]:.2f} {unidad}".strip(),
    )

    # Primero se consolida cada día para que las mediciones Mañana/Tarde
    # no se dupliquen al construir un total mensual.
    datos_para_serie = datos_filtrados
    if tipo_grafico == "Líneas":
        datos_para_serie = datos_para_serie[
            datos_para_serie["Valor"].notna()
            & datos_para_serie["Valor"].ne(0)
        ]

    datos_diarios = (
        datos_para_serie.groupby("Fecha", as_index=False, sort=True)["Valor"]
        .mean()
    )
    fecha_inicio = pd.Timestamp(fecha_inicio_seleccionada).normalize()
    fecha_fin = pd.Timestamp(fecha_fin_seleccionada).normalize()
    dias = pd.date_range(fecha_inicio, fecha_fin, freq="D")
    cantidad_meses = (
        (fecha_fin.year - fecha_inicio.year) * 12
        + fecha_fin.month
        - fecha_inicio.month
        + 1
    )
    resumen_mensual = cantidad_meses >= 3

    if resumen_mensual:
        fechas_grafico = pd.date_range(
            fecha_inicio.to_period("M").start_time,
            fecha_fin.to_period("M").start_time,
            freq="MS",
        )
        datos_mensuales = datos_diarios.copy()
        datos_mensuales["Fecha"] = (
            datos_mensuales["Fecha"].dt.to_period("M").dt.to_timestamp()
        )

        if parametro in PARAMETROS_ACUMULATIVOS:
            datos_serie = (
                datos_mensuales.groupby("Fecha", as_index=False, sort=True)["Valor"]
                .sum(min_count=1)
            )
            metodo_resumen = "acumulado mensual"
        else:
            datos_serie = (
                datos_mensuales.groupby("Fecha", as_index=False, sort=True)["Valor"]
                .mean()
            )
            metodo_resumen = "promedio mensual"

        st.sidebar.caption(f"Resumen temporal: {metodo_resumen}.")
    else:
        fechas_grafico = dias
        datos_serie = datos_diarios

    # La tabla conserva cada registro original; solo la serie gráfica se resume.
    datos_grafico = (
        pd.DataFrame({"Fecha": fechas_grafico})
        .merge(
            datos_serie[["Fecha", "Valor"]],
            on="Fecha",
            how="left",
        )
    )
    # Barras completan el calendario con cero; se marca qué datos son mediciones
    # reales para que esos ceros de relleno nunca aparezcan como alertas.
    datos_grafico["MedicionDisponible"] = datos_grafico["Valor"].notna()
    datos_grafico["Valor"] = datos_grafico["Valor"].fillna(0)

    opciones = {
        "x": "Fecha",
        "y": "Valor",
        "title": f"{parametro} — evolución en el período seleccionado",
        "labels": {
            "Fecha": "Fecha",
            "Valor": f"Valor ({unidad})" if unidad else "Valor",
        },
    }

    if tipo_grafico == "Barras":
        fig = px.bar(datos_grafico, **opciones)
    else:
        datos_linea = datos_serie[
            datos_serie["Valor"].notna()
            & datos_serie["Valor"].ne(0)
        ].copy()

        if datos_linea.empty:
            st.info("No hay valores distintos de cero para mostrar en el gráfico lineal.")
            return

        fig = px.line(datos_linea, markers=True, **opciones)

    aplicar_estilo_premium(fig, tipo_grafico, parametro, unidad)
    agregar_bandas(
        fig,
        parametro,
        limites_internos=limites_internos,
    )
    resaltar_valores_fuera_de_rango(
        fig,
        tipo_grafico,
        datos_grafico if tipo_grafico == "Barras" else datos_linea,
        obtener_limites_activos(parametro, limites_internos),
        columna_medicion="MedicionDisponible" if tipo_grafico == "Barras" else None,
    )

    if mostrar_tendencia:
        metodo_tendencia = agregar_tendencia(
            fig,
            datos_serie,
            parametro,
            unidad,
        )
        st.sidebar.caption(f"Tendencia automática: {metodo_tendencia}.")

    dias_semana = ("L", "M", "M", "J", "V", "S", "D")
    meses_abreviados = (
        "ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
        "JUL", "AGO", "SEP", "OCT", "NOV", "DIC",
    )
    if resumen_mensual:
        margen_lateral = pd.Timedelta(days=12)
        inicio_eje = fechas_grafico[0]
        fin_eje = fechas_grafico[-1]
        marcas_eje_x = fechas_grafico
        etiquetas_eje_x = []
        for posicion, inicio_mes in enumerate(fechas_grafico):
            etiqueta = meses_abreviados[inicio_mes.month - 1][0]
            if posicion == 0 or inicio_mes.month == 1:
                etiqueta += (
                    f"<br><span style='color:{COBRE}'><b>"
                    f"{inicio_mes.year}</b></span>"
                )
            etiquetas_eje_x.append(etiqueta)
    else:
        margen_lateral = pd.Timedelta(hours=12)
        inicio_eje = fecha_inicio
        fin_eje = fecha_fin
        azul_fin_semana = paleta_grafico(tema_nativo_oscuro())["fin_semana"]
        marcas_eje_x = dias
        etiquetas_eje_x = []
        for dia in dias:
            if dia.weekday() >= 5:
                etiqueta = (
                    f"<span style='color:{azul_fin_semana}'><b>{dia.day}<br>"
                    f"{dias_semana[dia.weekday()]}</b></span>"
                )
            else:
                etiqueta = f"{dia.day}<br>{dias_semana[dia.weekday()]}"

            if dia.day == 1:
                etiqueta += (
                    f"<br><span style='color:{COBRE}'><b>"
                    f"{meses_abreviados[dia.month - 1]}</b></span>"
                )
            etiquetas_eje_x.append(etiqueta)

    fig.update_xaxes(
        range=[
            inicio_eje - margen_lateral,
            fin_eje + margen_lateral,
        ],
        tickmode="array",
        tickvals=marcas_eje_x,
        ticktext=etiquetas_eje_x,
        tickangle=0,
        fixedrange=True,
        automargin=True,
    )
    fig.update_yaxes(fixedrange=True)

    with st.container(border=True):
        # Entre 31 días y tres meses aún se grafican datos diarios. En ese
        # tramo el scroll conserva separación entre fechas; desde tres meses
        # la serie ya está resumida mensualmente y permanece responsiva.
        if not resumen_mensual and len(fechas_grafico) > 30:
            mostrar_grafico_desplazable(fig, len(fechas_grafico))
        else:
            st.plotly_chart(
                fig,
                width="stretch",
                config=CONFIGURACION_GRAFICO,
                theme="streamlit",
            )

    st.markdown(
        "<h3 class='riles-tabla-titulo'>Registros mostrados</h3>",
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.caption("DETALLE DE MEDICIONES · ORDEN CRONOLÓGICO DESCENDENTE")
        st.dataframe(
            preparar_tabla_premium(datos_filtrados),
            width="stretch",
            hide_index=True,
            column_config={
                "Fecha": st.column_config.DateColumn(
                    "Fecha",
                    format="DD/MM/YYYY",
                ),
                "Valor": st.column_config.NumberColumn(
                    "Valor",
                    format="%.2f",
                ),
            },
        )
