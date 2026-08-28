"""Calendario de feriados utilizado por filtros y gráficos."""

from datetime import date


FERIADOS_CHILE_2026 = {
    date(2026, 1, 1): "Año Nuevo",
    date(2026, 4, 3): "Viernes Santo (Semana Santa)",
    date(2026, 4, 4): "Sábado Santo (Semana Santa)",
    date(2026, 5, 1): "Día Nacional del Trabajo",
    date(2026, 5, 21): "Día de las Glorias Navales",
    date(2026, 6, 21): "Día Nacional de los Pueblos Indígenas",
    date(2026, 6, 29): "San Pedro y San Pablo",
    date(2026, 7, 16): "Día de la Virgen del Carmen",
    date(2026, 8, 15): "Asunción de la Virgen",
}


def feriados_en_rango(fecha_inicio, fecha_fin):
    """Devuelve feriados del calendario que caen dentro del rango inclusivo."""
    inicio = fecha_inicio.date() if hasattr(fecha_inicio, "date") else fecha_inicio
    fin = fecha_fin.date() if hasattr(fecha_fin, "date") else fecha_fin
    return {
        fecha: nombre
        for fecha, nombre in FERIADOS_CHILE_2026.items()
        if inicio <= fecha <= fin
    }
