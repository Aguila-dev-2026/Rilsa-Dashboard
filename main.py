import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# 1. Leer y procesar archivo Excel
df = pd.read_excel("datos/laboratorio.xlsx")

# Convertir a datetime (dejamos el objeto datetime completo para que Plotly lo maneje mejor)
df["Fecha"] = pd.to_datetime(df["Fecha"])
df = df.sort_values("Fecha")

# Calcular eficiencia de remoción DQO
df["Eficiencia_DQO"] = ((df["DQO_Afluente"] - df["DQO_Efluente"]) / df["DQO_Afluente"]) * 100
df["Eficiencia_DQO"] = df["Eficiencia_DQO"].round(1)


# 2. Configuración del Dashboard (3 filas)
fig = make_subplots(
    rows=3,
    cols=1,
    shared_xaxes=True, # Comparte el eje X para que al hacer zoom en uno, se muevan todos
    vertical_spacing=0.08,
    subplot_titles=(
        "Evolución de DQO (Afluente vs Efluente)",
        "Tendencia de Eficiencia de Remoción",
        "Eficiencia Diaria por Muestreo"
    )
)

# --- Fila 1: Afluente vs Efluente (Juntos para comparar la caída) ---
fig.add_trace(
    go.Scatter(
        x=df["Fecha"], y=df["DQO_Afluente"],
        mode="lines+markers", name="DQO Afluente",
        line=dict(color="firebrick")
    ),
    row=1, col=1
)
fig.add_trace(
    go.Scatter(
        x=df["Fecha"], y=df["DQO_Efluente"],
        mode="lines+markers", name="DQO Efluente",
        line=dict(color="forestgreen")
    ),
    row=1, col=1
)
fig.update_yaxes(title_text="DQO (mg/L)", row=1, col=1)


# --- Fila 2: Eficiencia en Línea ---
fig.add_trace(
    go.Scatter(
        x=df["Fecha"], y=df["Eficiencia_DQO"],
        mode="lines+markers", name="Eficiencia (%)",
        line=dict(color="royalblue", dash="dash")
    ),
    row=2, col=1
)
fig.update_yaxes(title_text="Eficiencia (%)", row=2, col=1)


# --- Fila 3: Eficiencia Diaria en Barras ---
fig.add_trace(
    go.Bar(
        x=df["Fecha"], y=df["Eficiencia_DQO"],
        name="Eficiencia diaria",
        marker_color="lightskyblue"
    ),
    row=3, col=1
)
fig.update_yaxes(title_text="Eficiencia (%)", row=3, col=1)


# 3. Diseño y formato global
fig.update_layout(
    height=950,
    title=dict(
        text="<b>Panel de Control - Planta de RILES (DQO)</b>",
        font=dict(size=20)
    ),
    template="plotly_white", # Fondo blanco más limpio para reportes
    hovermode="x unified"    # Muestra los datos de todas las curvas al pasar el mouse
)

# Formato de fecha uniforme para todos los ejes X
fig.update_xaxes(tickformat="%d-%m-%y", dtick="D1") # Fuerza marcas diarias si hay pocos datos

fig.show()
