import sqlite3
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "buxex_data.db")

class BuxexDatabase:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        # Tabela atualizada: trades
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                symbol TEXT,
                type TEXT,
                price REAL,
                amount REAL,
                profit_pct REAL DEFAULT 0.0,
                profit_brl REAL DEFAULT 0.0,
                mode TEXT,
                
                -- Operacional
                valor_investido REAL,
                take_profit_alvo REAL,
                stop_loss_inicial REAL,
                stop_loss_ativo REAL,
                trailing_ativacao REAL,
                usa_trailing INTEGER,
                status TEXT,
                fechamento TEXT,
                motivo_fechamento TEXT
            )
        """)

        # Tabela atualizada: daily_metrics com chave composta
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_metrics (
                date TEXT,
                mode TEXT,
                profit REAL DEFAULT 0.0,
                PRIMARY KEY (date, mode)
            )
        """)
        
        # Nova Tabela: balance_history
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS balance_history (
                date TEXT,
                mode TEXT,
                balance REAL,
                PRIMARY KEY (date, mode)
            )
        """)

        # Tabela: sentiment_logs
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sentiment_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                value INTEGER,
                classification TEXT
            )
        """)
        
        self.conn.commit()

    # --- Daily Metrics ---
    def load_daily_profit(self, date_str: str, mode: str) -> float:
        self.cursor.execute("SELECT profit FROM daily_metrics WHERE date = ? AND mode = ?", (date_str, mode))
        row = self.cursor.fetchone()
        return row[0] if row else 0.0

    def save_daily_profit(self, date_str: str, mode: str, profit: float):
        self.cursor.execute("""
            INSERT INTO daily_metrics (date, mode, profit) 
            VALUES (?, ?, ?)
            ON CONFLICT(date, mode) DO UPDATE SET profit = excluded.profit
        """, (date_str, mode, profit))
        self.conn.commit()
        
    def save_balance_history(self, date_str: str, mode: str, balance: float):
        self.cursor.execute("""
            INSERT INTO balance_history (date, mode, balance) 
            VALUES (?, ?, ?)
            ON CONFLICT(date, mode) DO UPDATE SET balance = excluded.balance
        """, (date_str, mode, balance))
        self.conn.commit()

    def load_balance_history(self, mode: str):
        self.cursor.execute("SELECT date, balance FROM balance_history WHERE mode = ? ORDER BY date ASC", (mode,))
        return self.cursor.fetchall()

    # --- Sentimento ---
    def log_sentiment(self, value: int, classification: str):
        self.cursor.execute("""
            INSERT INTO sentiment_logs (timestamp, value, classification)
            VALUES (?, ?, ?)
        """, (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), value, classification))
        self.conn.commit()

    # --- Trades ---
    def insert_trade(self, trade_data: dict):
        self.cursor.execute("""
            INSERT INTO trades (
                id, timestamp, symbol, type, price, amount, mode, 
                valor_investido, take_profit_alvo, stop_loss_inicial, stop_loss_ativo, 
                trailing_ativacao, usa_trailing, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_data["id"], trade_data.get("timestamp"), trade_data["symbol"], trade_data["type"], 
            trade_data["price"], trade_data["amount"], trade_data["mode"],
            trade_data["valor_investido"], trade_data.get("take_profit_alvo", 0), trade_data.get("stop_loss_inicial", 0),
            trade_data.get("stop_loss_ativo", 0), trade_data.get("trailing_ativacao", 0),
            1 if trade_data.get("usa_trailing") else 0,
            trade_data.get("status", "OPEN")
        ))
        self.conn.commit()

    def update_trade_stop_loss(self, trade_id: str, novo_sl: float):
        self.cursor.execute("""
            UPDATE trades SET stop_loss_ativo = ? WHERE id = ?
        """, (novo_sl, trade_id))
        self.conn.commit()

    def close_trade(self, trade_id: str, fechamento_str: str, profit_pct: float, profit_brl: float, motivo: str):
        self.cursor.execute("""
            UPDATE trades 
            SET status = 'CLOSED', fechamento = ?, profit_pct = ?, profit_brl = ?, motivo_fechamento = ?
            WHERE id = ?
        """, (fechamento_str, profit_pct, profit_brl, motivo, trade_id))
        self.conn.commit()

    def get_open_trades(self, mode: str):
        self.cursor.execute("SELECT * FROM trades WHERE status = 'OPEN' AND mode = ?", (mode,))
        columns = [column[0] for column in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_all_trades(self, mode: str = None):
        if mode:
             self.cursor.execute("SELECT * FROM trades WHERE mode = ? ORDER BY timestamp DESC", (mode,))
        else:
             self.cursor.execute("SELECT * FROM trades ORDER BY timestamp DESC")
        columns = [column[0] for column in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_virtual_balance(self):
        saldo = 1000.0
        self.cursor.execute("SELECT sum(profit_brl) FROM trades WHERE status = 'CLOSED' AND mode = 'SANDBOX'")
        total_pnl = self.cursor.fetchone()[0]
        if total_pnl: saldo += total_pnl
        
        self.cursor.execute("SELECT sum(valor_investido) FROM trades WHERE status = 'OPEN' AND mode = 'SANDBOX'")
        total_investido_aberto = self.cursor.fetchone()[0]
        if total_investido_aberto: saldo -= total_investido_aberto
        
        return saldo

    def close(self):
        self.conn.close()

db = BuxexDatabase()
