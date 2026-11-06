# ❄️ FoodShield: Cold Chain & Food Safety Simulator

> Interactive research prototype developed for the **FoodShield** platform (Grade 10 Academic Deliverable).

Simulates temperature rise in fresh poultry meat transported without active refrigeration in the tropical climate of **Ibagué, Tolima**, and calculates bacterial proliferation of ***Salmonella spp.*** according to Colombian sanitary regulations (**INVIMA Resolution 2674 of 2013**).

🌐 **Live Web Application on GitHub Pages:** [https://mfgatos3.github.io/foodshield-simulator/](https://mfgatos3.github.io/foodshield-simulator/)

---

## 🚀 Key Features & Architecture

1. **Interactive Control Panel (Sidebar):**
   - **Ambient Temperature ($T_{\text{amb}}$):** 20°C to 35°C (default: 28°C).
   - **Travel Time ($t$):** 0.5 to 4.0 hours (0.5h step).
   - **Thermal Packaging Options:**
     - *Uninsulated Crate* ($k = 0.030\text{ min}^{-1}$)
     - *Plastic Bag* ($k = 0.020\text{ min}^{-1}$)
     - *Styrofoam Box* ($k = 0.010\text{ min}^{-1}$)
   - **Initial Meat Temperature ($T_0$):** 4°C.

2. **Mathematical & Biological Backend:**
   - **Newton's Law of Cooling/Heating:**
     $$T(t) = T_{\text{amb}} + (T_0 - T_{\text{amb}}) \cdot e^{-kt}$$
   - **Dynamic Binary Fission Growth:**
     $$N(t) = N_0 \cdot 2^n \quad \text{where} \quad n = \sum \frac{\Delta t}{g(T)}$$
   - **Initial Bacterial Load ($N_0$):** $10\text{ CFU/g}$.
   - **Legal Critical Safety Limit ($N_{\text{crit}}$):** $1,000\text{ CFU/g}$ (INVIMA Res. 2674/2013).

3. **Visual Outputs & Dashboard:**
   - **Chart 1:** Thermal curve of meat temperature vs. transit time, highlighting the safe refrigeration zone ($<7^\circ\text{C}$).
   - **Chart 2:** Bacterial growth curve with a dashed red line at $1,000\text{ CFU/g}$.
   - **Sanitary Diagnosis Alert:**
     - 🚨 **Red Alert:** `SANITARY ALERT: Product exceeds the safe INVIMA threshold` ($N(t) \ge 1,000$).
     - ✅ **Green Badge:** `SAFE PRODUCT` ($N(t) < 1,000$).
   - **Integrated Academic Argumentative Essay:** Complete 5-section formal policy and biothermal research paper on public health, distributive justice, and low-cost cold-chain interventions in Comuna 8 of Ibagué.

---

## 💻 Local Execution with Python (Streamlit)

To run the native Python application on your local machine:

```bash
# 1. Clone the repository
git clone https://github.com/mfgatos3/foodshield-simulator.git
cd foodshield-simulator

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch Streamlit
streamlit run app.py
```

---

## 📁 Repository Structure

```
foodshield-simulator/
├── app.py              # Native Python Streamlit application with Plotly
├── requirements.txt    # Python dependencies (streamlit, numpy, pandas, plotly)
├── index.html          # Interactive client application deployed on GitHub Pages
└── README.md           # Project documentation and research report
```

---

## 📜 Regulatory Standards & Citations
- **Ministry of Health and Social Protection / INVIMA:** *Resolution 2674 of 2013* - Sanitary requirements for the manufacturing, processing, packaging, storage, transportation, distribution, and commercialization of food products in Colombia.
