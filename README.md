# Planta RILES

Dashboard operacional para visualizar datos de una planta de tratamiento de RILES. La aplicación está construida con Streamlit.

## Estado de recuperación

Este repositorio hereda la estructura de una versión anterior. La recuperación se hará por secciones.

La primera sección activa es **Físico-químico**. Permite seleccionar un rango de fechas, elegir un único parámetro y visualizar su evolución.

## Requisitos

- Python 3.11 o superior.
- Las dependencias están fijadas en `requirements.txt`.

## Instalación

Ejecuta los comandos desde la raíz del proyecto.

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

También puedes instalar las dependencias con el atajo:

```bash
python tasks.py instalar
```

## Tareas rápidas

`tasks.py` ofrece atajos multiplataforma y usa el intérprete del entorno virtual activo:

```bash
python tasks.py dev               # abre el dashboard
python tasks.py actualizar        # importa ambas planillas y actualiza SQLite
python tasks.py importar-fisico   # importa sólo la planilla físico-química
python tasks.py importar-aerobico # importa sólo el análisis de planta
```

Para ver las tareas disponibles:

```bash
python tasks.py --help
```

## Importar datos físico-químicos

Guarda la planilla original en:

```text
datos/Planilla Procesos RILES.xlsx
```

Luego ejecuta:

```bash
python importar.py
```

El importador provisional detecta una hoja y una columna de fecha, transforma las columnas numéricas y genera:

```text
datos_generados/fisico_quimico.xlsx
```

La selección definitiva de hoja, encabezados y columnas a ignorar se ajustará al revisar la planilla real. También es posible indicar una hoja explícita:

```bash
python importar.py --hoja "Nombre exacto de la hoja"
```

## Ejecutar el dashboard

Con el entorno virtual activado:

```bash
python tasks.py dev
```

Streamlit abrirá el navegador. Si no lo hace, visita <http://localhost:8501>.

## Formato generado

El dashboard consume el archivo normalizado con estas columnas:

```text
Fecha | Area | Parametro | Valor | Unidad
```

## Estructura actual

```text
app.py                 Punto de entrada Streamlit
tasks.py               Atajos para desarrollo e importación
importar.py            Importador físico-químico provisional
dashboards/            Vistas recuperadas por sección
funciones/             Carga, filtros y visualización
datos/                 Planillas Excel de origen (no versionadas)
datos_generados/       Datos normalizados locales (no versionados)
```
