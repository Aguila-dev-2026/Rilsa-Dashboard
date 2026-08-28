import pandas as pd
import plotly.express as px
import streamlit as st

from funciones.cargar_datos import (
    cargar_catalogo_operacional,
    cargar_datos_operacionales,
)
from funciones.filtros import (
    filtrar_contexto_operacional,
    filtrar_por_parametro,
    seleccionar_rango_fecha,
)
from funciones.ui.tema import (
    COBRE,
    CONFIGURACION_GRAFICO,
    paleta_grafico,
    tema_nativo_oscuro,
)
from funciones.dominio.tendencias import PARAMETROS_ACUMULATIVOS
from funciones.graficos.render import (
    aplicar_estilo_premium,
    mostrar_grafico_desplazable,
    preparar_tabla_premium,
)
from funciones.graficos.bandas import (
    agregar_bandas,
    configurar_bandas,
    obtener_banda_normativa,
    obtener_limites_activos,
    resaltar_valores_fuera_de_rango,
)
from funciones.graficos.tendencias import (
    agregar_tendencia,
    calcular_tendencia,
    metodo_tendencia_recomendado,
    tipo_grafico_recomendado,
)


# Los acumulativos se suman por mes. Todos los demás parámetros activos
# se resumen mediante promedio mensual.


# Referencias NCh 1333 para uso de agua de riego. Boro se presenta con el
# valor conservador para cultivos sensibles; puede ajustarse según el cultivo.

























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
        marcas_eje_x = dias
        # Se muestra únicamente el número del día. El tooltip conserva la
        # fecha completa, por lo que no es necesario añadir letras o saltos
        # de línea al eje X.
        etiquetas_eje_x = [str(dia.day) for dia in dias]

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
