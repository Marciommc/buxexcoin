import time
from analyzer import Analyzer
from executor import Executor
from risk_manager import RiskManager
from sentiment import SentimentAnalyzer
import pandas as pd
import datetime
from notifier import BuxexNotifier
from database import db

class BuxexBrain:
    def __init__(self, notifier=None):
        print("Iniciando Mente do Agente SSAG BuxexCoin...")
        
        # Se não injetarem o notificador, a gente inicializa um padrão local (silencioso na config atual)
        self.notifier = notifier if notifier else BuxexNotifier()
        
        self.analyzer = Analyzer()
        self.executor = Executor()
        self.risk_manager = RiskManager(notifier=self.notifier)
        self.sentiment = SentimentAnalyzer()

    def loop_decision(self):
        """
        Ciclo principal de vida do agente.
        1. [SANDBOX] Checa alvos de Posições Abertas 
        2. Avalia as moedas
        3. Analisa tendência
        4. Valida risco (TP/SL)
        5. Executa trade
        """
        # --- VERIFICAÇÃO DE SANDBOX E ALVOS VIRTUAIS ---
        if self.executor.sandbox_mode:
            print(f"\n[BuxexBrain] 🤖 VARRENDO POSIÇÕES ({self.executor.mode}) NO SQLITE...")
            posicoes_vivas = db.get_open_trades(self.executor.mode)
            
            for pos in posicoes_vivas:
                trade_id = pos["id"]
                sym = pos["symbol"]
                curr_price = self.executor.get_current_price(sym)
                
                if curr_price == 0:
                     continue
                
                qty = pos["amount"]
                entry = pos["price"]
                
                # Atualizando Trailing Stop localmente se aplicavel
                if pos.get("usa_trailing") == 1:
                    novo_sl = self.risk_manager.calculate_trailing_stop(
                         current_high=curr_price,
                         entry_price=entry,
                         stop_atual=pos["stop_loss_ativo"],
                         preco_ativacao=pos["trailing_ativacao"]
                    )
                    if novo_sl > pos["stop_loss_ativo"]:
                         db.update_trade_stop_loss(trade_id, novo_sl)
                         pos["stop_loss_ativo"] = novo_sl
                
                # Check Fechamento
                fechou = False
                pnl_usd = 0.0
                motivo = ""
                
                # Bateu Take Profit?
                if curr_price >= pos["take_profit_alvo"]:
                     pnl_usd = (curr_price - entry) * qty
                     motivo = "🎯 TAKE PROFIT"
                     fechou = True
                     
                # Bateu Stop Loss?
                elif curr_price <= pos["stop_loss_ativo"]:
                     pnl_usd = (curr_price - entry) * qty
                     motivo = "🛑 STOP LOSS"
                     fechou = True
                     
                if fechou:
                     print(f"[Sandbox] 🔒 Posição em {sym} FECHADA! Motivo: {motivo} | P/L: ${pnl_usd:.2f} | Preço Saída: {curr_price:.4f}")
                     fechamento_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                     profit_pct = ((curr_price - entry) / entry) * 100 if entry > 0 else 0
                     
                     db.close_trade(trade_id, fechamento_str, profit_pct, pnl_usd, motivo)
                     db.save_balance_history(datetime.datetime.now().strftime("%Y-%m-%d"), self.executor.mode, db.get_virtual_balance())
                     self.risk_manager.registrar_lucro(pnl_usd)
            
            print(f"[BuxexBrain] Status Banca Virtual Atual: ${db.get_virtual_balance():.2f}")

        # --- FIM DA VERIFICAÇÃO DE SANDBOX ---
        # Obter moedas interessantes
        target_coins = self.analyzer.fetch_top_coins(limit=5, min_volume=2000000.0)
        print(f"\n[BuxexBrain] Moedas Alvo Identificadas: {target_coins}")
        
        balance_usdt = self.executor.get_balance("USDT")
        print(f"[BuxexBrain] Saldo Disponível: ${balance_usdt:.2f}")

        for coin in target_coins:
            # Em um cenário real, o CCXT baixaria os candles com o método fetch_ohlcv.
            # Aqui simulamos o download para construir um df para o pandas-ta.
            # df_candles = self.executor.exchange.fetch_ohlcv(coin, timeframe='1h')
            # convert para DF
            
            # Simulando um candle dataframe (Fallback dryrun/setup)
            df_mock = pd.DataFrame({
                "Date": pd.date_range(end=pd.Timestamp.now(), periods=100),
                "Open": [10.0]*100,
                "High": [11.0]*100,
                "Low": [9.0]*100,
                "Close": [10.5]*100,
                "Volume": [1000]*100
            })
            # --- NOVO: FILTRO DE TENDÊNCIA 4H (ARCHON Edition) ---
            print(f"[BuxexBrain] Verificando filtro direcional de 4h para {coin}...")
            df_4h_mock = pd.DataFrame({
                "Date": pd.date_range(end=pd.Timestamp.now(), periods=250),
                "Close": [10.5]*250, # Acima da tendencia simulada
            })
            # Na API real: df_4h = self.executor.exchange.fetch_ohlcv(coin, timeframe='4h')
            # convert para DF e passa pra func
            
            filtro_4h = self.analyzer.analyze_4h_trend(df_4h_mock)
            if filtro_4h["signal"] == "rejected":
                 print(f"[BuxexBrain] 🛑 Mercados em queda. {coin} ignorada: {filtro_4h['reason']}")
                 continue # Pula a moeda e vai pra proxima
                 
            # --- FIM DO FILTRO 4H ---
            
            # Forçando uma tendência de alta no mock nos finais pra acionar o buy no gráfico menor
            df_mock.loc[99, 'Close'] = 11.0 
            
            analysis = self.analyzer.analyze_trend(df_mock)
            print(f"[BuxexBrain] Analisando Entrada (Curto Prazo) para {coin}... Sinal: {analysis['signal']} | Reason: {analysis['reason']}")

            if analysis["signal"] == "buy":
                # Sinal de Compra - Processo Gestão de Risco
                current_price = self.executor.get_current_price(coin)
                if current_price == 0:
                    current_price = 10.5 # Preço base para simulação se api falhar
                    
                print(f"[BuxexBrain] Ativando protocolo de Risco para a possível compra em {current_price}")
                
                # Exigência do plano: TP / SL / Metas
                risk_profile = self.risk_manager.validate_trade(symbol=coin, signal="buy", current_price=current_price)
                
                if risk_profile.get("status") == "rejected":
                     print(f"[BuxexBrain] 🛑 Ignorando oportunidade em {coin}. Motivo: {risk_profile.get('reason')}")
                     continue
                     
                print(f"[BuxexBrain] Gestão de Risco Definida: TP {risk_profile.get('take_profit_alvo')} | SL {risk_profile.get('stop_loss_inicial')}")
                # Validação de lote/capital
                position_size = self.risk_manager.calculate_position_size(available_balance=balance_usdt, current_price=current_price)
                print(f"[BuxexBrain] Tamanho Base do Lote: {position_size:.4f} moedas")
                
                # --- NOVO: FASE 3 - REDUÇÃO POR SENTIMENTO (Fear & Greed) ---
                feelings = self.sentiment.get_fear_and_greed_index()
                if feelings["value"] <= 20: # Medo Extremo
                     print(f"⚠️ [MERCADO EM MEDO EXTREMO - F&G {feelings['value']}] Cortando o tamanho da mão na metade!")
                     position_size = position_size / 2.0
                     print(f"[BuxexBrain] Novo Lote Ajustado (Reduzido): {position_size:.4f} moedas")
                # --- FIM REDUÇÃO SENTIMENTO ---
                
                # O Executor realiza a ação no mercado.
                # Como criamos o Sandbox, enviamos as metragens do RiskProfile na ordem simulada.
                result = self.executor.place_order(symbol=coin, quantity=position_size, side="buy", order_type="market", price=current_price, risk_profile=risk_profile)
                if result.get("status") == "success":
                    print(f"[BuxexBrain] TRADE EXECUTADO COM SUCESSO na moeda {coin}!")
                    self.notifier.enviar_whatsapp(f"✅ Nova Ordem de COMPRA Executada!\nMoeda: {coin}\nQuantidade: {position_size:.4f}\nPreço: ${current_price:.2f}")
                else:
                    print(f"[BuxexBrain] O TRADE FALHOU! {result}")
                    
                # Se for operação real, logamos a ordem criada (O executor já cria diretamento pro bd caso seja sandbox)
                if not self.executor.sandbox_mode and result.get("status") == "success":
                    db.insert_trade({
                         "id": str(datetime.datetime.now().timestamp()),
                         "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         "symbol": coin,
                         "type": "BUY",
                         "price": current_price,
                         "amount": position_size,
                         "mode": self.executor.mode,
                         "valor_investido": position_size * current_price,
                         "take_profit_alvo": risk_profile["take_profit_alvo"] if risk_profile else current_price * 1.05,
                         "stop_loss_inicial": risk_profile["stop_loss_inicial"] if risk_profile else current_price * 0.95,
                         "stop_loss_ativo": risk_profile["stop_loss_inicial"] if risk_profile else current_price * 0.95,
                         "trailing_ativacao": risk_profile["trailing_ativacao"] if risk_profile else current_price * 1.02,
                         "usa_trailing": risk_profile["usa_trailing"] if risk_profile else False,
                         "status": "OPEN"
                    })

        print("\n[BuxexBrain] Fim de ciclo. Aguardando próximo bloco...")


if __name__ == "__main__":
    brain = BuxexBrain()
    brain.loop_decision()
