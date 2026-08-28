"""Páginas de las áreas operacionales."""

import streamlit as st


def mostrar(nombre_area: str, titulo: str, datos_disponibles: bool) -> None:
    if not datos_disponibles:
        st.header(titulo)
        st.info("Aún no hay datos sincronizados para esta sección.")
        return
    from funciones.dashboard_area import mostrar_dashboard_area

    mostrar_dashboard_area(nombre_area=nombre_area, titulo=titulo)
