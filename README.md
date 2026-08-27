# Planta RILES

Dashboard operacional para visualizar datos de una planta de tratamiento de RILES. La aplicación está construida con Streamlit.

Puede ejecutarse localmente con SQLite o como aplicación multiusuario en Azure
App Service con PostgreSQL y planillas alojadas en SharePoint.

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
python tasks.py comprobar         # valida sintaxis y pruebas automatizadas
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

El importador procesa la hoja físico-química, transforma las columnas numéricas y genera:

```text
datos_generados/fisico_quimico.xlsx
```

## Ejecutar el dashboard

Con el entorno virtual activado:

```bash
python tasks.py dev
```

Streamlit abrirá el navegador. Si no lo hace, visita <http://localhost:8501>.

## Modo nube

El modo nube se activa únicamente con `RILSA_APP_ENV=cloud`. En ese modo:

- Microsoft Graph descarga las dos planillas desde SharePoint.
- PostgreSQL almacena las mediciones para todos los usuarios.
- Azure App Service ejecuta Streamlit y protege el acceso con Microsoft Entra.
- Un WebJob actualiza los datos cada hora.

Las variables necesarias están documentadas en `.env.example`. La guía completa
está en [`docs/AZURE_DEPLOYMENT.md`](docs/AZURE_DEPLOYMENT.md).

```bash
python tasks.py validar-config
python tasks.py sincronizar-nube
python tasks.py dev-nube
```

## Formato generado

El dashboard consume el archivo normalizado con estas columnas:

```text
Fecha | Area | Parametro | Valor | Unidad
```

## Estructura actual

```text
app.py                 Punto de entrada Streamlit
tasks.py               Atajos para desarrollo e importación
sincronizar_nube.py     SharePoint → PostgreSQL
startup.sh              Inicio de Azure App Service
importar.py            Importador físico-químico provisional
dashboards/            Vistas recuperadas por sección
funciones/             Carga, filtros y visualización
App_Data/               WebJob programado de Azure
datos/                 Planillas Excel de origen (no versionadas)
datos_generados/       Datos normalizados locales (no versionados)
```
