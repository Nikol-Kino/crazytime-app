# ======================================================================
# CRAZYTIME PRO – VERSIONE DEFINITIVA
# Multipuntata + Statistiche + Classifiche + Alerts + HUD + Extra
# ======================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="CrazyTime PRO Ultimate", layout="wide")

# ---------------------- STILE DARK ----------------------
st.markdown("""
<style>
body {background-color:#0e0e0e;}
div.stButton>button {
    background-color:#222; color:white;
    border-radius:8px; border:1px solid #444;
}
.sidebar .sidebar-content {
    background-color:#121212;
}
</style>
""", unsafe_allow_html=True)

# ---------------------- SESSIONE ----------------------
if "spins" not in st.session_state:
    st.session_state.spins = []

# ----------------- BASE MULTIPLIERS -----------------
BASE_MULT = {
    '1': 1,
    '2': 2,
    '5': 5,
    '10': 10,
    'Coin': 2,
    'Cash Hunt': 2,
    'Pachinko': 2,
    'CrazyTime': 2
}

# ---------------------- SIDEBAR HUD ----------------------
st.sidebar.header("🎰 HUD — Casino Live")
st.sidebar.write("Statistiche in tempo reale mentre inserisci gli spin.")

if len(st.session_state.spins) > 0:
    total_spins = len(st.session_state.spins)
    st.sidebar.metric("Totale Spins", total_spins)

    # percentuali uscita
    results_list = [s["result"] for s in st.session_state.spins]
    df_count = pd.Series(results_list).value_counts(normalize=True) * 100
    for key, value in df_count.items():
        st.sidebar.write(f"• **{key}** → {value:.1f}%")

# ---------------------- FORM LARGO ----------------------
st.title("🎰 CRAZYTIME PRO — Modalità COMPLETA")

st.header("➕ Aggiungi Spin")

with st.form("add_spin", clear_on_submit=True):

    result = st.selectbox("Risultato", list(BASE_MULT.keys()))
    
    multiplier = st.number_input("Moltiplicatore Extra", min_value=1.0, value=1.0, step=1.0)

    st.markdown("### 💸 Puntate multipla")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        stake_1  = st.number_input("Puntata 1", min_value=0.0, value=0.0)
        stake_5  = st.number_input("Puntata 5", min_value=0.0, value=0.0)

    with c2:
        stake_2  = st.number_input("Puntata 2", min_value=0.0, value=0.0)
        stake_10 = st.number_input("Puntata 10", min_value=0.0, value=0.0)

    with c3:
        stake_coin  = st.number_input("Puntata Coin Flip", min_value=0.0, value=0.0)
        stake_cash  = st.number_input("Puntata Cash Hunt", min_value=0.0, value=0.0)

    with c4:
        stake_pach  = st.number_input("Puntata Pachinko", min_value=0.0, value=0.0)
        stake_ctime = st.number_input("Puntata CrazyTime", min_value=0.0, value=0.0)

    submit = st.form_submit_button("Aggiungi Spin")

    if submit:

        bets = {
            "1": stake_1,
            "2": stake_2,
            "5": stake_5,
            "10": stake_10,
            "Coin": stake_coin,
            "Cash Hunt": stake_cash,
            "Pachinko": stake_pach,
            "CrazyTime": stake_ctime
        }

        st.session_state.spins.append({
            "timestamp": datetime.now(),
            "result": result,
            "multiplier": multiplier,
            "bets": bets
        })

        st.success("Spin aggiunto!")

# ---------------------- CALCOLI ----------------------
st.header("📊 Risultati")

if len(st.session_state.spins) == 0:
    st.info("Inserisci almeno uno spin.")
    st.stop()

rows = []
bankroll = 0

for idx, spin in enumerate(st.session_state.spins):

    result = spin["result"]
    extra_mult = spin["multiplier"]
    bets = spin["bets"]
    
    stake_winner = bets[result]
    base_m = BASE_MULT[result]
    total_mult = base_m * extra_mult

    returned = stake_winner * (total_mult + 1)
    total_bet = sum(bets.values())
    net = returned - total_bet
    bankroll += net

    rows.append([
        idx + 1, result, extra_mult, total_mult,
        total_bet, returned, net, bankroll
    ])

df = pd.DataFrame(rows, columns=[
    "Giro", "Risultato", "Moltiplicatore Extra", "Moltiplicatore Totale",
    "Totale Puntato", "Restituito", "Netto", "Bankroll"
])

# ---------------------- METRICHE ----------------------
c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Spin", len(df))
c2.metric("Tot. Puntato", f"€ {df['Totale Puntato'].sum():.2f}")
c3.metric("Tot. Vinto", f"€ {df['Restituito'].sum():.2f}")
c4.metric("Netto Finale", f"€ {df['Netto'].sum():.2f}")

roi = df["Netto"].sum() / df["Totale Puntato"].sum() * 100
c5.metric("ROI (%)", f"{roi:.1f}%")

# ---------------------- GRAFICO ----------------------
st.subheader("📈 Andamento Bankroll")
fig = px.line(df, x="Giro", y="Bankroll", template="plotly_dark")
fig.update_traces(line=dict(width=4))
st.plotly_chart(fig, use_container_width=True)

# ---------------------- CLASSIFICA VINCITE ----------------------
st.header("🏆 Classifica Vincite")

df_sorted = df.sort_values(by="Netto", ascending=False)
st.subheader("Top 10 Vincite")
st.dataframe(df_sorted.head(10), use_container_width=True)

# ---------------------- DISTANZA TRA VINCITE IMPORTANTI ----------------------
st.header("📏 Distanza tra Vincite Alte")

threshold = st.number_input("Soglia vincita importante (es. €10)", value=10.0)

bigwins = df[df["Netto"] >= threshold]

if len(bigwins) < 2:
    st.info("Servono almeno 2 vincite sopra la soglia.")
else:
    bigwins["Distanza"] = bigwins["Giro"].diff()
    st.dataframe(bigwins[["Giro", "Netto", "Distanza"]], use_container_width=True)

# ---------------------- DISTRIBUZIONE USCITE ----------------------
st.header("📊 Statistiche di uscita")

counts = df["Risultato"].value_counts()
st.bar_chart(counts)

# ---------------------- ALERT ----------------------
st.header("🚨 Alerts automatici")

if bankroll <= -50:
    st.error("⚠️ Stai perdendo più di €50!")
elif bankroll >= 50:
    st.success("🟢 Hai superato i €50 di profitto!")

# ---------------------- RESET ----------------------
if st.button("🗑️ Reset dati"):
    st.session_state.spins = []
    st.experimental_rerun()


