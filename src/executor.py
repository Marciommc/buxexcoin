import os
import ccxt
import datetime
from database import db

class Executor:
    def __init__(self):
        # Acesso seguro via variáveis de ambiente
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.secret_key = os.getenv("BINANCE_SECRET_KEY")
        self.sandbox_mode = os.getenv("SANDBOX_MODE", "true").lower() == "true"
        self.mode = "SANDBOX" if self.sandbox_mode else "REAL"
        
        # Iniciando conexão CCXT (mesmo no sandbox usamos pra ler saldo real e tickers)
        self.exchange = ccxt.binance({
            'apiKey': self.api_key,
            'secret': self.secret_key,
            'enableRateLimit': True,
        })
        
        # Testnet opcional
        if os.getenv("USE_TESTNET", "false").lower() == "true":
             self.exchange.set_sandbox_mode(True)
             
    def get_balance(self, coin: str = "USDT") -> float:
        """
        Consulta o saldo disponível de uma moeda na Binance.
        (Ou saldo virtual se em modo Sandbox).
        """
        if self.sandbox_mode:
            return db.get_virtual_balance()
            
        try:
            balance = self.exchange.fetch_balance()
            if coin in balance:
                return float(balance[coin]['free'])
            return 0.0
        except Exception as e:
            print(f"[Executor] Erro ao buscar saldo: {e}")
            return 0.0

    def get_current_price(self, symbol: str) -> float:
        """
        Retorna o ticker atual da exchange
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            print(f"[Executor] Erro na requisição de cotação de {symbol}: {e}")
            return 0.0

    def place_order(self, symbol: str, quantity: float, side: str, order_type: str = "market", price: float = None, risk_profile: dict = None) -> dict:
        """
        Envia uma ordem para a corretora ou para o arquivo de Sandbox.
        """
        print(f"[Executor] -> Enviando Ordem: {side.upper()} {quantity} {symbol} a {order_type} (Preço: {price})")
        
        # [MODO PAPER TRADING ATIVADO]
        if self.sandbox_mode:
            print("[Executor] 🎲 [SANDBOX MODE] Ordem processada localmente, nenhum dinheiro real será utilizado.")
            valor_da_ordem = quantity * price
            
            if side == "buy":
                # Verifica saldo virtual
                banca = db.get_virtual_balance()
                if banca < valor_da_ordem:
                     return {"status": "error", "message": "Saldo virtual insuficiente para a compra no Sandbox."}
                     
                nova_posicao = {
                    "id": str(datetime.datetime.now().timestamp()),
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "symbol": symbol,
                    "type": side.upper(),
                    "price": price,
                    "amount": quantity,
                    "mode": self.mode,
                    "valor_investido": valor_da_ordem,
                    "take_profit_alvo": risk_profile["take_profit_alvo"] if risk_profile else price * 1.05,
                    "stop_loss_inicial": risk_profile["stop_loss_inicial"] if risk_profile else price * 0.95,
                    "stop_loss_ativo": risk_profile["stop_loss_inicial"] if risk_profile else price * 0.95,
                    "trailing_ativacao": risk_profile["trailing_ativacao"] if risk_profile else price * 1.02,
                    "usa_trailing": risk_profile["usa_trailing"] if risk_profile else False,
                    "status": "OPEN"
                }
                db.insert_trade(nova_posicao)
                # Salva snapshot de balanço no momento da transação (SANDBOX)
                db.save_balance_history(datetime.datetime.now().strftime("%Y-%m-%d"), self.mode, db.get_virtual_balance())
                return {"status": "success", "info": "Posicao Virtual ABERTA", "order": nova_posicao}
            
            # Exceção de fallback pra venda
            return {"status": "success", "info": "sandbox bypass"}
        
        # --- [MODO REAL API] ---
        if not self.api_key or self.api_key.startswith("sua_chave"):
            print("[Executor] [Dry-Run] Ordem NÃO enviada pois as chaves não estão configuradas pra conta real.")
            return {"status": "success", "info": "dry-run order executed"}
            
        try:
            if order_type == "market":
                order = self.exchange.create_order(symbol, order_type, side, quantity)
            elif order_type == "limit":
                order = self.exchange.create_order(symbol, order_type, side, quantity, price)
            return {"status": "success", "order": order}
        except Exception as e:
            print(f"[Executor] Erro na execução de ordem: {e}")
            return {"status": "error", "message": str(e)}
