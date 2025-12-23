import streamlit as st
import pandas as pd
import numpy as np
import gspread
from datetime import datetime
from google.oauth2 import service_account


# --- 0. CLOUD SYNC FUNCTION ---
def sync_to_google_sheets(zone, scope, ent_id, hens, cocks, water, feed, task, notes):
    try:
        # 1. Pull the credentials from Streamlit's Secret Vault
        creds_dict = st.secrets["gcp_service_account"]

        # 2. Setup the credentials from the secret dictionary
        credentials = service_account.Credentials.from_service_account_info(creds_dict)

        # 3. Authorize the client
        client = gspread.authorize(credentials)

        # 4. Open the sheet and append the data
        sheet = client.open("EthiCoAI_Master_Log").sheet1

        # Prepare timestamped row for the 10-column schema
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_row = [
            timestamp,
            zone,
            scope,
            ent_id,
            hens,
            cocks,
            water,
            feed,
            task,
            notes,
        ]

        sheet.append_row(data_row)
        return True
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return False


# --- 1. SYSTEM CONFIG & STYLING ---
st.set_page_config(page_title="EthiCoAI Master v36.0", layout="wide")

st.markdown(
    """
    <style>
    .main { background-color: #f8fafc; }
    div.stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
    .stMetric { background: white; padding: 12px; border-radius: 12px; border: 1px solid #e2e8f0; }
    .inv-card-normal { background: #ffffff; padding: 10px; border-radius: 8px; border-left: 5px solid #10b981; margin-bottom: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .inv-card-critical { background: #fef2f2; padding: 10px; border-radius: 8px; border-left: 5px solid #ef4444; margin-bottom: 8px; }
    .profile-box { background: #ffffff; padding: 25px; border-radius: 15px; border: 2px solid #f1f5f9; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
    .opex-container { background: #f1f5f9; padding: 15px; border-radius: 10px; border: 2px solid #cbd5e1; margin-top: 10px; }
    .opex-label { font-size: 0.85rem; color: #475569; font-weight: bold; margin-bottom: -2px; }
    .opex-value { font-size: 1.05rem; color: #1e293b; margin-bottom: 8px; border-bottom: 1px solid #e2e8f0; }
    .net-profit-box { font-size: 1.2rem; font-weight: bold; padding: 12px; border-radius: 8px; text-align: center; margin-top: 10px; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- 2. GLOBAL STATE INITIALIZATION ---
if "inventory" not in st.session_state:
    st.session_state.inventory = {
        "NitroBoost (L)": 45,
        "PhosBoost (L)": 22,
        "Root Serum (L)": 110,
        "Probiotics (kg)": 8.0,
        "Turmeric (kg)": 12.0,
        "Designer Eggs (qty)": 320,
        "Packed Serum Bottles": 45,
        "Clean Water (L)": 950,
    }

if "active_animal" not in st.session_state:
    st.session_state.active_animal = None
if "assigned_tasks" not in st.session_state:
    st.session_state.assigned_tasks = {}

EGG_DB = {
    "Extra Protein": ["💪", 18.5, 6.2, 520, 85, 12, "L-Leucine", "🔥 High"],
    "Maternal Care": ["🤰", 14.2, 5.8, 450, 70, 15, "Folate", "🟢 Stable"],
    "Superior Breed": ["🏆", 15.0, 6.0, 350, 65, 10, "Calcium", "🟡 Fair"],
    "Cognition Booster": ["🧠", 13.5, 5.5, 610, 90, 8, "DHA/EPA", "🚀 Trending"],
    "High Omega-3": ["🐟", 12.8, 6.5, 410, 60, 5, "Alpha-Linolenic", "🔥 High"],
    "Turmeric Immune": ["🧡", 14.0, 5.9, 390, 85, 20, "Curcumin", "🔥 High"],
    "Vigor Fertility": ["🌱", 14.5, 6.1, 410, 50, 14, "Zinc/Selenium", "🟢 Stable"],
    "Senior Friendly": ["👵", 13.0, 5.2, 280, 75, 18, "Glucosamine", "🟡 Fair"],
    "Orange Yolk": ["🟠", 12.5, 6.3, 360, 95, 22, "Carotenoids", "🚀 Trending"],
    "Diabetes Friendly": ["🩸", 13.2, 4.8, 375, 80, 10, "Chromium", "🔥 High"],
    "Light on Gut": ["😌", 11.8, 4.5, 240, 40, 5, "Prebiotics", "🟢 Stable"],
    "Standard Organic": ["🥚", 12.0, 5.5, 250, 30, 8, "Vitamin D", "🟢 Stable"],
}

if "farm_population" not in st.session_state:
    p_names = ["Jojo", "Tutu", "Zuzu", "Coco", "Lulu", "Mumu"]
    poultry_zones = {
        f"{k} Meadow": [
            {
                "id": f"P-{k[:3]}-{j}",
                "sex": "F",
                "name": p_names[j - 1],
                "weight": 2.1,
                "sensor": f"IOT-{j}",
            }
            for j in range(1, 6)
        ]
        + [
            {
                "id": f"P-{k[:3]}-C",
                "sex": "M",
                "name": "Chief",
                "weight": 3.4,
                "sensor": "IOT-0",
            }
        ]
        for k in EGG_DB.keys()
    }
    aqua_zones = [
        "Full Sun Exposure",
        "Controlled Shade",
        "Special Omega Feed",
        "Probiotic Pulse Tank",
        "Growth Control",
        "Reserve Tank",
    ]
    scampi_pop = {
        z: [
            {
                "id": f"S-{z[:2]}-{j}",
                "sex": "F",
                "name": f"Scamp_{j}",
                "weight": 0.05,
                "sensor": f"IOT-S{j}",
            }
            for j in range(1, 11)
        ]
        for z in aqua_zones
    }
    fish_pop = {
        z: [
            {
                "id": f"F-{z[:2]}-{j}",
                "sex": "F",
                "name": f"Finley_{j}",
                "weight": 0.8,
                "sensor": f"IOT-F{j}",
            }
            for j in range(1, 11)
        ]
        for z in aqua_zones
    }
    st.session_state.farm_population = {
        "Poultry": poultry_zones,
        "Scampi": scampi_pop,
        "Fish": fish_pop,
    }

# --- 3. LAYOUT DEFINITION (GLOBAL) ---
main_col, inv_col = st.columns([0.76, 0.24])

# --- 4. SIDEBAR LOGIC ---
with st.sidebar:
    st.header("🌍 Sanctuary Live Controls")
    species_choice = st.selectbox(
        "Active Production Line", ["Poultry", "Scampi", "Fish"]
    )

    st.subheader("🧬 Biological Sliders")
    turmeric_g = st.slider("Turmeric (g/kg)", 0, 20, 10)
    probiotics_v = st.slider("Probiotics (CFU/ml)", 0, 100, 50)
    high_prot_feed = st.slider("High-Protein (g)", 0, 50, 25)
    omega_supp = st.slider("Omega-3 (ml)", 0, 10, 5)
    stress_idx = st.slider("Stress Reduction Index", 0, 100, 85)
    longevity_mode = st.checkbox("Activate Longevity Formula")

    elec_kwh = 120 + (stress_idx * 1.8) + (50 if longevity_mode else 0)
    water_l = 750 + (high_prot_feed * 6.2)
    chem_units = (probiotics_v * 0.5) + (turmeric_g * 0.3)
    vet_costs = 2800 - (stress_idx * 22) + (1400 if longevity_mode else 0)
    daily_burn = (elec_kwh * 9.0) + (water_l * 0.7) + (chem_units * 45) + vet_costs
    daily_rev = (st.session_state.inventory["Designer Eggs (qty)"] * 0.15 * 25) + 600
    net_profit = daily_rev - daily_burn
    margin = (net_profit / daily_rev * 100) if daily_rev > 0 else 0

    st.markdown(
        f"""
    <div class='opex-container'>
        <h4 style='margin-top:0;'>⚡ Live Operational Costs</h4>
        <div class='opex-label'>Electricity Consumed:</div><div class='opex-value'>{elec_kwh:.1f} kWh</div>
        <div class='opex-label'>Water Utilized:</div><div class='opex-value'>{water_l:,.0f} L</div>
        <div class='opex-label'>Chemicals & Inputs:</div><div class='opex-value'>{chem_units:.1f} Units</div>
        <div class='opex-label'>Vet / Medical Checkups:</div><div class='opex-value'>₹{vet_costs:,.0f}</div>
        <div class='opex-label' style='color:#b91c1c;'>Total Daily Burn (OpEx):</div><div class='opex-value' style='color:#b91c1c; font-weight:bold;'>₹{daily_burn:,.0f}</div>
        <div class='net-profit-box' style='background:{"#dcfce7" if net_profit > 0 else "#fee2e2"}; color:{"#166534" if net_profit > 0 else "#991b1b"};'>
            Daily Net: ₹{net_profit:,.0f}<br><small>Margin: {margin:.1f}%</small>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# --- 5. MAIN CONTENT BLOCK ---
with main_col:
    mode = st.radio(
        "Navigation",
        [
            "🚜 Real-Time Farm Twin",
            "🏢 Supervisor's Office",
            "👷 Worker Task Force",
            "🥚 Designer Egg Boutique",
            "🧪 Precision Fertilizer Advisor",
            "🧠 Immune & Stress Analytics",
        ],
        horizontal=True,
    )

    if mode == "🚜 Real-Time Farm Twin":
        st.header(f"🚜 {species_choice} Digital Twin")
        zones = list(st.session_state.farm_population[species_choice].keys())
        selected_zone = st.selectbox("Select Active Zone", zones)
        cols = st.columns(6)
        for i, unit in enumerate(
            st.session_state.farm_population[species_choice][selected_zone]
        ):
            with cols[i % 6]:
                icon = (
                    "🐓"
                    if (species_choice == "Poultry" and unit["sex"] == "M")
                    else (
                        "🐔"
                        if species_choice == "Poultry"
                        else ("🦐" if species_choice == "Scampi" else "🐟")
                    )
                )
                st.markdown(
                    f"<div style='text-align:center; border:2px solid #cbd5e1; border-radius:10px; padding:10px; background:white;'><b>{unit['name']}</b><br><span style='font-size:30px'>{icon}</span></div>",
                    unsafe_allow_html=True,
                )
                if st.button("Open Profile", key=f"btn_{unit['id']}"):
                    st.session_state.active_animal = unit

        if st.session_state.active_animal:
            u = st.session_state.active_animal
            st.divider()
            st.markdown(
                f"<div class='profile-box'><h3>Health Profile: {u['name']}</h3>",
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns([1, 2])
            with c1:
                full_id = f"{selected_zone}_{u['name']}"
                st.write(f"**Entity ID:** `{full_id}`")
                st.write(f"**Zone:** {selected_zone}")
                st.write(f"**Species:** {species_choice}")
            with c2:
                task_choice = st.selectbox(
                    "Task Category",
                    [
                        "Medical Check",
                        "Routine Log",
                        "Feeding Adjustment",
                        "Vet Emergency",
                    ],
                )
                notes_input = st.text_area(
                    "Observations / Remarks", placeholder="Enter clinical notes..."
                )
                if st.button("🚀 Sync to Master Ledger"):
                    if notes_input:
                        success = sync_to_google_sheets(
                            zone=selected_zone,
                            scope=species_choice,
                            ent_id=full_id,
                            hens="N/A",
                            cocks="N/A",
                            water="Optimum",
                            feed=high_prot_feed,
                            task=task_choice,
                            notes=notes_input,
                        )
                        if success:
                            st.success(f"✅ Data for {u['name']} synced to Ledger!")
                            st.session_state.active_animal = None
                            st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    elif mode == "🏢 Supervisor's Office":
        st.header("🏢 Task Allocation")
        worker = st.selectbox("Select Staff", ["Arjun", "Meena", "Suresh"])
        tasks = st.multiselect(
            "Assign Duties",
            ["Feed Replenishment", "Tank Cleaning", "Egg Sorting", "Vet Triage"],
        )
        if st.button("Send to Field"):
            st.session_state.assigned_tasks[worker] = tasks
            st.success(f"Tasks pushed to {worker}'s dashboard.")

        st.divider()
        st.subheader("📋 Live Cloud Audit (Last 5 Logs)")
        if st.button("🔄 Refresh Cloud Data"):
            try:
                creds_dict = st.secrets["gcp_service_account"]
                credentials = service_account.Credentials.from_service_account_info(
                    creds_dict
                )
                client = gspread.authorize(credentials)
                sheet = client.open("EthiCoAI_Master_Log").sheet1
                data = sheet.get_all_records()
                if data:
                    df_cloud = pd.DataFrame(data)
                    st.table(df_cloud.tail(5)[::-1])
                else:
                    st.info("Cloud sheet is currently empty.")
            except Exception as e:
                st.error(f"Could not fetch Cloud data: {e}")

    elif mode == "👷 Worker Task Force":
        st.header("👷 Field Execution")
        who = st.selectbox("Worker Log-in", ["Arjun", "Meena", "Suresh"])
        my_tasks = st.session_state.assigned_tasks.get(who, ["General Patrol"])
        for t in my_tasks:
            st.checkbox(f"Done: {t}")
            st.file_uploader(f"Proof for {t}", key=f"file_{t}")
        st.divider()
        st.subheader("📦 Inventory Update")
        coll = st.number_input("Collected Designer Eggs", min_value=0, step=1)
        if st.button("Deposit to Vault & Sync to Cloud"):
            if coll > 0:
                st.session_state.inventory["Designer Eggs (qty)"] += coll
                success = sync_to_google_sheets(
                    zone="Inventory_Vault",
                    scope="Production",
                    ent_id=f"VAULT_{who}",
                    hens=coll,
                    cocks=0,
                    water="N/A",
                    feed="N/A",
                    task="Egg Collection",
                    notes=f"Deposited by {who} via Worker Dashboard",
                )
                if success:
                    st.success(f"✅ {coll} eggs added to vault and logged to Cloud.")
                else:
                    st.warning("⚠️ Inventory updated locally, but Cloud Sync failed.")
            else:
                st.error("Please enter a collection quantity.")

    elif mode == "🥚 Designer Egg Boutique":
        st.header("🥚 12-Product Scientific Boutique")
        for i in range(0, 12, 4):
            cols = st.columns(4)
            for j in range(4):
                name = list(EGG_DB.keys())[i + j]
                if cols[j].button(f"{EGG_DB[name][0]} {name}"):
                    st.session_state.egg_view = name
        if "egg_view" in st.session_state:
            v = EGG_DB[st.session_state.egg_view]
            st.divider()
            st.subheader(f"📊 {st.session_state.egg_view} Analysis")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Protein", f"{v[1]}g")
            c2.metric("Fat", f"{v[2]}g")
            c3.metric("Choline", f"{v[3]}mg")
            c4.metric("Antioxidants", f"{v[4]}%")
            st.write(f"**Special Component:** {v[6]} | **Market Status:** {v[7]}")

    elif mode == "🧪 Precision Fertilizer Advisor":
        st.header("🧪 Precision Nutrient Gap & Serum Advisor")
        acre = st.number_input("Land Size (Acres)", 1.0)
        st.markdown(
            """
        | Nutrient Component | Soil Req (mg/kg) | Provided | Status |
        | :--- | :--- | :--- | :--- |
        | **Nitrogen (N)** | 280 | 278 | ✅ Balanced |
        | **Phosphorus (P)** | 140 | 142 | ✅ Surplus |
        | **Potash (K)** | 190 | 188 | ✅ Balanced |
        | **Zinc/Boron (Zn/B)**| 15 | 16 | ✅ Met |
        """
        )
        st.divider()
        v1, v2, v3 = st.columns(3)
        v1.metric("NitroBoost (L)", f"{acre*22}")
        v2.metric("PhosBoost (L)", f"{acre*14}")
        v3.metric("Root Serum (L)", f"{acre*18}")

    elif mode == "🧠 Immune & Stress Analytics":
        st.header("🧠 High-Fidelity Biological Flux")
        t = np.linspace(0, 24, 100)
        imm = (
            60
            + (turmeric_g * 1.3)
            + (probiotics_v * 0.1)
            + (10 if longevity_mode else 0)
        )
        st_val = 40 - (stress_idx * 0.28)
        df = pd.DataFrame(
            {
                "Hour": t,
                "Immunity Index %": (np.sin(t / 4) * 5) + imm,
                "Stress Level (ng/ml)": (np.cos(t / 4) * 4) + st_val,
                "Locomotion Flux": (np.sin(t / 6) * 12) + 50 + (omega_supp * 1.5),
                "Feeding Rate": (np.sin(t / 3) * 15) + 60 + (high_prot_feed * 0.2),
                "Longevity Index": 80 + (10 if longevity_mode else 0),
            }
        ).set_index("Hour")
        col_y, col_chart = st.columns([0.05, 0.95])
        with col_y:
            st.markdown(
                "<div style='writing-mode: vertical-rl; text-orientation: mixed; height: 350px; font-weight: bold; font-size: 18px; color: #1e293b; padding-top: 50px; border-right: 2px solid #cbd5e1;'>BIOLOGICAL AMPLITUDE (%)</div>",
                unsafe_allow_html=True,
            )
        with col_chart:
            st.line_chart(df, height=450)
            st.markdown(
                "<div style='text-align: center; font-weight: bold; font-size: 18px; color: #1e293b; margin-top: -10px; border-top: 2px solid #cbd5e1; padding-top: 5px;'>24-HOUR CIRCADIAN CYCLE (TIME)</div>",
                unsafe_allow_html=True,
            )
        st.info(
            "💡 Traces represent real-time physiological response to bio-slider inputs."
        )

# --- 6. INVENTORY VAULT ---
with inv_col:
    st.markdown("### 📦 Inventory Vault")
    for item, qty in st.session_state.inventory.items():
        cls = "inv-card-critical" if qty < 20 else "inv-card-normal"
        st.markdown(
            f"<div class='{cls}'><small>{item}</small><br><strong>{qty}</strong></div>",
            unsafe_allow_html=True,
        )
        if st.button("➕", key=f"add_{item}"):
            st.session_state.inventory[item] += 1
            st.rerun()
    total_val = (st.session_state.inventory["Designer Eggs (qty)"] * 25) + (
        st.session_state.inventory["Packed Serum Bottles"] * 450
    )
    st.metric("Total Asset Value", f"₹{total_val:,}")
# run

# cd C:\Users\Shashank\Documents\python

# streamlit run ethico_demo_v5.py
