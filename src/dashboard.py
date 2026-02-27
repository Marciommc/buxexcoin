import streamlit as st
import pandas as pd
import os
from datetime import datetime
from database import db

st.set_page_config(page_title="BuxexCoin Dashboard", page_icon="🤖", layout="wide")

# Paths and Configs
META_DIARIA = float(os.getenv("META_DIARIA_USD", 35.0))

# --- HELPER FUNCTIONS ---
def load_daily_profit(mode: str):
    hoje_str = str(datetime.utcnow().date())
    try:
        return db.load_daily_profit(hoje_str, mode)
    except Exception as e:
        return 0.0

def load_trades(mode: str):
    try:
        trades = db.get_all_trades(mode)
        if trades:
            df = pd.DataFrame(trades)
            # Adaptando a visualização
            df = df.rename(columns={"timestamp": "Data", "symbol": "Ativo", "amount": "Quantidade", "profit_brl": "P/L BRL", "type": "Lado"})
            return df
    except Exception:
        pass
    return pd.DataFrame()

def load_balance_history(mode: str):
    try:
        history = db.load_balance_history(mode)
        if history:
             return pd.DataFrame(history, columns=["Data", "Balanço"])
    except Exception:
        pass
    return pd.DataFrame()

# --- HEADER ---
st.title("🤖 BuxexCoin | Monitor de Operações")
st.markdown("Dashboard Analítico do Motor Autônomo SSAG")
st.divider()

# --- METRIC SUMMARY ---
# Toggle
modo_selecionado = st.radio("Selecione o Ambiente de Visualização:", ["SANDBOX", "REAL"], horizontal=True)

col1, col2, col3 = st.columns(3)

lucro_atual = load_daily_profit(modo_selecionado)
progresso_meta = (lucro_atual / META_DIARIA) * 100 if META_DIARIA > 0 else 0

with col1:
    st.metric(label="Lucro Diário Atual (USD)", value=f"${lucro_atual:.2f}")

with col2:
    st.metric(label="Meta de Segurança Mínima", value=f"${META_DIARIA:.2f}")

with col3:
    status = "🔴 STANDBY" if lucro_atual >= META_DIARIA else "🟢 OPERANDO"
    st.metric(label="Status do Robô", value=status)

# Progress Bar
st.progress(min(progresso_meta / 100.0, 1.0), text=f"Progresso da Meta: {progresso_meta:.1f}%")

st.divider()

# --- EVOLUÇÃO DO CAPITAL ---
st.subheader(f"📈 Evolução do Capital - {modo_selecionado}")
df_balance = load_balance_history(modo_selecionado)
if not df_balance.empty:
     df_balance["Data"] = pd.to_datetime(df_balance["Data"])
     st.line_chart(df_balance, x="Data", y="Balanço")
else:
     st.info("Nenhum histórico de balanço diário consolidado para este modo.")

st.divider()

# --- TRADES HISTORY ---
st.subheader(f"📋 Histórico de Execuções ({modo_selecionado})")

df_trades = load_trades(modo_selecionado)

if not df_trades.empty:
    st.dataframe(df_trades.sort_values(by="Data", ascending=False), use_container_width=True)
    
    st.subheader(f"Gráfico de Performance {modo_selecionado} (P/L)")
    # Se houver P/L, exibe:
    if "P/L BRL" in df_trades.columns:
         st.bar_chart(df_trades, x="Data", y="P/L BRL", color="Ativo")
else:
    st.info(f"Nenhum trade registrado no ambiente {modo_selecionado} ainda!")

st.caption(f"Última atualização: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Add a refresh button
if st.button("Atualizar Dados"):
    st.rerun()
