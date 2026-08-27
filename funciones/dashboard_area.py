import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from funciones.cargar_datos import cargar_datos_operacionales
from funciones.filtros import filtrar_por_fecha, filtrar_por_parametro


def mostrar_grafico_con_gesto_touchpad(fig):
    """Renderiza Plotly con desplazamiento temporal mediante dos dedos."""
    html = """
    <!doctype html>
    <html>
    <head>
      <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
      <style>
        html, body { margin: 0; padding: 0; overflow: hidden; }
        #grafico { width: 100%; height: 510px; }
      </style>
    </head>
    <body>
      <div id="grafico"></div>
      <script>
        const figura = FIGURA_JSON;
        const grafico = document.getElementById("grafico");

        Plotly.newPlot(grafico, figura.data, figura.layout, {
          displayModeBar: true,
          scrollZoom: true,
          responsive: true,
          modeBarButtonsToRemove: [
            "zoom2d", "select2d", "lasso2d", "autoScale2d"
          ]
        }).then(() => {
          grafico.addEventListener("wheel", (evento) => {
            // En un touchpad, el desplazamiento con dos dedos llega como
            // un evento wheel. El pellizco (ctrlKey) conserva el zoom.
            if (evento.ctrlKey) return;

            const ejeX = grafico._fullLayout.xaxis;
            const inicio = new Date(ejeX.range[0]).getTime();
            const fin = new Date(ejeX.range[1]).getTime();
            const delta = Math.abs(evento.deltaX) > 0
              ? evento.deltaX
              : evento.deltaY;

            if (!delta || !Number.isFinite(inicio) || !Number.isFinite(fin)) {
              return;
            }

            evento.preventDefault();
            const desplazamiento = delta * (fin - inicio) / grafico.clientWidth;
            Plotly.relayout(grafico, {
              "xaxis.range": [
                new Date(inicio + desplazamiento).toISOString(),
                new Date(fin + desplazamiento).toISOString()
              ]
            });
          }, { passive: false });
        });
      </script>
    </body>
    </html>
    """.replace("FIGURA_JSON", fig.to_json())

    components.html(html, height=520, scrolling=False)


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

    tipo_grafico = st.sidebar.selectbox(
        "Tipo de gráfico",
        ["Líneas", "Barras"],
        key="tipo_grafico",
    )

    datos_filtrados = datos_filtrados.sort_values("Fecha")
    parametro = datos_filtrados["Parametro"].iat[0]
    unidad = (
        datos_filtrados["Unidad"].dropna().iloc[0]
        if datos_filtrados["Unidad"].notna().any()
        else ""
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Registros", len(datos_filtrados))
    col2.metric("Promedio", f"{datos_filtrados['Valor'].mean():.2f} {unidad}".strip())
    col3.metric(
        "Último valor",
        f"{datos_filtrados['Valor'].iloc[-1]:.2f} {unidad}".strip(),
    )

    opciones = {
        "x": "Fecha",
        "y": "Valor",
        "template": "plotly_white",
        "title": f"{parametro} — evolución en el período seleccionado",
        "labels": {
            "Fecha": "Fecha",
            "Valor": f"Valor ({unidad})" if unidad else "Valor",
        },
    }

    if tipo_grafico == "Barras":
        fig = px.bar(datos_filtrados, **opciones)
        fig.update_traces(marker_color="#6d1f2b")
    else:
        fig = px.line(datos_filtrados, markers=True, **opciones)
        fig.update_traces(line_width=3, marker_size=7)

    fig.update_layout(
        hovermode="x unified",
        dragmode="pan",
        margin=dict(l=10, r=10, t=55, b=10),
    )
    fig.update_xaxes(fixedrange=False)
    fig.update_yaxes(fixedrange=True)

    st.caption(
        "Desliza con dos dedos sobre el gráfico para recorrer el tiempo. "
        "El pellizco y los botones de zoom solo modifican el eje X."
    )
    mostrar_grafico_con_gesto_touchpad(fig)

    st.subheader("Registros mostrados")
    st.dataframe(
        datos_filtrados.sort_values("Fecha", ascending=False),
        width="stretch",
        hide_index=True,
    )
