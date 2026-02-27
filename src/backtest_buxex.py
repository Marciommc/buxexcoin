import os
import pandas as pd
import pandas_ta as ta
from binance.client import Client
import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURAÇÕES INICIAIS ---
api_key = os.getenv("BINANCE_API_KEY", "")
api_secret = os.getenv("BINANCE_SECRET_KEY", "")

# Instanciando com proteção
if api_key.startswith("sua_") or not api_key:
    api_key, api_secret = "", "" # Binance aceita reqs publicas sem keys, mas avisaremos
    print("Aviso: Chaves da Binance não configuradas. Buscando Klines de forma anônima.")

client = Client(api_key, api_secret)

symbol = "BTCUSDT"
interval = Client.KLINE_INTERVAL_15MINUTE
banca_inicial_usd = 1000  # Exemplo: ~R$ 5.600,00
meta_diaria_brl = 150.00
usd_brl_quote = 5.60 # Cotação estimada

# --- 1. COLETA DE DADOS ---
print(f"BuxexCoin: Baixando dados de {symbol} dos ultimos 7 dias...")
klines = client.get_historical_klines(symbol, interval, "7 days ago UTC")
df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])

# Garantindo conversão de tipos
df['close'] = df['close'].astype(float)
df['high'] = df['high'].astype(float)
df['low'] = df['low'].astype(float)

# --- 2. INDICADORES (ESTRATÉGIA) ---
df['RSI'] = ta.rsi(df['close'], length=14)
df['EMA_FAST'] = ta.ema(df['close'], length=9)
df['EMA_SLOW'] = ta.ema(df['close'], length=21)

# --- 3. SIMULAÇÃO DE BACKTEST ---
balance = banca_inicial_usd
trades = 0
vitorias = 0

print(f"Iniciando Simulação com banca de ${banca_inicial_usd} ...")

# Simularemos o mercado candle a candle ignorando indices fora do range com - 5
for i in range(1, len(df) - 5):
    # Lógica de Compra (Exemplo: RSI < 35 e Preço acima da EMA 21 indicando oportunidade em pullbacks de tendência)
    if df['RSI'].iloc[i] < 35 and df['close'].iloc[i] > df['EMA_SLOW'].iloc[i]:
        entrada = df['close'].iloc[i]
        
        # Simulação de saída (Take Profit de 1% ou Stop Loss de 0.5%)
        tp = entrada * 1.01 
        sl = entrada * 0.995
        
        # Simulação basica: Verifica os proximos 5 candles se pegamos o TP ou SL
        max_futuro = df['high'].iloc[i+1:i+6].max()
        min_futuro = df['low'].iloc[i+1:i+6].min()
        
        # Critério Simplificado de Simulação (Num bot de verdade isso varia a cada minuto, aqui usamos o topo/fundo dos clusters proximos)
        if max_futuro >= tp:
            balance += (balance * 0.01) # Ganhou 1%
            vitorias += 1
            trades += 1
        elif min_futuro <= sl:
            balance -= (balance * 0.005) # Perdeu 0.5%
            trades += 1
            
# --- 4. RESULTADOS ---
lucro_total_usd = balance - banca_inicial_usd
lucro_total_brl = lucro_total_usd * usd_brl_quote
lucro_diario_medio = lucro_total_brl / 7

print("-" * 30)
print(f"RESULTADOS BUXEXCOIN (7 DIAS)")
print(f"Total de Trades Simulados: {trades}")
print(f"Taxa de Acerto (Win Rate): {(vitorias/trades)*100:.2f}%" if trades > 0 else "Nenhum Trade Ex:")
print(f"Lucro Total (Estimado): R$ {lucro_total_brl:.2f} / USD {lucro_total_usd:.2f}")
print(f"Média Diária: R$ {lucro_diario_medio:.2f}")
print("-" * 30)

if lucro_diario_medio >= meta_diaria_brl:
    print("✅ ESTRATÉGIA VALIDADA: Meta de R$ 100/200 atingida matematicamente!")
else:
    print("⚠️ ALERTA: Precisamos ajustar os indicadores (ou aumentar a banca) para bater a meta.")
