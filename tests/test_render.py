import unittest
from unittest.mock import patch

import plotly.graph_objects as go

from funciones.graficos.render import (
    aplicar_estilo_premium,
    calcular_ancho_minimo_grafico,
    mostrar_grafico_desplazable,
)


class RenderGraficoTest(unittest.TestCase):
    def test_ancho_crece_24_px_por_cada_intervalo_adicional(self):
        self.assertEqual(calcular_ancho_minimo_grafico(31), 820)
        self.assertEqual(calcular_ancho_minimo_grafico(32), 844)

    def test_conserva_configuracion_del_tooltip_unificado(self):
        figura = go.Figure(go.Scatter(x=["2026-08-28"], y=[7.2]))
        aplicar_estilo_premium(figura, "Líneas", "pH", "")

        self.assertEqual(figura.layout.hovermode, "x unified")
        self.assertEqual(figura.layout.xaxis.unifiedhovertitle.text, "\u200b")

    @patch("funciones.graficos.render.components.html")
    @patch("funciones.graficos.render.tema_nativo_oscuro", return_value=False)
    def test_html_conserva_ancho_minimo_y_crece_con_la_pagina(
        self,
        _tema,
        renderizar_html,
    ):
        figura = go.Figure(go.Scatter(x=list(range(31)), y=list(range(31))))
        mostrar_grafico_desplazable(figura, 31)

        html = renderizar_html.call_args.args[0]
        self.assertIn("width: max(100%, 820px)", html)
        self.assertIn("min-width: 820px", html)
        self.assertIn("window.parent.document", html)
        self.assertIn("window.Plotly.relayout", html)
        self.assertIn('"texto": "#FAFAFA"', html)
        self.assertIn('"texto_eje": "#C8CBD4"', html)


if __name__ == "__main__":
    unittest.main()
