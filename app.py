import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ==============================================================================
# CONFIGURACIÓN DE LA PÁGINA (STREAMLIT)
# ==============================================================================
st.set_page_config(
    page_title="FoodShield - Simulación de Cadena de Frío",
    page_icon="❄️",
    layout="wide"
)

# Estilos personalizados: Paleta Cold Chain Frost
st.markdown("""
<style>
    /* Fondo y estructura estilo Cold Chain Frost */
    .stApp {
        background: linear-gradient(180deg, #f0f9ff 0%, #f8fafc 100%);
    }
    [data-testid="stSidebar"] {
        background-color: #e0f2fe !important;
        border-right: 1px solid #bae6fd;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0f2fe;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(2, 132, 199, 0.08);
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# MOTOR MATEMÁTICO Y BIOLÓGICO (BACKEND CALIBRADO)
# ==============================================================================

def calcular_temperatura(t_horas, t_amb, t_0, k_min):
    """
    Ley de Calentamiento/Enfriamiento de Newton:
    T(t) = T_amb + (T_0 - T_amb) * exp(-k * t_min)
    El parámetro k está dado en min^-1, por lo que el tiempo se evalúa en minutos.
    """
    t_min = t_horas * 60.0
    return t_amb + (t_0 - t_amb) * np.exp(-k_min * t_min)


def tiempo_duplicacion_salmonella(temp):
    """
    Calcula el tiempo de generación g(T) en horas para Salmonella spp.
    según la temperatura alcanzada en la carne de pollo:
    - T < 7°C: Crecimiento latente / inhibido (g -> inf).
    - 7°C a 12°C: Activación inicial lenta (g pasa de 2.5h a 1.2h).
    - 12°C a 20°C: Crecimiento moderado (g pasa de 1.2h a 0.6h / 36 min).
    - 20°C a 30°C: Crecimiento acelerado (g pasa de 36 min a 19 min / 0.32h).
    - 30°C a 45°C: Fase exponencial óptima (g alcanza ~15-18 min / 0.25h).
    - T > 45°C: Estrés térmico letal para la bacteria.
    """
    if temp < 7.0:
        return np.inf
    elif temp < 12.0:
        return 2.5 - (temp - 7.0) * (1.3 / 5.0)
    elif temp < 20.0:
        return 1.2 - (temp - 12.0) * (0.6 / 8.0)
    elif temp < 30.0:
        return 0.6 - (temp - 20.0) * (0.28 / 10.0)
    elif temp <= 45.0:
        return max(0.25, 0.32 - (temp - 30.0) * (0.07 / 15.0))
    else:
        return np.inf


def simular_crecimiento(t_total_horas, t_amb, t_0, k_min, n_0=10.0, pasos=250):
    """
    Simula dinámicamente la temperatura y la fisión binaria en el intervalo de tiempo.
    N(t) = N_0 * 2^n, donde n = sum(dt / g(T)).
    """
    tiempos = np.linspace(0, t_total_horas, pasos)
    dt = tiempos[1] - tiempos[0]

    temperaturas = calcular_temperatura(tiempos, t_amb, t_0, k_min)
    poblacion = np.zeros(pasos)
    poblacion[0] = n_0

    n_acumulado = 0.0
    for i in range(1, pasos):
        temp_actual = temperaturas[i]
        g = tiempo_duplicacion_salmonella(temp_actual)

        if np.isneginf(g) or np.isposinf(g):
            dn = 0.0
        else:
            dn = dt / g

        n_acumulado += dn
        poblacion[i] = n_0 * (2.0 ** n_acumulado)

    return tiempos, temperaturas, poblacion


# ==============================================================================
# INTERFAZ DE USUARIO (STREAMLIT UI - COLD CHAIN FROST)
# ==============================================================================

# Encabezado
st.title("❄️ FoodShield: Simulación de Cadena de Frío")
st.caption(
    "Modelo predictivo de bioseguridad alimentaria para transporte avícola en Ibagué, Tolima. "
    "Paleta: Cold Chain Frost • Nivel Académico: 10° Grado."
)
st.markdown("---")

# ----------------- BARRA LATERAL (SIDEBAR) -----------------
st.sidebar.header("⚙️ Parámetros de Simulación")

# 1. Deslizador de Temperatura Ambiente
t_amb = st.sidebar.slider(
    "Temperatura Ambiente ($T_{\\text{amb}}$ en °C):",
    min_value=20.0,
    max_value=35.0,
    value=28.0,
    step=0.5,
    help="Temperatura climática exterior típica en Ibagué."
)

# 2. Deslizador de Tiempo de Trayecto
t_viaje = st.sidebar.slider(
    "Tiempo de Trayecto ($t$ en horas):",
    min_value=0.5,
    max_value=4.0,
    value=2.0,
    step=0.5,
    help="Duración del viaje sin refrigeración activa (pasos de 0.5h)."
)

# 3. Menú Desplegable de Tipo de Empaque
opciones_empaque = {
    "Uninsulated Crate (k = 0.030)": 0.030,
    "Plastic Bag (k = 0.020)": 0.020,
    "Styrofoam Box (k = 0.010)": 0.010
}
empaque_sel = st.sidebar.selectbox(
    "Tipo de Empaque Térmico:",
    options=list(opciones_empaque.keys()),
    index=0,
    help="El coeficiente k representa la tasa de pérdida de frío del empaque."
)
k_val = opciones_empaque[empaque_sel]

# 4. Campo Numérico para Temperatura Inicial
t_0 = st.sidebar.number_input(
    "Temperatura Inicial de la Carne ($T_0$ en °C):",
    min_value=0.0,
    max_value=15.0,
    value=4.0,
    step=0.5,
    help="Temperatura de almacenamiento previo al despacho (meta: 4°C)."
)

# Constantes biológicas y normativas
N_0 = 10.0         # Carga inicial (CFU/g)
N_CRIT = 1000.0    # Umbral crítico legal INVIMA 2674/2013 (CFU/g)

# ----------------- CÁLCULOS -----------------
tiempos, temps, bacterias = simular_crecimiento(
    t_total_horas=t_viaje,
    t_amb=t_amb,
    t_0=t_0,
    k_min=k_val,
    n_0=N_0
)

temp_final = temps[-1]
cfu_final = bacterias[-1]

# ----------------- MÉTRICAS RÁPIDAS (KPIS) -----------------
m1, m2, m3, m4 = st.columns(4)
m1.metric("🌡️ Temp. Final", f"{temp_final:.1f} °C", f"+{temp_final - t_0:.1f} °C")
m2.metric("⏱️ Tiempo Viaje", f"{t_viaje:.1f} h", "Sin refrigerar")
m3.metric(
    "🧫 Salmonella spp.", 
    f"{cfu_final:,.0f} CFU/g", 
    f"{cfu_final - N_0:+,.0f} CFU/g",
    delta_color="inverse"
)
m4.metric("⚖️ Umbral INVIMA", f"{N_CRIT:,.0f} CFU/g", "Res. 2674/2013")

# ----------------- CUADRO DE ALERTA VISUAL -----------------
st.markdown("### 🚦 Diagnóstico Sanitario del Lote")
if cfu_final >= N_CRIT:
    exceso = ((cfu_final - N_CRIT) / N_CRIT) * 100
    st.error(
        f"🚨 **ALERTA SANITARIA: El producto supera el límite seguro de INVIMA.**\n\n"
        f"- Carga final detectada: **{cfu_final:,.0f} CFU/g** (Supera el límite legal por **+{exceso:,.1f}%**).\n"
        f"- Condición: El alimento perdió la cadena de frío, permitiendo la proliferación exponencial de patógenos.\n"
        f"- Acción: **Lote rechazado**. Prohibida su comercialización."
    )
else:
    margen_seguridad = ((N_CRIT - cfu_final) / N_CRIT) * 100
    st.success(
        f"✅ **PRODUCTO SEGURO**\n\n"
        f"- Carga final estimada: **{cfu_final:,.0f} CFU/g** (Por debajo del límite de {N_CRIT:,.0f} CFU/g).\n"
        f"- Margen de inocuidad: **{margen_seguridad:.1f}%** de seguridad restante.\n"
        f"- El empaque y tiempo de transporte mantuvieron la bacteria en rangos admisibles."
    )

st.markdown("---")

# ----------------- GRÁFICAS INTERACTIVAS -----------------
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("📈 Curva Térmica: Temperatura vs. Tiempo")
    fig_temp = go.Figure()
    
    fig_temp.add_trace(go.Scatter(
        x=tiempos,
        y=temps,
        mode="lines",
        name="Temp. Carne",
        line=dict(color="#f97316", width=3.5)
    ))
    
    # Línea ambiente
    fig_temp.add_hline(
        y=t_amb,
        line_dash="dot",
        line_color="#64748b",
        annotation_text=f"Ambiente ({t_amb}°C)",
        annotation_position="bottom right"
    )

    # Zona segura refrigeración
    fig_temp.add_hrect(
        y0=0, y1=7,
        fillcolor="#0284c7", opacity=0.08,
        line_width=0,
        annotation_text="Zona de Inhibición (<7°C)",
        annotation_position="top left"
    )
    
    fig_temp.update_layout(
        xaxis_title="Tiempo transcurrido (horas)",
        yaxis_title="Temperatura (°C)",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=40, r=20, t=30, b=40),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(240,249,255,0.6)"
    )
    st.plotly_chart(fig_temp, use_container_width=True)

with col_g2:
    st.subheader("🔬 Curva de Crecimiento: Salmonella spp. vs. Tiempo")
    fig_bact = go.Figure()
    
    color_linea = "#dc2626" if cfu_final >= N_CRIT else "#0284c7"
    
    fig_bact.add_trace(go.Scatter(
        x=tiempos,
        y=bacterias,
        mode="lines",
        name="CFU/g",
        line=dict(color=color_linea, width=3.5)
    ))
    
    # Línea horizontal crítica discontinua en 1,000 CFU/g
    fig_bact.add_hline(
        y=N_CRIT,
        line_dash="dash",
        line_color="#dc2626",
        line_width=2.5,
        annotation_text="Límite Legal INVIMA (1,000 CFU/g)",
        annotation_position="top left",
        annotation_font_color="#dc2626"
    )
    
    fig_bact.update_layout(
        xaxis_title="Tiempo transcurrido (horas)",
        yaxis_title="Carga Bacteriana (CFU/g)",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=40, r=20, t=30, b=40),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(240,249,255,0.6)"
    )
    st.plotly_chart(fig_bact, use_container_width=True)

# ----------------- FUNDAMENTO CIENTÍFICO -----------------
with st.expander("📖 Fundamento Científico y Validación Biológica (10° Grado)"):
    st.markdown(r"""
    ### 1. Ley de Enfriamiento/Calentamiento de Newton
    $$T(t) = T_{\text{amb}} + (T_0 - T_{\text{amb}}) \cdot e^{-kt}$$
    - **$k = 0.030\text{ min}^{-1}$ (Canastilla sin aislar):** Rápida penetración de calor del clima de Ibagué.
    - **$k = 0.020\text{ min}^{-1}$ (Bolsa plástica):** Resistencia térmica mínima.
    - **$k = 0.010\text{ min}^{-1}$ (Caja de icopor / Styrofoam):** Retarda sustancialmente la curva térmica.

    ### 2. Modelo de Fisión Binaria Calibrado
    $$N(t) = N_0 \cdot 2^n \quad \text{donde} \quad n = \sum \frac{\Delta t}{g(T)}$$
    - Por debajo de $7^\circ\text{C}$, el metabolismo de *Salmonella* está latente ($g \to \infty$).
    - Al subir la temperatura hacia $28^\circ\text{C}-35^\circ\text{C}$, el tiempo de duplicación $g(T)$ desciende drásticamente hasta $\approx 15-20\text{ minutos}$ en carne de pollo rica en sustrato.
    - **Resultado observable:** Un viaje superior a 2.5 - 3 horas sin empaque aislante en Ibagué supera con creces el límite de $1,000\text{ CFU/g}$, detonando la **Alerta Sanitaria**.
    """)
