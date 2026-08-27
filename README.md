# Planta RILES

Dashboard operacional para visualizar y analizar datos de una planta de
tratamiento de RILES. La interfaz está construida con Streamlit y presenta
indicadores, filtros por fecha, gráficos y tablas para los procesos
físico-químico y aeróbico, consumo de químicos y energía.

## Requisitos

- Python 3.11 o superior (probado con Python 3.14.4).

Las versiones de las bibliotecas de Python están fijadas en
`requirements.txt`.

## Instalación          

Ejecuta todos los comandos desde la raíz del proyecto, ya que la aplicación
utiliza rutas relativas para leer los archivos Excel.

En Linux o macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

En Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

En Ubuntu o Debian puede ser necesario instalar primero el soporte para
entornos virtuales:

```bash
sudo apt install python3-venv
```

## Datos e importadores

La aplicación lee los archivos normalizados que ya existen en
`datos_generados/`. Estos archivos se conservan como datos históricos para
que los dashboards actuales puedan seguir consultándose.

Los importadores de columnas están en reconstrucción desde cero. Por el
momento:

- No existe un mapeo automático entre las planillas de `datos/` y las
  columnas normalizadas.
- `importar.py` está reservado como futuro punto de entrada y todavía no
  ejecuta importaciones.
- El botón de actualización desde Excel está deshabilitado en la aplicación.

Las planillas originales pueden mantenerse en `datos/`, pero no se procesan
automáticamente hasta implementar y validar los nuevos importadores.

## Ejecución

Con el entorno virtual activado:

```bash
python -m streamlit run app.py
```

Streamlit abrirá el navegador automáticamente. Si no lo hace, visita
<http://localhost:8501>.

Para detener la aplicación, presiona `Ctrl+C` en la terminal.

## Secciones disponibles

- Dashboard general de datos operacionales.
- Proceso físico-químico.
- Proceso aeróbico.
- Consumo de químicos.
- Consumo y eficiencia energética.
- Indicadores operacionales consolidados.

Las opciones **Contenedores** y **Predicción** aparecen en el menú y tienen
módulos implementados, pero todavía no están conectadas al enrutamiento de
`app.py`; actualmente se muestran como secciones en desarrollo.

## Estructura principal

```text
app.py                 Punto de entrada de la aplicación Streamlit
importar.py            Punto de entrada reservado para los nuevos importadores
dashboards/            Vistas de cada sección del dashboard
funciones/             Carga, filtros, gráficos y esqueletos de importadores
datos/                 Libros Excel de origen
datos_generados/       Archivos normalizados consumidos por la aplicación
modelos/               Espacio para modelos analíticos
reportes/              Espacio para exportación de reportes
utilidades/            Utilidades generales
```

`main.py` es un análisis independiente anterior y no es el punto de entrada
del dashboard actual. Para utilizar la aplicación web debe ejecutarse
`app.py` mediante Streamlit.

## Problemas comunes

- **No existe un archivo en `datos_generados/`:** esa sección no podrá
  mostrarse hasta que se implemente su nuevo importador o se proporcione un
  archivo normalizado compatible.
- **El puerto 8501 está ocupado:** inicia la aplicación en otro puerto con
  `python -m streamlit run app.py --server.port 8502`.
