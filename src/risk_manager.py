import os
from typing import Dict, Any
from database import db

class RiskManager:
    def __init__(self, notifier=None):
        self.notifier = notifier
        # Lê os parâmetros do ambiente configurados no .env
        self.strategy = os.getenv("TRADE_STRATEGY", "scalping")
        self.take_profit_pct = float(os.getenv("TAKE_PROFIT_PERCENT", "1.0")) / 100.0
        self.stop_loss_pct = float(os.getenv("STOP_LOSS_PERCENT", "0.5")) / 100.0
        self.max_risk_per_trade = float(os.getenv("MAX_RISK_PER_TRADE", "0.05"))
        
        # Fase 2: Segurança do Capital e Arquivo de Persistência
        self.meta_diaria_usd = float(os.getenv("META_DIARIA_USD", "35.0"))
        self.enable_trailing = os.getenv("ENABLE_TRAILING_STOP", "true").lower() == "true"
        self.trailing_activation_pct = float(os.getenv("TRAILING_ACTIVATION_PCT", "0.8")) / 100.0
        
        # Modo isolado PNL
        self.sandbox_mode = os.getenv("SANDBOX_MODE", "true").lower() == "true"
        self.mode = "SANDBOX" if self.sandbox_mode else "REAL"
        
        # Controle de Estado Diário
        self.lucro_diario_atual_usd = 0.0
        self.data_ultima_execucao = None
        self._load_profit()
        
    def _load_profit(self):
        """Carrega o lucro acumulado no SQLite"""
        import datetime
        hoje_str = str(datetime.datetime.utcnow().date())
        
        self.lucro_diario_atual_usd = db.load_daily_profit(hoje_str, self.mode)
        self.data_ultima_execucao = hoje_str
        print(f"[RiskManager] Persistência carregada ({self.mode}): Lucro de hoje ${self.lucro_diario_atual_usd:.2f}")

    def _save_profit(self):
        """Salva o progresso diário no SQLite"""
        if self.data_ultima_execucao:
            db.save_daily_profit(self.data_ultima_execucao, self.mode, self.lucro_diario_atual_usd)

    def _reset_daily_stats_if_needed(self):
        """Zera o contador de lucro se virou o dia (UTC)"""
        import datetime
        hoje_str = str(datetime.datetime.utcnow().date())
        if str(self.data_ultima_execucao) != hoje_str:
            print(f"[RiskManager] Novo dia detectado ({hoje_str}). Resetando travas diárias.")
            self.lucro_diario_atual_usd = 0.0
            self.data_ultima_execucao = hoje_str
            self._save_profit()

    def registrar_lucro(self, lucro_realizado_usd: float):
        """Soma (ou subtrai) o resultado da operação fechada ao histórico do dia"""
        self._reset_daily_stats_if_needed()
        self.lucro_diario_atual_usd += lucro_realizado_usd
        self._save_profit()
        print(f"[RiskManager] Fechamento no dia atual: ${self.lucro_diario_atual_usd:.2f} / Meta: ${self.meta_diaria_usd:.2f}")

        if self.lucro_diario_atual_usd >= self.meta_diaria_usd:
            msg = f"🏆 *META DIÁRIA ATINGIDA!* \nLucro gerado: ${self.lucro_diario_atual_usd:.2f} USD.\nO Bot BuxexCoin está entrando em Standby para proteger os ganhos."
            if self.notifier:
                self.notifier.enviar_whatsapp(msg)
                
    def meta_diaria_atingida(self) -> bool:
        """Verifica se o bot deve entrar em Standby por atingir a meta/bater limite"""
        self._reset_daily_stats_if_needed()
        
        # Pode se criar uma trava de stop loss diario aqui também se a banca descer X dólares no mesmo dia.
        if self.lucro_diario_atual_usd >= self.meta_diaria_usd:
            return True
        return False

    def calculate_position_size(self, available_balance: float, current_price: float) -> float:
        """
        Calcula o tamanho da posição com base no risco máximo permitido pelo capital total.
        :param available_balance: Saldo disponível na moeda de cotação (ex: USDT)
        :param current_price: Preço atual do ativo
        :return: Quantidade a ser comprada da moeda base
        """
        capital_to_risk = available_balance * self.max_risk_per_trade
        # Se usarmos o stop loss como base do risco:
        # Posição = Capital em risco / (Preço Atual * % de Stop Loss)
        # Ex: Risco = $20 (2% de $1000). Stop Loss = 2%. Posição = 20 / (Price * 0.02)
        position_size_usd = capital_to_risk / self.stop_loss_pct
        
        # Garantir que a posição em USD não exceda margens de segurança (ex: 100% do saldo)
        if position_size_usd > available_balance:
            position_size_usd = available_balance * 0.95 # Usa max 95% se math estourar

        amount_to_buy = position_size_usd / current_price
        return amount_to_buy

    def calculate_exit_targets(self, entry_price: float, side: str = "buy") -> Dict[str, Any]:
        """
        Calcula os níveis de Take Profit e Stop Loss base.
        """
        if side == "buy":
            tp_price = entry_price * (1 + self.take_profit_pct)
            sl_price = entry_price * (1 - self.stop_loss_pct)
        else:
            tp_price = entry_price * (1 - self.take_profit_pct)
            sl_price = entry_price * (1 + self.stop_loss_pct)
            
        return {
            "take_profit_alvo": round(tp_price, 4),
            "stop_loss_inicial": round(sl_price, 4),
            "trailing_ativacao": round(entry_price * (1 + self.trailing_activation_pct) if side == "buy" else entry_price * (1 - self.trailing_activation_pct), 4),
            "usa_trailing": self.enable_trailing
        }

    def validate_trade(self, symbol: str, signal: str, current_price: float) -> dict:
        """
        Valida se um trade faz sentido baseado no risco e regras diárias.
        """
        if self.meta_diaria_atingida():
             print(f"[RiskManager] 🚫 Trade Rejeitado! Meta Diária Bateu (Standby).")
             return {"status": "rejected", "reason": "daily_goal_reached"}

        print(f"[Risk Manager] Validando operação {signal} para {symbol} ao preço de {current_price}")
        targets = self.calculate_exit_targets(current_price, side=signal)
        targets["status"] = "approved"
        
        return targets
        
    def calculate_trailing_stop(self, entry_price: float, current_high: float, stop_atual: float) -> float:
        """
        Sobe o Stop Loss (Trailing). Se o mercado subiu e bateu a % de ativação do Trailing,
        o novo stop passa a ser pelo menos a entrada ou logo abaixo da alta atual.
        """
        if not self.enable_trailing:
            return stop_atual
            
        preco_ativacao = entry_price * (1 + self.trailing_activation_pct)
        if current_high >= preco_ativacao:
            # Trava no Break-Even (ou leve lucro) se o preco subir 0.8%
            novo_stop = entry_price * 1.002 # Breakeven + pequena folga para a taxa
            if novo_stop > stop_atual:
                 print(f"🔒 [RiskManager] Trailing Ativado! Stop protegido no Break-Even: {novo_stop:.4f}")
                 if self.notifier:
                      self.notifier.enviar_whatsapp(f"🔒 *Trailing Stop Ativado!*\nOrdem protegida no Break-Even. O mercado subiu a favor! Lucro garantido.")
                 return novo_stop
                 
        return stop_atual
