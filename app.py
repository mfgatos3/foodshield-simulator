import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ==============================================================================
# PAGE CONFIGURATION (STREAMLIT)
# ==============================================================================
st.set_page_config(
    page_title="FoodShield - Cold Chain Simulation",
    page_icon="❄️",
    layout="wide"
)

# Custom styles: Cold Chain Frost Palette
st.markdown("""
<style>
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
# MATHEMATICAL AND BIOLOGICAL MODEL (BACKEND)
# ==============================================================================

def calculate_temperature(t_hours, t_amb, t_0, k_min):
    """
    Newton's Law of Cooling/Heating:
    T(t) = T_amb + (T_0 - T_amb) * exp(-k * t_min)
    Parameter k is given in min^-1; time is converted to minutes.
    """
    t_min = t_hours * 60.0
    return t_amb + (t_0 - t_amb) * np.exp(-k_min * t_min)


def salmonella_doubling_time(temp):
    """
    Calculates doubling time g(T) in hours for Salmonella spp.
    based on the meat temperature reached:
    - T < 7°C: Inactive / safe cold storage (g -> inf).
    - 7°C to 12°C: Slow initial growth (g decreases from 2.5h to 1.2h).
    - 12°C to 20°C: Moderate growth (g decreases from 1.2h to 0.6h / 36 min).
    - 20°C to 30°C: Accelerated growth (g decreases from 36 min to 19 min / 0.32h).
    - 30°C to 45°C: Optimal exponential phase (g reaches ~15-18 min / 0.25h).
    - T > 45°C: Thermal inactivation and stress (g -> inf).
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


def simulate_growth(t_total_hours, t_amb, t_0, k_min, n_0=10.0, steps=250):
    """
    Simulates temperature and continuous binary fission over the time interval.
    N(t) = N_0 * 2^n, where n = sum(dt / g(T)).
    """
    times = np.linspace(0, t_total_hours, steps)
    dt = times[1] - times[0]

    temperatures = calculate_temperature(times, t_amb, t_0, k_min)
    population = np.zeros(steps)
    population[0] = n_0

    n_cumulative = 0.0
    for i in range(1, steps):
        temp_current = temperatures[i]
        g = salmonella_doubling_time(temp_current)

        if np.isneginf(g) or np.isposinf(g):
            dn = 0.0
        else:
            dn = dt / g

        n_cumulative += dn
        population[i] = n_0 * (2.0 ** n_cumulative)

    return times, temperatures, population


# ==============================================================================
# USER INTERFACE (STREAMLIT UI - COLD CHAIN FROST)
# ==============================================================================

# Header
st.title("❄️ FoodShield: Cold Chain Simulation")
st.caption(
    "Predictive food safety model for fresh poultry transport in Ibagué, Tolima. "
    "Cold Chain Frost Theme • Grade 10 Deliverable."
)
st.markdown("---")

# ----------------- SIDEBAR -----------------
st.sidebar.header("⚙️ Simulation Parameters")

# 1. Ambient Temperature Slider
t_amb = st.sidebar.slider(
    "Ambient Temperature ($T_{\\text{amb}}$ in °C):",
    min_value=20.0,
    max_value=35.0,
    value=28.0,
    step=0.5,
    help="Typical outdoor ambient temperature during transit in Ibagué."
)

# 2. Travel Time Slider
t_travel = st.sidebar.slider(
    "Travel Time ($t$ in hours):",
    min_value=0.5,
    max_value=4.0,
    value=2.0,
    step=0.5,
    help="Duration of transit without active refrigeration (0.5h steps)."
)

# 3. Packaging Type Selectbox
packaging_options = {
    "Uninsulated Crate (k = 0.030)": 0.030,
    "Plastic Bag (k = 0.020)": 0.020,
    "Styrofoam Box (k = 0.010)": 0.010
}
selected_pkg = st.sidebar.selectbox(
    "Thermal Packaging Type:",
    options=list(packaging_options.keys()),
    index=0,
    help="The k coefficient denotes heat transfer rate through the container."
)
k_val = packaging_options[selected_pkg]

# 4. Initial Meat Temperature Input
t_0 = st.sidebar.number_input(
    "Initial Meat Temperature ($T_0$ in °C):",
    min_value=0.0,
    max_value=15.0,
    value=4.0,
    step=0.5,
    help="Initial cold storage temperature prior to transit (target: 4°C)."
)

# Biological and regulatory constants
N_0 = 10.0         # Initial count (CFU/g)
N_CRIT = 1000.0    # INVIMA 2674/2013 legal safety threshold (CFU/g)

# ----------------- CALCULATIONS -----------------
times, temps, bacteria = simulate_growth(
    t_total_hours=t_travel,
    t_amb=t_amb,
    t_0=t_0,
    k_min=k_val,
    n_0=N_0
)

final_temp = temps[-1]
final_cfu = bacteria[-1]

# ----------------- KPI METRIC CARDS -----------------
m1, m2, m3, m4 = st.columns(4)
m1.metric("🌡️ Final Temp", f"{final_temp:.1f} °C", f"+{final_temp - t_0:.1f} °C")
m2.metric("⏱️ Travel Duration", f"{t_travel:.1f} h", "Unrefrigerated")
m3.metric(
    "🧫 Salmonella spp.", 
    f"{final_cfu:,.0f} CFU/g", 
    f"{final_cfu - N_0:+,.0f} CFU/g",
    delta_color="inverse"
)
m4.metric("⚖️ Legal Threshold", f"{N_CRIT:,.0f} CFU/g", "INVIMA Res. 2674")

# ----------------- SANITARY ALERT BOX -----------------
st.markdown("### 🚦 Batch Food Safety Diagnosis")
if final_cfu >= N_CRIT:
    excess = ((final_cfu - N_CRIT) / N_CRIT) * 100
    st.error(
        f"🚨 **SANITARY ALERT: Product exceeds the safe INVIMA threshold.**\n\n"
        f"- Final bacterial load: **{final_cfu:,.0f} CFU/g** (Exceeds legal limit by **+{excess:,.1f}%**).\n"
        f"- Condition: Cold chain was lost, allowing exponential proliferation of pathogens.\n"
        f"- Action: **Batch rejected**. Prohibited for commercial distribution or human consumption."
    )
else:
    safety_margin = ((N_CRIT - final_cfu) / N_CRIT) * 100
    st.success(
        f"✅ **SAFE PRODUCT**\n\n"
        f"- Final estimated load: **{final_cfu:,.0f} CFU/g** (Below legal threshold of {N_CRIT:,.0f} CFU/g).\n"
        f"- Safety margin: **{safety_margin:.1f}%** remaining safety cushion.\n"
        f"- Packaging and transit duration preserved meat safety within regulatory standards."
    )

st.markdown("---")

# ----------------- INTERACTIVE CHARTS -----------------
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("📈 Thermal Curve: Temperature vs. Time")
    fig_temp = go.Figure()
    
    fig_temp.add_trace(go.Scatter(
        x=times,
        y=temps,
        mode="lines",
        name="Meat Temp.",
        line=dict(color="#f97316", width=3.5)
    ))
    
    # Ambient reference line
    fig_temp.add_hline(
        y=t_amb,
        line_dash="dot",
        line_color="#64748b",
        annotation_text=f"Ambient ({t_amb}°C)",
        annotation_position="bottom right"
    )

    # Safe refrigeration zone
    fig_temp.add_hrect(
        y0=0, y1=7,
        fillcolor="#0284c7", opacity=0.08,
        line_width=0,
        annotation_text="Safe Dormancy Zone (<7°C)",
        annotation_position="top left"
    )
    
    fig_temp.update_layout(
        xaxis_title="Travel time (hours)",
        yaxis_title="Temperature (°C)",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=40, r=20, t=30, b=40),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(240,249,255,0.6)"
    )
    st.plotly_chart(fig_temp, use_container_width=True)

with col_g2:
    st.subheader("🔬 Salmonella spp. Growth vs. Time")
    fig_bact = go.Figure()
    
    line_color = "#dc2626" if final_cfu >= N_CRIT else "#0284c7"
    
    fig_bact.add_trace(go.Scatter(
        x=times,
        y=bacteria,
        mode="lines",
        name="CFU/g",
        line=dict(color=line_color, width=3.5)
    ))
    
    # Legal threshold dashed horizontal line
    fig_bact.add_hline(
        y=N_CRIT,
        line_dash="dash",
        line_color="#dc2626",
        line_width=2.5,
        annotation_text="INVIMA 2674 Legal Limit (1,000 CFU/g)",
        annotation_position="top left",
        annotation_font_color="#dc2626"
    )
    
    fig_bact.update_layout(
        xaxis_title="Travel time (hours)",
        yaxis_title="Bacterial Load (CFU/g)",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=40, r=20, t=30, b=40),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(240,249,255,0.6)"
    )
    st.plotly_chart(fig_bact, use_container_width=True)

# ----------------- SCIENTIFIC FOUNDATION -----------------
with st.expander("📖 Scientific Foundation & Biological Validation (Grade 10)"):
    st.markdown(r"""
    ### 1. Newton's Law of Cooling/Heating
    $$T(t) = T_{\text{amb}} + (T_0 - T_{\text{amb}}) \cdot e^{-kt}$$
    - **$k = 0.030\text{ min}^{-1}$ (Uninsulated Crate):** Rapid convective heat transfer under Ibagué outdoor temperatures.
    - **$k = 0.020\text{ min}^{-1}$ (Plastic Bag):** Minimal thermal protection.
    - **$k = 0.010\text{ min}^{-1}$ (Styrofoam Box):** Delays internal thermal rise by approximately $300\%$.

    ### 2. Dynamic Binary Fission Model
    $$N(t) = N_0 \cdot 2^n \quad \text{where} \quad n = \sum \frac{\Delta t}{g(T)}$$
    - Below $7^\circ\text{C}$, bacterial metabolism remains dormant ($g \to \infty$).
    - When internal temperature enters $28^\circ\text{C}-35^\circ\text{C}$, doubling time $g(T)$ drops to **15 to 20 minutes** in fresh poultry.
    - **Empirical result:** An unrefrigerated trip exceeding 2.5 - 3 hours in an open crate in Ibagué reliably exceeds the critical $1,000\text{ CFU/g}$ legal threshold.
    """)
