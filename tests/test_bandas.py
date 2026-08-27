import ast
from pathlib import Path
import unittest


class BandasTests(unittest.TestCase):
    def test_bandas_y_tendencia_tienen_funciones_independientes(self):
        ruta = Path(__file__).resolve().parents[1] / "funciones" / "dashboard_area.py"
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        funciones = {
            nodo.name: ast.unparse(nodo)
            for nodo in arbol.body
            if isinstance(nodo, ast.FunctionDef)
        }

        self.assertNotIn("add_hrect", funciones["agregar_tendencia"])
        self.assertIn("add_hrect", funciones["agregar_bandas"])
        self.assertIn("#A12C32", funciones["agregar_bandas"])
        self.assertIn("number_input", funciones["configurar_bandas"])
        self.assertIn("Añadir banda inferior", funciones["configurar_bandas"])
        self.assertIn("Añadir banda superior", funciones["configurar_bandas"])
        self.assertIn("Mostrar bandas normativas", funciones["configurar_bandas"])


if __name__ == "__main__":
    unittest.main()
