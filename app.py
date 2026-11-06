import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ==============================================================================
# CONFIGURACIÓN DE LA PÁGINA (STREAMLIT)
# ==============================================================================
st.set_page_config(
    page_title="FoodShield - Simulación de Cadena de Frío",
    page_icon="🍗",
    layout="wide"
)

# ==============================================================================
# MOTOR MATEMÁTICO Y BIOLÓGICO (BACKEND)
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
    según la temperatura alcanzada (modelo térmico calibrado):
    - T < 7°C: Crecimiento inhibido / fase de latencia prolongada (g -> inf).
    - 7°C a 15°C: Crecimiento muy lento (g decrece de 8h a 3h).
    - 15°C a 25°C: Crecimiento moderado (g decrece de 3h a 1.2h).
    - 25°C a 45°C: Zona óptima de crecimiento rápido (g mínimo ~0.42h = 25 min).
    - T > 45°C: Desnaturalización y estrés térmico (g -> inf).
    """
    if temp < 7.0:
        return np.inf
    elif temp < 15.0:
        return 8.0 - (temp - 7.0) * (5.0 / 8.0)
    elif temp < 25.0:
        return 3.0 - (temp - 15.0) * (1.8 / 10.0)
    elif temp <= 45.0:
        return max(0.42, 1.2 - (temp - 25.0) * (0.78 / 12.0))
    else:
        return np.inf


def simular_crecimiento(t_total_horas, t_amb, t_0, k_min, n_0=10.0, pasos=200):
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
# INTERFAZ DE USUARIO (STREAMLIT UI)
# ==============================================================================

# Encabezado
st.title("🍗 FoodShield: Simulación de Cadena de Frío")
st.caption(
    "Modelo predictivo de elevación térmica y crecimiento bacteriano de Salmonella spp. "
    "en transporte de pollo fresco en Ibagué, Tolima. (Evaluación Nivel 10° Grado)."
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
    "Uninsulated Crate (k = 0.03)": 0.03,
    "Plastic Bag (k = 0.02)": 0.02,
    "Styrofoam Box (k = 0.01)": 0.01
}
empaque_sel = st.sidebar.selectbox(
    "Tipo de Empaque:",
    options=list(opciones_empaque.keys()),
    index=0,
    help="Determina la constante de transferencia de calor k del material."
)
k_val = opciones_empaque[empaque_sel]

# 4. Campo Numérico para Temperatura Inicial
t_0 = st.sidebar.number_input(
    "Temperatura Inicial de la Carne ($T_0$ en °C):",
    min_value=0.0,
    max_value=15.0,
    value=4.0,
    step=0.5,
    help="Temperatura inicial de salida del centro de beneficio (idealmente 4°C)."
)

# Constantes fijas del problema
N_0 = 10.0         # Carga inicial (CFU/g)
N_CRIT = 1000.0    # Umbral crítico Resolución INVIMA 2674/2013 (CFU/g)

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
m1.metric("🌡️ Temp. Final Producto", f"{temp_final:.1f} °C", f"+{temp_final - t_0:.1f} °C")
m2.metric("⏱️ Tiempo de Viaje", f"{t_viaje:.1f} h")
m3.metric("🧫 Salmonella spp. Final", f"{cfu_final:,.0f} CFU/g")
m4.metric("⚖️ Umbral INVIMA", f"{N_CRIT:,.0f} CFU/g")

# ----------------- CUADRO DE ALERTA VISUAL -----------------
st.markdown("### 🚦 Diagnóstico Sanitario del Lote")
if cfu_final >= N_CRIT:
    st.error(
        f"🚨 **ALERTA SANITARIA: El producto supera el límite seguro de INVIMA.** "
        f"(Carga final: **{cfu_final:,.1f} CFU/g** ≥ {N_CRIT:,.0f} CFU/g). "
        f"Riesgo crítico de salmonelosis. No apto para consumo humano."
    )
else:
    margen_seguridad = ((N_CRIT - cfu_final) / N_CRIT) * 100
    st.success(
        f"✅ **PRODUCTO SEGURO:** La carne se encuentra dentro de los estándares "
        f"sanitarios de la Resolución INVIMA 2674/2013 "
        f"({cfu_final:,.1f} CFU/g < {N_CRIT:,.0f} CFU/g). Margen: {margen_seguridad:.1f}%."
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
        line=dict(color="#f97316", width=3)
    ))
    
    fig_temp.add_hline(
        y=t_amb,
        line_dash="dot",
        line_color="#64748b",
        annotation_text=f"Ambiente ({t_amb}°C)",
        annotation_position="bottom right"
    )
    
    fig_temp.update_layout(
        xaxis_title="Tiempo transcurrido (horas)",
        yaxis_title="Temperatura (°C)",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=40, r=20, t=30, b=40),
        height=380
    )
    st.plotly_chart(fig_temp, use_container_width=True)

with col_g2:
    st.subheader("🔬 Curva de Crecimiento: Salmonella spp. vs. Tiempo")
    fig_bact = go.Figure()
    
    color_linea = "#dc2626" if cfu_final >= N_CRIT else "#16a34a"
    
    fig_bact.add_trace(go.Scatter(
        x=tiempos,
        y=bacterias,
        mode="lines",
        name="CFU/g",
        line=dict(color=color_linea, width=3)
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
        height=380
    )
    st.plotly_chart(fig_bact, use_container_width=True)

# ----------------- FUNDAMENTO CIENTÍFICO -----------------
with st.expander("📖 Fundamento Científico y Fórmulas Matemáticas (10° Grado)"):
    st.markdown(r"""
    ### 1. Ley de Enfriamiento/Calentamiento de Newton
    $$T(t) = T_{\text{amb}} + (T_0 - T_{\text{amb}}) \cdot e^{-kt}$$
    - **$T_{\text{amb}}$**: Temperatura ambiente en Ibagué ($20^\circ\text{C} - 35^\circ\text{C}$).
    - **$T_0$**: Temperatura inicial refrigerada ($4^\circ\text{C}$).
    - **$k$**: Coeficiente de transferencia térmica según empaque:
      - Canastilla sin aislar (*Uninsulated Crate*): $k = 0.030\text{ min}^{-1}$
      - Bolsa plástica (*Plastic Bag*): $k = 0.020\text{ min}^{-1}$
      - Caja de icopor (*Styrofoam Box*): $k = 0.010\text{ min}^{-1}$

    ### 2. Modelo de Fisión Binaria
    $$N(t) = N_0 \cdot 2^n \quad \text{donde} \quad n = \frac{t}{g(T)}$$
    - **$N_0$**: Carga inicial ($10\text{ CFU/g}$).
    - **$g(T)$**: Tiempo de duplicación bacteriana, el cual depende dinámicamente de la temperatura del pollo:
      - $T < 7^\circ\text{C}$: Crecimiento latente / prácticamente nulo ($g \to \infty$).
      - $7^\circ\text{C} \le T \le 45^\circ\text{C}$: Zona de peligro alimentario donde el tiempo de duplicación decae progresivamente hasta $\approx 25\text{ minutos}$ en condiciones óptimas.

    ### 3. Marco Normativo Colombiano
    - **Resolución INVIMA 2674 de 2013**: Fija condiciones higiénico-sanitarias y umbrales microbiológicos estrictos ($N_{\text{crit}} = 1,000\text{ CFU/g}$) para la protección de la salud pública.
    """)
