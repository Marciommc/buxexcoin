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
        st.warning(f"Erro ao carregar lucro diário: {e}")
        return 0.0

def load_trades(mode: str):
    try:
        trades = db.get_all_trades(mode)
        if trades:
            df = pd.DataFrame(trades)
            df = df.rename(columns={
                "timestamp": "Data",
                "symbol": "Ativo",
                "amount": "Quantidade",
                "profit_brl": "P/L BRL",
                "type": "Lado",
                "status": "Status",
                "profit_pct": "P/L %"
            })
            return df
    except Exception as e:
        st.warning(f"Erro ao carregar trades: {e}")
    return pd.DataFrame()

def load_balance_history(mode: str):
    try:
        history = db.load_balance_history(mode)
        if history:
             return pd.DataFrame(history, columns=["Data", "Balanço"])
    except Exception as e:
        st.warning(f"Erro ao carregar histórico de balanço: {e}")
    return pd.DataFrame()

# --- HEADER ---
st.title("🤖 BuxexCoin | Monitor de Operações")
st.markdown("Dashboard Analítico do Motor Autônomo SSAG")

# Mostra caminho do banco para debug
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "buxex_data.db")
db_exists = os.path.exists(db_path)
if not db_exists:
    st.error(f"⚠️ Banco de dados não encontrado em: `{db_path}`. O robô ainda não gerou dados ou o volume não está montado corretamente.")
else:
    db_size_kb = os.path.getsize(db_path) / 1024
    st.caption(f"✅ Banco conectado: `{db_path}` ({db_size_kb:.1f} KB)")

st.divider()

# --- METRIC SUMMARY ---
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
    if "P/L BRL" in df_trades.columns:
         st.bar_chart(df_trades, x="Data", y="P/L BRL", color="Ativo")
else:
    st.info(f"Nenhum trade registrado no ambiente {modo_selecionado} ainda. O robô pode ainda estar inicializando ou aguardando oportunidades.")

st.divider()
st.caption(f"Última atualização: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    if st.button("🔄 Atualizar Dados"):
        st.rerun()
