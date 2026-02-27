import os
import requests
import pandas as pd
import pandas_ta as ta

class Analyzer:
    def __init__(self):
        self.cmc_api_key = os.getenv("CMC_API_KEY")
        self.headers_cmc = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.cmc_api_key,
        }

    def fetch_top_coins(self, limit: int = 10, min_volume: float = 1000000.0) -> list:
        """
        Busca do CoinMarketCap moedas com volume maior a $1M
        :param limit: Quantidade limite
        :param min_volume: Volume em USD
        :return: Lista de símbolos
        """
        print(f"[Analyzer] Buscando top {limit} criptomoedas com volume mínimo de ${min_volume}...")
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        parameters = {
            'start':'1',
            'limit':str(limit),
            'convert':'USD'
        }
        
        # Como o endpoint sem chave falhará, caso ocorra exceção voltamos moedas dummy
        try:
            if not self.cmc_api_key or self.cmc_api_key == "sua_chave_coinmarketcap":
                print("[Analyzer] Chave de CMC não configurada, retornando ['BTCUSDT']")
                return ['BTCUSDT']

            response = requests.get(url, headers=self.headers_cmc, params=parameters)
            data = response.json()
            symbols = []
            
            for coin in data.get('data', []):
                quote = coin['quote']['USD']
                if quote['volume_24h'] >= min_volume:
                    symbol = f"{coin['symbol']}USDT"
                    symbols.append(symbol)
                    
            return symbols
        except Exception as e:
            print(f"[Analyzer] Erro no CMC: {e}. Usando Default: BTCUSDT e ETHUSDT")
            return ['BTCUSDT', 'ETHUSDT']

    def analyze_4h_trend(self, df_4h: pd.DataFrame) -> dict:
        """
        Garante que só compramos se o preço atual estiver ACIMA da Média Móvel Exponencial (EMA) de 200 períodos do gráfico de 4h.
        Isso evita que o robô compre "facas caindo" em mercados de urso.
        """
        if df_4h.empty or len(df_4h) < 200:
            return {"signal": "hold", "reason": "Pouco histórico para EMA 200"}

        df_4h.ta.ema(length=200, append=True)
        last_row = df_4h.iloc[-1]
        
        ema200 = last_row['EMA_200']
        close_price = last_row['Close']
        
        if close_price > ema200:
            return {"signal": "approved", "reason": "Preço acima da EMA 200 (Tendência de Alta)"}
        else:
            return {"signal": "rejected", "reason": f"Preço (${close_price:.2f}) Abaixo da EMA 200 (${ema200:.2f})"}

    def analyze_trend(self, df: pd.DataFrame) -> dict:
        """
        Analisa a tendência usando médias móveis e RSI (via pandas-ta).
        Requer DataFrame com colunas OHLCV ('Date', 'Open', 'High', 'Low', 'Close', 'Volume')
        Aqui usamos a estratégia de Scalping padrão.
        """
        if df.empty or len(df) < 50:
            return {"signal": "hold", "reason": "Not enough data"}

        # Adiciona indicadores ao DataFrame
        df.ta.sma(length=20, append=True)
        df.ta.sma(length=50, append=True)
        df.ta.rsi(length=14, append=True)

        last_row = df.iloc[-1]
        
        sma20 = last_row['SMA_20']
        sma50 = last_row['SMA_50']
        rsi14 = last_row['RSI_14']
        close = last_row['Close']

        # Exemplo Simples de Estratégia de Decisão
        if sma20 > sma50 and rsi14 < 70 and close > sma20:
            return {"signal": "buy", "reason": "Sinal rápido de Compra (RSI ok, Preço alto)"}
        
        return {"signal": "hold", "reason": "Sem sinal claro"}
