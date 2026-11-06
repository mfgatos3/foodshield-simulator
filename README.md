# 🍗 FoodShield: Simulador de Cadena de Frío e Inocuidad Alimentaria

> Prototipo interactivo desarrollado para la plataforma **FoodShield** (evaluación de nivel 10° grado).

Simula la elevación de temperatura en carne de pollo fresca transportada sin refrigeración activa en el clima de **Ibagué, Tolima**, y calcula el crecimiento bacteriano de ***Salmonella spp.*** bajo la normativa colombiana (**Resolución INVIMA 2674 de 2013**).

🌐 **Demo en vivo en GitHub Pages:** [https://mfgatos3.github.io/foodshield-simulator/](https://mfgatos3.github.io/foodshield-simulator/)

---

## 🚀 Características y Arquitectura

1. **Panel de Control (Sidebar):**
   - **Temperatura Ambiente ($T_{\text{amb}}$):** Rango de 20°C a 35°C (predeterminado: 28°C).
   - **Tiempo de Trayecto ($t$):** Rango de 0.5 a 4.0 horas (pasos de 0.5 h).
   - **Tipo de Empaque:**
     - *Uninsulated Crate* ($k = 0.03\text{ min}^{-1}$)
     - *Plastic Bag* ($k = 0.02\text{ min}^{-1}$)
     - *Styrofoam Box* ($k = 0.01\text{ min}^{-1}$)
   - **Temperatura Inicial de la Carne ($T_0$):** 4°C.

2. **Modelación Matemática y Biológica (Backend):**
   - **Ley de Enfriamiento/Calentamiento de Newton:**
     $$T(t) = T_{\text{amb}} + (T_0 - T_{\text{amb}}) \cdot e^{-kt}$$
   - **Modelo de Fisión Binaria Bacteriana:**
     $$N(t) = N_0 \cdot 2^n \quad \text{donde} \quad n = \sum \frac{\Delta t}{g(T)}$$
   - **Carga bacteriana inicial ($N_0$):** $10\text{ CFU/g}$.
   - **Umbral crítico normativo ($N_{\text{crit}}$):** $1,000\text{ CFU/g}$ (Resolución INVIMA 2674/2013).

3. **Resultados Visuales:**
   - **Gráfica 1:** Curva térmica del producto vs. tiempo con referencia a la temperatura ambiente.
   - **Gráfica 2:** Curva de crecimiento de *Salmonella spp.* vs. tiempo con línea roja discontinua en $1,000\text{ CFU/g}$.
   - **Alerta Sanitaria:**
     - 🚨 **Rojo:** `ALERTA SANITARIA: El producto supera el límite seguro de INVIMA` ($N(t) \ge 1,000$).
     - ✅ **Verde:** `PRODUCTO SEGURO` ($N(t) < 1,000$).

---

## 💻 Ejecución Local con Streamlit (Python)

Si deseas ejecutar la aplicación nativa en tu entorno local de Python:

```bash
# 1. Clonar el repositorio
git clone https://github.com/mfgatos3/foodshield-simulator.git
cd foodshield-simulator

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Iniciar la aplicación Streamlit
streamlit run app.py
```

---

## 📁 Estructura del Repositorio

```
foodshield-simulator/
├── app.py              # Aplicación nativa en Python con Streamlit y Plotly
├── requirements.txt    # Dependencias de Python (streamlit, numpy, pandas, plotly)
├── index.html          # Interfaz web interactiva desplegada en GitHub Pages
└── README.md           # Documentación del proyecto
```

---

## 📜 Normativa y Referencias
- **Ministerio de Salud y Protección Social / INVIMA:** *Resolución 2674 de 2013* - Requisitos sanitarios que se deben cumplir para la fabricación, procesamiento, preparación, envase, almacenamiento, transporte, distribución y comercialización de alimentos en Colombia.
