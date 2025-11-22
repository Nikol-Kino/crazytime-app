import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title("🎡 Crazy Time Simulator – Versione Estesa")

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
# 2. PANNELLO PUNTATE (LARGO)
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
    "1": puntata_1,
    "2": puntata_2,
    "5": puntata_5,
    "10": puntata_10,
    "CoinFlip": puntata_coin,
    "Pachinko": puntata_pachinko,
    "CashHunt": puntata_cashhunt,
    "CrazyTime": puntata_crazy,
}

# ---------------------------
# 3. INPUT GIRO / MOLTIPLICATORE
# ---------------------------
st.header("🎡 Inserisci l’esito dello spin")

colA, colB = st.columns(2)

with colA:
    risultato_spin = st.selectbox("Risultato uscito:", 
        ["1", "2", "5", "10", "CoinFlip", "Pachinko", "CashHunt", "CrazyTime"]
    )

with colB:
    moltiplicatore = st.number_input("Moltiplicatore (se presente)", min_value=1, step=1)

# ---------------------------
# 4. TABELLA VINCITE STANDARD
# ---------------------------
coef = {
    "1": 1,
    "2": 2,
    "5": 5,
    "10": 10,
    "CoinFlip": 1,     # default, ma può ricevere moltiplicatori
    "Pachinko": 1,    # valori medi standard
    "CashHunt": 1,
    "CrazyTime": 1
}

# ---------------------------
# 5. CALCOLO
# ---------------------------
if st.button("Aggiungi giro 🎰"):
    puntata = puntate[risultato_spin]

    if puntata <= 0:
        st.error("Non hai puntato su questo risultato!")
    else:
        vincita_base = coef[risultato_spin]
        vincita = puntata + (puntata * vincita_base * moltiplicatore)

        st.success(f"Hai vinto **{vincita:.2f} €** su {risultato_spin}!")

        # Aggiorna saldo
        totale_puntato = sum(puntate.values())
        st.session_state.saldo -= totale_puntato
        st.session_state.saldo += vincita

        st.sidebar.write(f"**Saldo aggiornato:** {st.session_state.saldo:.2f} €")

        # Salvataggio storico
        if "storico" not in st.session_state:
            st.session_state.storico = []

        st.session_state.storico.append({
            "Spin": len(st.session_state.storico) + 1,
            "Risultato": risultato_spin,
            "Moltiplicatore": moltiplicatore,
            "Totale Puntato": totale_puntato,
            "Vincita": vincita,
            "Saldo Dopo Giro": st.session_state.saldo
        })

# ---------------------------
# 6. MOSTRA STORICO
# ---------------------------
st.header("📊 Storico Giri")

if "storico" in st.session_state and len(st.session_state.storico) > 0:
    df = pd.DataFrame(st.session_state.storico)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Nessun giro registrato al momento.")
