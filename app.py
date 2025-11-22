# app.py — CrazyTime PRO (tutte le funzioni A-E integrate)
# Requisiti: pip install streamlit pandas numpy plotly
# Esegui: streamlit run app.py

import streamlit as st
import pandas as pd
import numpy as np
import io, base64, json
import plotly.express as px
from datetime import datetime

# ---------------- Basic config ----------------
st.set_page_config(page_title="CrazyTime Ultimate", layout="wide")
st.title("🎰 CrazyTime — Ultimate Simulator (A–E)")

# ---------------- Dark CSS (small) ----------------
st.markdown("""
<style>
body {background-color: #0b0b0b; color: #ddd;}
section.main {background-color: #0b0b0b;}
div.stButton>button {background-color:#222; color:#fff; border-radius:6px;}
.stApp header {display:none;}
[data-testid="stMetricValue"] {color:#00ff88; font-weight:700;}
table.dataframe {color:#ddd;}
</style>
""", unsafe_allow_html=True)

# ---------------- Session state ----------------
if 'spins' not in st.session_state:
    st.session_state.spins = []  # list of dicts
if 'sessions' not in st.session_state:
    st.session_state.sessions = {}  # name -> list of spins (dicts)

# ---------------- Helpers ----------------
BASE_MULT = {'1':1, '2':2, '5':5, '10':10, 'Coin':2, 'Cash Hunt':2, 'Pachinko':2, 'CrazyTime':2}

def df_from_spins(spins):
    if not spins:
        return pd.DataFrame(columns=[
            'spin_index','timestamp','result','multiplier','stake',
            'base_multiplier','total_multiplier','returned','net','bankroll'
        ])
    df = pd.DataFrame(spins).copy()
    # ensure types & order
    df = df.reset_index(drop=True)
    df['spin_index'] = df.index + 1
    if 'timestamp' not in df.columns:
        df['timestamp'] = pd.NaT
    df['result'] = df['result'].astype(str)
    df['multiplier'] = df['multiplier'].astype(float)
    df['stake'] = df['stake'].astype(float)
    df['base_multiplier'] = df['result'].map(BASE_MULT).fillna(2).astype(float)
    df['total_multiplier'] = df['base_multiplier'] * df['multiplier']
    df['returned'] = df['stake'] * (df['total_multiplier'] + 1.0)
    df['net'] = df['returned'] - df['stake']
    df['bankroll'] = df['net'].cumsum()
    # reorder
    cols = ['spin_index','timestamp','result','multiplier','base_multiplier','total_multiplier','stake','returned','net','bankroll']
    return df[cols]

def download_csv(df, filename="crazytime_ledger.csv"):
    towrite = io.BytesIO()
    df.to_csv(towrite, index=False)
    towrite.seek(0)
    b64 = base64.b64encode(towrite.read()).decode()
    return f'data:file/csv;base64,{b64}', f'{filename}'

def download_json(data, filename="crazytime_session.json"):
    s = json.dumps(data, default=str).encode()
    b64 = base64.b64encode(s).decode()
    return f'data:application/json;base64,{b64}', filename

def compute_stats(df):
    stats = {}
    stats['total_spins'] = len(df)
    stats['total_staked'] = df['stake'].sum() if not df.empty else 0.0
    stats['total_returned'] = df['returned'].sum() if not df.empty else 0.0
    stats['net_total'] = df['net'].sum() if not df.empty else 0.0
    stats['roi_percent'] = (stats['total_returned'] / stats['total_staked'] - 1)*100 if stats['total_staked']>0 else None
    # counts per segment
    stats['counts'] = df['result'].value_counts().to_dict() if not df.empty else {}
    # average win (only positive nets)
    if not df.empty:
        wins = df[df['net']>0]['net']
        stats['avg_win'] = wins.mean() if not wins.empty else 0.0
        stats['max_win'] = wins.max() if not wins.empty else 0.0
        stats['avg_loss'] = df[df['net']<0]['net'].mean() if not df[df['net']<0].empty else 0.0
    else:
        stats.update({'avg_win':0.0,'max_win':0.0,'avg_loss':0.0})
    # volatility (std) of net
    stats['volatility'] = df['net'].std() if not df.empty else 0.0
    # max drawdown on bankroll
    if not df.empty:
        roll_max = df['bankroll'].cummax()
        drawdown = (df['bankroll'] - roll_max)
        stats['max_drawdown'] = drawdown.min()
    else:
        stats['max_drawdown'] = 0.0
    return stats

def top_wins_table(df, top_n=10):
    if df.empty:
        return pd.DataFrame(columns=['rank','vincita','giro'])
    # use 'returned' or 'net'? use 'returned' for total cash in, but top profits likely net. We'll show both.
    df2 = df.copy()
    df2['vincita_net'] = df2['net']
    df2 = df2.sort_values('vincita_net', ascending=False).reset_index(drop=True)
    top = df2.head(top_n)[['vincita_net','spin_index']].copy()
    top.insert(0, 'rank', top.index+1)
    top.columns = ['rank','vincita','giro']
    # compute distances
    top['distanza'] = top['giro'].diff().fillna(0).astype(int)
    top.loc[0,'distanza'] = np.nan
    return top

# ---------------- Sidebar: settings ----------------
st.sidebar.header("Impostazioni generali")
initial_budget = st.sidebar.number_input("Budget iniziale (€) (solo display)", min_value=0.0, value=60.0, step=1.0, format="%.2f")
alert_profit = st.sidebar.number_input("Alert: profitto >= (€)", min_value=0.0, value=100.0, step=1.0)
alert_loss = st.sidebar.number_input("Alert: perdita >= (€)", min_value=0.0, value=60.0, step=1.0)
top_n = st.sidebar.number_input("Quante top vincite mostrare", min_value=3, max_value=100, value=10, step=1)

st.sidebar.markdown("---")
st.sidebar.header("Salvataggio sessioni")
session_name = st.sidebar.text_input("Nome sessione per salvataggio", value=f"Session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
if st.sidebar.button("💾 Salva sessione corrente"):
    # save spins
    st.session_state.sessions[session_name] = list(st.session_state.spins)
    st.sidebar.success(f"Sessione '{session_name}' salvata ({len(st.session_state.spins)} spin).")

# list saved sessions
if st.session_state.sessions:
    sel = st.sidebar.selectbox("Carica sessione salvata", options=[""] + list(st.session_state.sessions.keys()))
    if sel:
        if st.sidebar.button("📂 Carica"):
            st.session_state.spins = list(st.session_state.sessions[sel])
            st.sidebar.success(f"Sessione '{sel}' caricata ({len(st.session_state.spins)} spin).")
    if st.sidebar.button("🗑️ Elimina tutte le sessioni"):
        st.session_state.sessions = {}
        st.sidebar.warning("Tutte le sessioni cancellate.")

st.sidebar.markdown("---")
st.sidebar.header("Import/Export")
uploaded_session = st.sidebar.file_uploader("Importa sessione JSON", type=['json'])
if uploaded_session is not None:
    try:
        js = json.load(uploaded_session)
        # expect dict name->spins or list of spins
        if isinstance(js, dict):
            # merge
            for k,v in js.items():
                st.session_state.sessions[k] = v
            st.sidebar.success("Sessione(i) importata correttamente.")
        elif isinstance(js, list):
            # put as unnamed
            st.session_state.spins = js
            st.sidebar.success("Lista di spin importata nella sessione corrente.")
        else:
            st.sidebar.error("Formato JSON non riconosciuto.")
    except Exception as e:
        st.sidebar.error("Errore import JSON: " + str(e))

if st.sidebar.button("📤 Esporta sessioni (JSON)"):
    data = st.session_state.sessions
    href, filename = download_json(data, filename="crazytime_sessions.json")
    st.sidebar.markdown(f"[⬇️ Scarica JSON]({href})", unsafe_allow_html=True)

# ---------------- Main UI ----------------
# Left: input add spin / csv / controls, Right: visual, stats
left, right = st.columns([1,2])

with left:
    st.subheader("➕ Inserisci spin")
    with st.form("spin_form", clear_on_submit=True):
        r1, r2, r3 = st.columns([2,2,2])
        with r1:
            result = st.selectbox("Risultato", options=['1','2','5','10','Coin','Cash Hunt','Pachinko','CrazyTime'])
        with r2:
            multiplier = st.number_input("Moltiplicatore (metti 1 se no)", min_value=1.0, value=1.0, step=1.0)
        with r3:
            stake = st.number_input("Puntata (€)", min_value=0.0, value=1.0, step=0.1)
        add = st.form_submit_button("Aggiungi spin")
    if add:
        st.session_state.spins.append({
            'timestamp': datetime.now().isoformat(),
            'result': result,
            'multiplier': float(multiplier),
            'stake': float(stake)
        })
        st.success("Spin aggiunto.")

    st.markdown("---")
    st.subheader("📥 Importa CSV o Aggiungi massa")
    uploaded = st.file_uploader("Carica CSV (cols: result, stake, multiplier (opt), timestamp (opt))", type=['csv'])
    if uploaded:
        try:
            df_up = pd.read_csv(uploaded)
            if 'result' not in df_up.columns:
                st.error("CSV deve avere la colonna 'result'.")
            else:
                if 'stake' not in df_up.columns:
                    df_up['stake'] = 1.0
                if 'multiplier' not in df_up.columns:
                    df_up['multiplier'] = 1.0
                for _, r in df_up.iterrows():
                    st.session_state.spins.append({
                        'timestamp': r.get('timestamp', pd.NaT),
                        'result': str(r['result']),
                        'multiplier': float(r['multiplier']),
                        'stake': float(r['stake'])
                    })
                st.success(f"Aggiunti {len(df_up)} spin.")
        except Exception as e:
            st.error("Errore CSV: " + str(e))

    st.markdown("---")
    st.subheader("Session controls")
    if st.button("🔄 Cancella spin corrente"):
        st.session_state.spins = []
        st.experimental_rerun()
    st.write("Salva / carica sessioni dalla sidebar.")
    st.markdown("---")
    st.subheader("Alerts (configura)")
    st.write(f"Alert profitto ≥ €{alert_profit}  — Alert perdita ≥ €{alert_loss}")
    st.markdown("Se il bankroll finale supera il profit réglato o scende oltre la perdita impostata verrà mostrato un avviso.")

with right:
    st.subheader("📊 Ledger e Dashboard")
    df = df_from_spins(st.session_state.spins)
    if df.empty:
        st.info("Nessun spin: aggiungi spin o importa CSV.")
    else:
        # summary & alerts
        stats = compute_stats(df)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Spin", stats['total_spins'])
        col2.metric("Totale puntato", f"€ {stats['total_staked']:.2f}")
        col3.metric("Totale restituito", f"€ {stats['total_returned']:.2f}")
        col4.metric("Netto", f"€ {stats['net_total']:.2f}", delta=f"{stats['roi_percent']:.2f}%" if stats['roi_percent'] is not None else "")

        # Alerts: compare final bankroll (bankroll last) to thresholds
        final_bankroll = df['bankroll'].iloc[-1]
        if final_bankroll >= alert_profit:
            st.success(f"🎉 ALERT: Bankroll finale ≥ {alert_profit}€ ({final_bankroll:.2f}€)")
        if -final_bankroll >= alert_loss or final_bankroll <= -abs(alert_loss):
            # negative bankroll threshold
            st.error(f"⚠️ ALERT: perdita ≥ {alert_loss}€ (bankroll {final_bankroll:.2f}€)")

        # plot bankroll
        st.markdown("**Andamento bankroll**")
        fig = px.line(df, x='spin_index', y='bankroll', title="Bankroll nel tempo", template="plotly_dark")
        fig.update_traces(line=dict(width=3, color="#00ff88"))
        st.plotly_chart(fig, use_container_width=True)

        # show ledger
        with st.expander("📄 Ledger dettagliato"):
            st.dataframe(df.style.format({"returned":"{:.2f}","net":"{:.2f}","bankroll":"{:.2f}"}))

        # Top wins table + distances
        st.markdown("**Top vincite (per net)**")
        topn = top_wins_table(df, top_n)
        st.table(topn)

        # Stats breakdown
        st.markdown("**Statistiche avanzate**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Avg vincita (quando positivo)", f"€ {stats['avg_win']:.2f}")
        c2.metric("Max vincita", f"€ {stats['max_win']:.2f}")
        c3.metric("Volatilità (std net)", f"€ {stats['volatility']:.2f}")
        st.write("Conteggi per segmento:", pd.Series(stats['counts']).rename("conteggi"))

        st.write(f"Max drawdown: € {stats['max_drawdown']:.2f}")

        # distances between top wins already in topn['distanza']

        # download ledger CSV
        href, fname = download_csv(df)
        st.markdown(f"[⬇️ Scarica ledger CSV]({href})", unsafe_allow_html=True)

        # export session JSON
        if st.button("📤 Esporta sessione (scarica JSON)"):
            hrefj, jname = download_json(st.session_state.spins, filename="session_export.json")
            st.markdown(f"[⬇️ Scarica JSON sessione]({hrefj})", unsafe_allow_html=True)

# ---------------- Footer - extras ----------------
st.markdown("---")
st.caption("CrazyTime Ultimate — Interfaccia locale. Usa dati solo per scopi dimostrativi. Non è un invito al gioco d'azzardo reale.")

