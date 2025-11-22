import streamlit as st
import pandas as pd
import plotly.express as px
import time
import random

st.set_page_config(layout="wide", page_title="Crazy Time Simulator Animato")

st.title("🎡 Crazy Time Simulator – Animazione Ruota PRO")

# ---------------------------
# 1. BUDGET / RICARICA
# ---------------------------
st.sidebar.header("💰 Ricarica Budget")
budget = st.sidebar.number_input("Carica il tuo budget iniziale (€)", min_value=0.0, step=1.0)
if "saldo" not in st.session_state:
    st.session_state.saldo = budget

if st.sidebar.button("Ricarica"):
    st.session_state.saldo = budget

st.sidebar.write(f"**Saldo attuale:** {st.session_state.saldo:.2f} €")

# ---------------------------
# 2. PANNELLO PUNTATE
# ---------------------------
st.header("🎯 Imposta le tue puntate")

col1, col2, col3, col4 = st.columns(4)
with col1:
    puntata_1 = st.number_input("Puntata su 1", min_value=0.0, step=0.1)
    puntata_coin = st.number_input("Puntata CoinFlip", min_value=0.0, step=0.1)
with col2:
    puntata_2 = st.number_input("Puntata su 2", min_value=0.0, step=0.1)
    puntata_pachinko = st.number_input("Puntata Pachinko", min_value=0.0, step=0.1)
with col3:
    puntata_5 = st.number_input("Puntata su 5", min_value=0.0, step=0.1)
    puntata_cashhunt = st.number_input("Puntata Cash Hunt", min_value=0.0, step=0.1)
with col4:
    puntata_10 = st.number_input("Puntata su 10", min_value=0.0, step=0.1)
    puntata_crazy = st.number_input("Puntata CrazyTime", min_value=0.0, step=0.1)

puntate = {
    "1": puntata_1, "2": puntata_2, "5": puntata_5, "10": puntata_10,
    "CoinFlip": puntata_coin, "Pachinko": puntata_pachinko,
    "CashHunt": puntata_cashhunt, "CrazyTime": puntata_crazy,
}

# ---------------------------
# 3. INPUT GIRO / MOLTIPLICATORE
# ---------------------------
st.header("🎡 Inserisci l’esito dello spin")
colA, colB = st.columns(2)
with colA:
    risultato_spin = st.selectbox("Risultato uscito:", list(puntate.keys()))
with colB:
    moltiplicatore = st.number_input("Moltiplicatore (se presente)", min_value=1, step=1)

# ---------------------------
# 4. COEFFICIENTI
# ---------------------------
coef = {"1":1, "2":2, "5":5, "10":10, "CoinFlip":1, "Pachinko":1, "CashHunt":1, "CrazyTime":1}

# ---------------------------
# 5. ANIMAZIONE RUOTA + CALCOLO
# ---------------------------
if st.button("Aggiungi giro 🎰"):
    totale_puntato = sum(puntate.values())
    st.session_state.saldo -= totale_puntato
    puntata_vincente = puntate[risultato_spin]
    vincita = puntata_vincente + (puntata_vincente * coef[risultato_spin] * moltiplicatore) if puntata_vincente > 0 else 0
    st.session_state.saldo += vincita

    # Animazione ruota
    placeholder = st.empty()
    opzioni_ruota = list(puntate.keys())*3  # ripetiamo per effetto rotazione
    random.shuffle(opzioni_ruota)
    for val in opzioni_ruota[:15]:
        placeholder.markdown(f"**🎡 Ruota: {val}**")
        time.sleep(0.1)
    placeholder.markdown(f"**🎉 Numero estratto: {risultato_spin}**")
    st.success(f"Vincita: {vincita:.2f} €")
    st.sidebar.write(f"**Saldo aggiornato:** {st.session_state.saldo:.2f} €")

    # Storico
    if "storico" not in st.session_state:
        st.session_state.storico = []
    st.session_state.storico.append({
        "Spin": len(st.session_state.storico)+1,
        "Risultato": risultato_spin,
        "Moltiplicatore": moltiplicatore,
        "Totale Puntato": totale_puntato,
        "Vincita": vincita,
        "Saldo Dopo Giro": st.session_state.saldo
    })

# ---------------------------
# 6. MOSTRA STORICO + GRAFICI + ROI + Percentuali + Alert
# ---------------------------
if "storico" in st.session_state and len(st.session_state.storico)>0:
    df = pd.DataFrame(st.session_state.storico)
    st.header("📊 Storico Giri")
    st.dataframe(df, use_container_width=True)

    # Elimina giro
    st.subheader("🗑️ Elimina un giro")
    spin_da_eliminare = st.number_input("Numero spin da eliminare:", min_value=1, max_value=len(df), step=1)
    if st.button("Elimina spin"):
        index = spin_da_eliminare-1
        st.session_state.storico.pop(index)
        saldo = 0
        for item in st.session_state.storico:
            saldo += item["Vincita"] - item["Totale Puntato"]
            item["Saldo Dopo Giro"] = saldo
        st.session_state.saldo = saldo
        st.experimental_rerun()

    # Grafico saldo
    st.subheader("📈 Andamento Saldo")
    fig = px.line(df, x="Spin", y="Saldo Dopo Giro", markers=True, title="Andamento Saldo")
    st.plotly_chart(fig, use_container_width=True)

    # Top vincite
    st.subheader("🏆 Top 5 Vincite")
    st.dataframe(df.sort_values(by="Vincita", ascending=False).head(5), use_container_width=True)

    # ROI
    roi = (df["Vincita"].sum() - df["Totale Puntato"].sum())/df["Totale Puntato"].sum()*100
    st.metric("ROI (%)", f"{roi:.2f}%")

    # Percentuali uscite
    st.subheader("📊 Percentuali di uscita dei numeri")
    counts = df["Risultato"].value_counts(normalize=True)*100
    st.bar_chart(counts)

    # Distanza tra vincite alte
    st.subheader("📏 Distanza tra vincite alte")
    soglia = st.number_input("Soglia vincita importante (€)", value=10.0)
    bigwins = df[df["Vincita"]>=soglia]
    if len(bigwins)>=2:
        bigwins["Distanza"] = bigwins["Spin"].diff()
        st.dataframe(bigwins[["Spin","Vincita","Distanza"]], use_container_width=True)
    else:
        st.info("Servono almeno 2 vincite sopra la soglia.")

    # Alerts automatici
    st.subheader("🚨 Alerts automatici")
    if st.session_state.saldo <= -50:
        st.error("⚠️ Stai perdendo più di €50!")
    elif st.session_state.saldo >= 50:
        st.success("🟢 Hai superato i €50 di profitto!")
else:
    st.info("Nessun giro registrato al momento.")
