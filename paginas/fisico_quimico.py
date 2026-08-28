"""Página físico-química del dashboard."""

import streamlit as st


def mostrar(datos_disponibles: bool) -> None:
    if not datos_disponibles:
        st.header("⚗️ Físico-químico")
        st.info("Aún no hay datos sincronizados en la fuente activa.")
        return
    from dashboards.fisico_quimico import mostrar_fisico_quimico

    mostrar_fisico_quimico()
