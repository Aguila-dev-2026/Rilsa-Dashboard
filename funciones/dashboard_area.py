import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from funciones.cargar_datos import cargar_datos_operacionales
from funciones.filtros import filtrar_por_fecha, filtrar_por_parametro


CONFIGURACION_GRAFICO = {
    "displayModeBar": False,
    "scrollZoom": False,
    "responsive": True,
}

VINO = "#6D1F2B"
VINO_OSCURO = "#48121A"
COBRE = "#B36F3D"
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
    "Volumen TK3 [m3]": "Líneas",
    "DQO TK3 [mg/l]": "Líneas",
    "pH": "Líneas",
    "Conductividad [mS]": "Líneas",
    "Turbiedad [NTU]": "Líneas",
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
    "Volumen TK3 [m3]": "Theil–Sen",
    "DQO TK3 [mg/l]": "Theil–Sen",
    "Conductividad [mS]": "Theil–Sen",
    "Turbiedad [NTU]": "Theil–Sen",
    "pH": "Theil–Sen",
}


def calcular_tendencia(datos, parametro, ajustes=None):
    """Calcula la tendencia recomendada usando solo valores válidos del filtro."""
    ajustes = ajustes or {}
    validos = (
        datos.loc[
            datos["Valor"].notna() & datos["Valor"].ne(0),
            ["Fecha", "Valor"],
        ]
        .sort_values("Fecha")
        .copy()
    )
    if len(validos) < 2:
        return None, TIPO_TENDENCIA_RECOMENDADA.get(parametro, "Theil–Sen")

    metodo = TIPO_TENDENCIA_RECOMENDADA.get(parametro, "Theil–Sen")

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

        ventana = int(ajustes.get("periodos_ewma", ventana))
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


def agregar_tendencia(fig, datos, parametro, unidad, ajustes=None):
    ajustes = ajustes or {}
    tendencia, metodo = calcular_tendencia(datos, parametro, ajustes)
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
    if parametro == "pH":
        limite_inferior = float(ajustes.get("ph_minimo", 6))
        limite_superior = float(ajustes.get("ph_maximo", 8))
        if limite_inferior < limite_superior:
            fig.add_hrect(
                y0=limite_inferior,
                y1=limite_superior,
                fillcolor="rgba(46,106,77,0.14)",
                line_width=0,
                layer="below",
                annotation_text=(
                    f"Banda operativa pH {limite_inferior:g}–{limite_superior:g}"
                ),
                annotation_position="top left",
                annotation_font=dict(color="#4F9A75", size=12),
            )
            fig.add_hline(
                y=limite_inferior,
                line=dict(color="rgba(79,154,117,0.72)", width=1, dash="dash"),
            )
            fig.add_hline(
                y=limite_superior,
                line=dict(color="rgba(79,154,117,0.72)", width=1, dash="dash"),
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


def tema_nativo_oscuro():
    try:
        return st.context.theme.type == "dark"
    except (AttributeError, RuntimeError):
        return True


def aplicar_estilo_premium(fig, tipo_grafico, parametro, unidad):
    vino = "#A94353"
    vino_oscuro = "#6D1F2B"
    cobre = "#D99A68"

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
                color=vino,
                line=dict(color=vino_oscuro, width=0.7),
            ),
            opacity=0.94,
        )
    else:
        fig.update_traces(
            line=dict(color=vino, width=3),
            marker=dict(
                color=cobre,
                size=7,
                line=dict(color="#FFFDF8", width=1.4),
            ),
            fill="tozeroy",
            fillcolor="rgba(169,67,83,0.09)",
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
            bgcolor=vino_oscuro,
            bordercolor=vino_oscuro,
            font=dict(color="#FFFFFF", size=13),
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

def mostrar_grafico_desplazable(fig, cantidad_dias):
    """Replica el tema nativo y añade scroll únicamente desde el día 32."""
    ancho_grafico = cantidad_dias * 48
    oscuro = tema_nativo_oscuro()
    texto = "#FAFAFA" if oscuro else "#171514"
    texto_eje = "#C8CBD4" if oscuro else "#332E2A"
    cuadricula = "rgba(250,250,250,0.12)" if oscuro else "rgba(23,21,20,0.14)"

    fig.update_layout(
        template="plotly_dark" if oscuro else "plotly_white",
        font=dict(family='"Source Sans Pro", sans-serif', color=texto),
        width=ancho_grafico,
        height=480,
        autosize=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(tickfont=dict(size=12, color=texto_eje))
    fig.update_yaxes(
        tickfont=dict(size=12, color=texto_eje),
        title_font=dict(size=12, color=texto_eje),
        gridcolor=cuadricula,
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
        datos.sort_values("Fecha", ascending=False)
        .rename(
            columns={
                "Area": "Área",
                "Parametro": "Parámetro",
            }
        )
        .reset_index(drop=True)
    )

    # Los fondos y encabezados quedan a cargo del tema nativo de Streamlit,
    # para que cambien de forma fiable entre Light y Dark.
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

    datos = cargar_datos_operacionales()
    datos = datos[datos["Area"] == nombre_area].copy()

    if datos.empty:
        st.warning(f"No hay datos disponibles para {nombre_area}.")
        return

    datos = filtrar_por_fecha(datos)
    if datos.empty:
        st.info("No hay datos para el rango de fechas seleccionado.")
        return

    datos_filtrados = filtrar_por_parametro(datos)
    if datos_filtrados.empty:
        st.info("No hay datos para el parámetro seleccionado.")
        return

    datos_filtrados = datos_filtrados.sort_values("Fecha")
    parametro = datos_filtrados["Parametro"].iat[0]
    unidad = (
        datos_filtrados["Unidad"].dropna().iloc[0]
        if datos_filtrados["Unidad"].notna().any()
        else ""
    )

    tipo_recomendado = TIPO_GRAFICO_RECOMENDADO.get(parametro, "Líneas")
    if st.session_state.get("parametro_tipo_grafico") != parametro:
        st.session_state["tipo_grafico"] = tipo_recomendado
        st.session_state["parametro_tipo_grafico"] = parametro

    tipo_grafico = st.sidebar.selectbox(
        "Tipo de gráfico",
        ["Líneas", "Barras"],
        key="tipo_grafico",
    )
    st.sidebar.caption(f"Gráfico recomendado: {tipo_recomendado}.")

    metodo_recomendado = TIPO_TENDENCIA_RECOMENDADA.get(
        parametro,
        "Theil–Sen",
    )
    mostrar_tendencia = st.sidebar.toggle(
        "Mostrar tendencia",
        value=True,
        key="mostrar_tendencia",
    )
    ajustes_tendencia = {}
    with st.sidebar.expander("Ajustar cálculo de tendencia"):
        if metodo_recomendado == "EWMA adaptativa":
            cantidad_validos = int(
                (
                    datos_filtrados["Valor"].notna()
                    & datos_filtrados["Valor"].ne(0)
                ).sum()
            )
            if cantidad_validos <= 7:
                periodos_recomendados = 3
            elif cantidad_validos <= 31:
                periodos_recomendados = 7
            elif cantidad_validos <= 90:
                periodos_recomendados = 14
            else:
                periodos_recomendados = 30

            st.code("α = 2 / (N + 1)", language=None)
            ajustes_tendencia["periodos_ewma"] = st.number_input(
                "N · períodos",
                min_value=2,
                max_value=90,
                value=periodos_recomendados,
                step=1,
                key=f"periodos_ewma_{parametro}",
            )
        else:
            st.code(
                "pendiente = valor central de (y₂ − y₁) / (x₂ − x₁)",
                language=None,
            )
            st.caption("Theil–Sen no requiere constantes numéricas editables.")

            if parametro == "pH":
                st.code("Límite inferior ≤ pH ≤ Límite superior", language=None)
                ajustes_tendencia["ph_minimo"] = st.number_input(
                    "Límite inferior",
                    value=6.0,
                    step=0.1,
                    format="%.1f",
                    key="ph_limite_inferior",
                )
                ajustes_tendencia["ph_maximo"] = st.number_input(
                    "Límite superior",
                    value=8.0,
                    step=0.1,
                    format="%.1f",
                    key="ph_limite_superior",
                )
                if (
                    ajustes_tendencia["ph_minimo"]
                    >= ajustes_tendencia["ph_maximo"]
                ):
                    st.error("El límite inferior debe ser menor que el superior.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Registros", len(datos_filtrados))
    col2.metric("Promedio", f"{datos_filtrados['Valor'].mean():.2f} {unidad}".strip())
    col3.metric(
        "Último valor",
        f"{datos_filtrados['Valor'].iloc[-1]:.2f} {unidad}".strip(),
    )

    fecha_inicio = datos_filtrados["Fecha"].min().normalize()
    fecha_fin = datos_filtrados["Fecha"].max().normalize()
    dias = pd.date_range(fecha_inicio, fecha_fin, freq="D")

    # La importación conserva solo mediciones válidas. Para el gráfico se
    # reconstruyen todos los días del período y los faltantes se muestran en 0.
    datos_grafico = (
        pd.DataFrame({"Fecha": dias})
        .merge(
            datos_filtrados[["Fecha", "Valor"]],
            on="Fecha",
            how="left",
        )
    )
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
        fig = px.line(datos_grafico, markers=True, **opciones)

    aplicar_estilo_premium(fig, tipo_grafico, parametro, unidad)

    if mostrar_tendencia:
        metodo_tendencia = agregar_tendencia(
            fig,
            datos_filtrados,
            parametro,
            unidad,
            ajustes_tendencia,
        )
        st.sidebar.caption(f"Tendencia automática: {metodo_tendencia}.")

    margen_lateral = pd.Timedelta(hours=12)
    dias_semana = ("L", "M", "M", "J", "V", "S", "D")
    azul_fin_semana = "#4F92BD"
    etiquetas_dias = [
        (
            f"<span style='color:{azul_fin_semana}'><b>{dia.day}<br>"
            f"{dias_semana[dia.weekday()]}</b></span>"
            if dia.weekday() >= 5
            else f"{dia.day}<br>{dias_semana[dia.weekday()]}"
        )
        for dia in dias
    ]

    fig.update_xaxes(
        range=[
            fecha_inicio - margen_lateral,
            fecha_fin + margen_lateral,
        ],
        tickmode="array",
        tickvals=dias,
        ticktext=etiquetas_dias,
        tickangle=0,
        fixedrange=True,
        automargin=True,
    )
    fig.update_yaxes(fixedrange=True)

    with st.container(border=True):
        if len(dias) > 31:
            mostrar_grafico_desplazable(fig, len(dias))
        else:
            st.plotly_chart(
                fig,
                width="stretch",
                config=CONFIGURACION_GRAFICO,
                theme="streamlit",
            )

    st.subheader("Registros mostrados")
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
