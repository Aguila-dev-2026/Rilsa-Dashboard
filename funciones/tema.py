import streamlit as st


TEMAS = {
    "light": {
        "fondo": "#F4F0E9",
        "panel": "#FFFDF8",
        "sidebar": "#ECE4DA",
        "texto": "#171514",
        "muted": "#756E67",
        "linea": "#D8CEC2",
        "sombra": "0 16px 42px rgba(72,18,26,0.08)",
        "control": "#FFFDF8",
        "halo": "rgba(179,111,61,0.08)",
    },
    "dark": {
        "fondo": "#0D0C0B",
        "panel": "#141210",
        "sidebar": "#100F0E",
        "texto": "#F4F0E9",
        "muted": "#AAA096",
        "linea": "#2C2824",
        "sombra": "0 20px 52px rgba(0,0,0,0.46)",
        "control": "#1A1715",
        "halo": "rgba(179,111,61,0.025)",
    },
}


def tema_oscuro() -> bool:
    return st.session_state.get("tema_visual", 0) == 1


def aplicar_tema(modo: str) -> None:
    # Dark conserva el aspecto nativo original de Streamlit.
    if modo == "dark":
        return

    tema = TEMAS[modo]
    st.markdown(
        f"""
        <style>
        :root {{
          color-scheme: {modo};
        }}

        [data-testid="stAppViewContainer"],
        .stApp {{
          background:
            radial-gradient(circle at 88% 4%, {tema["halo"]}, transparent 28rem),
            {tema["fondo"]};
          color: {tema["texto"]};
        }}

        [data-testid="stHeader"] {{
          background: transparent;
        }}

        [data-testid="stSidebar"] {{
          background:
            linear-gradient(180deg, rgba(109,31,43,0.06), transparent 16rem),
            {tema["sidebar"]};
          border-right: 1px solid {tema["linea"]};
        }}

        h1, h2, h3, h4, h5, h6,
        [data-testid="stMarkdownContainer"],
        [data-testid="stWidgetLabel"] {{
          color: {tema["texto"]};
        }}

        [data-testid="stCaptionContainer"],
        [data-testid="stMetricLabel"] {{
          color: {tema["muted"]};
        }}

        [data-testid="stMetric"] {{
          background: {tema["panel"]};
          border: 1px solid {tema["linea"]};
          border-radius: 16px;
          padding: 1rem 1.1rem;
          box-shadow: {tema["sombra"]};
        }}

        [data-testid="stVerticalBlockBorderWrapper"] {{
          background: {tema["panel"]};
          border-color: {tema["linea"]};
          border-radius: 18px;
          box-shadow: {tema["sombra"]};
        }}

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        [data-testid="stDateInput"] > div > div {{
          background-color: {tema["control"]};
          border-color: {tema["linea"]};
          color: {tema["texto"]};
        }}

        div[data-baseweb="select"] *,
        div[data-baseweb="input"] input {{
          color: {tema["texto"]};
        }}

        hr {{
          border-color: {tema["linea"]};
        }}

        .stButton > button[kind="primary"] {{
          background: linear-gradient(135deg, #6D1F2B, #48121A);
          border: 1px solid rgba(255,255,255,0.18);
          border-radius: 11px;
          box-shadow: 0 8px 22px rgba(72,18,26,0.24);
          color: #FFFDF8 !important;
          font-weight: 750;
        }}

        .stButton > button[kind="primary"] p,
        .stButton > button[kind="primary"] span {{
          color: #FFFDF8 !important;
          font-weight: 750;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def configurar_tema() -> str:
    try:
        modo = "dark" if st.context.theme.type == "dark" else "light"
    except (AttributeError, RuntimeError):
        modo = "light"

    st.session_state.tema_visual = 1 if modo == "dark" else 0
    aplicar_tema(modo)
    return modo
