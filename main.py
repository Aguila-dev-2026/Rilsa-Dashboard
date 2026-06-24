import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# =====================================
# CARGA DE DATOS
# =====================================

lab = pd.read_excel(
    "datos/Historial_laboratorio.xlsx",
    header=8
)

ing = pd.read_excel(
    "datos/Historial_ingresos.xlsx",
    header=8
)

# Eliminar columnas vacías
lab = lab.loc[:, ~lab.columns.str.contains("^Unnamed")]
ing = ing.loc[:, ~ing.columns.str.contains("^Unnamed")]

# =====================================
# LABORATORIO
# =====================================

lab["Fecha"] = pd.to_datetime(lab["Fecha"])

# Filtrar DQO
dqo = lab[
    lab["Análisis"]
    .astype(str)
    .str.contains("DQO", case=False, na=False)
]

# Convertir filas a columnas
dqo = dqo.pivot_table(
    index="Fecha",
    columns="Lugar",
    values="Resultado",
    aggfunc="mean"
)

dqo = dqo.sort_index()

# Eficiencia
dqo["Eficiencia_DQO"] = (
    (dqo["Afluente"] - dqo["Efluente"])
    / dqo["Afluente"]
) * 100

dqo["Eficiencia_DQO"] = dqo["Eficiencia_DQO"].round(1)

# =====================================
# INGRESOS
# =====================================

ing["Fecha"] = pd.to_datetime(
    ing["Fecha/Hora de Ingreso"]
).dt.date

ingresos_diarios = (
    ing.groupby("Fecha")
    .agg(
        Carga_Diaria_kg=("Carga Neta (kg)", "sum"),
        Camiones=("ID Registro", "count")
    )
    .reset_index()
)

ingresos_diarios["Fecha"] = pd.to_datetime(
    ingresos_diarios["Fecha"]
)

# =====================================
# UNIÓN
# =====================================

dashboard = pd.merge(
    dqo.reset_index(),
    ingresos_diarios,
    on="Fecha",
    how="left"
)

# =====================================
# RESUMEN
# =====================================

print("\nResumen general")
print(dashboard.head())

print("\nEstadísticas")
print(dashboard.describe())

# =====================================
# DASHBOARD
# =====================================

fig = make_subplots(
    rows=4,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.05,
    subplot_titles=(
        "DQO Afluente vs Efluente",
        "Eficiencia de Remoción",
        "Carga Diaria Recibida",
        "Cantidad de Camiones"
    )
)

# ----------------------------
# DQO
# ----------------------------

fig.add_trace(
    go.Scatter(
        x=dashboard["Fecha"],
        y=dashboard["Afluente"],
        mode="lines+markers",
        name="DQO Afluente"
    ),
    row=1,
    col=1
)

fig.add_trace(
    go.Scatter(
        x=dashboard["Fecha"],
        y=dashboard["Efluente"],
        mode="lines+markers",
        name="DQO Efluente"
    ),
    row=1,
    col=1
)

# ----------------------------
# EFICIENCIA
# ----------------------------

fig.add_trace(
    go.Scatter(
        x=dashboard["Fecha"],
        y=dashboard["Eficiencia_DQO"],
        mode="lines+markers",
        name="Eficiencia (%)"
    ),
    row=2,
    col=1
)

# ----------------------------
# CARGA DIARIA
# ----------------------------

fig.add_trace(
    go.Bar(
        x=dashboard["Fecha"],
        y=dashboard["Carga_Diaria_kg"],
        name="Carga diaria (kg)"
    ),
    row=3,
    col=1
)

# ----------------------------
# CAMIONES
# ----------------------------

fig.add_trace(
    go.Bar(
        x=dashboard["Fecha"],
        y=dashboard["Camiones"],
        name="Camiones"
    ),
    row=4,
    col=1
)

# =====================================
# FORMATO
# =====================================

fig.update_layout(
    height=1200,
    title="Dashboard Planta RILES",
    hovermode="x unified"
)

fig.update_xaxes(
    tickformat="%d-%m-%Y"
)

fig.show()

