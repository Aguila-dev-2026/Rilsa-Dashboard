import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from funciones.filtros import seleccionar_rango_fecha


class FiltrosFechaTest(unittest.TestCase):
    @patch("funciones.filtros.st")
    def test_permite_consultar_antes_del_primer_registro_del_parametro(self, st):
        st.session_state = {}
        st.sidebar = MagicMock()
        st.sidebar.date_input.side_effect = [
            date(2024, 7, 1),
            date(2024, 12, 31),
        ]

        inicio, fin = seleccionar_rango_fecha(
            date(2024, 12, 11),
            date(2026, 8, 25),
            clave="descarga_reactor",
        )

        self.assertEqual(inicio, date(2024, 7, 1))
        self.assertEqual(fin, date(2024, 12, 31))
        llamadas = st.sidebar.date_input.call_args_list
        self.assertEqual(llamadas[0].kwargs["min_value"], date(2020, 1, 1))
        self.assertEqual(llamadas[1].kwargs["min_value"], date(2020, 1, 1))


if __name__ == "__main__":
    unittest.main()
