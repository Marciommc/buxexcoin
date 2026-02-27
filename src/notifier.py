import smtplib
from email.mime.text import MIMEText
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class BuxexNotifier:
    def __init__(self):
        # Configurações de E-mail (Ex: Gmail SMTP)
        self.email_user = os.getenv("EMAIL_USER", "seu_email@gmail.com")
        self.email_pass = os.getenv("EMAIL_PASS", "sua_senha_app") # Senha de aplicativo do Google
        self.destinatario = os.getenv("EMAIL_DESTINO", "seu_email_destino@gmail.com")
        
        # Configuração WhatsApp (Exemplo via Webhook/Evolution API)
        self.whatsapp_webhook = os.getenv("WHATSAPP_WEBHOOK", "")
        self.whatsapp_evol_apikey = os.getenv("EVOLUTION_API_KEY", "")
        self.destinatario_zap = os.getenv("WHATSAPP_DESTINO", "5592992790506")

    def enviar_email(self, assunto, mensagem):
        if self.email_user == "seu_email@gmail.com":
            print(f"[Notifier] Email simulado: {assunto}")
            return
            
        try:
            msg = MIMEText(mensagem)
            msg['Subject'] = assunto
            msg['From'] = self.email_user
            msg['To'] = self.destinatario

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.email_user, self.email_pass)
                server.send_message(msg)
            print("✉️ Relatório enviado por e-mail.")
        except Exception as e:
            print(f"❌ Erro ao enviar e-mail: {e}")

    def enviar_whatsapp(self, texto):
        if not self.whatsapp_webhook:
            print(f"[Notifier] WhatsApp simulado: {texto}")
            return
            
        headers = {"Content-Type": "application/json"}
        if self.whatsapp_evol_apikey:
            headers["apikey"] = self.whatsapp_evol_apikey
            
        payload = {
            "number": self.destinatario_zap,
            "options": {
                "delay": 1200,
                "presence": "composing"
            },
            "textMessage": {
                "text": texto
            }
        }
        
        try:
            resp = requests.post(self.whatsapp_webhook, json=payload, headers=headers, timeout=5)
            if resp.status_code in (200, 201):
                print("📲 Alerta enviado para o WhatsApp com sucesso.")
            else:
                print(f"❌ Erro ao enviar WhatsApp do Evolution: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"❌ Erro de conexão com a Evolution API: {e}")

    def alertar_trade(self, symbol: str, progresso_meta_pct: float, meta_valor: float):
        msg = (
            f"💰 *BuxexCoin - Alerta de Trade*\n"
            f"Par: {symbol}\n"
            f"Status: Meta de R$ {meta_valor:.2f} em {progresso_meta_pct:.1f}%!"
        )
        self.enviar_whatsapp(msg)


# --- EXEMPLO DE USO NO BOT ---
if __name__ == "__main__":
    notifier = BuxexNotifier()
    notifier.enviar_whatsapp("Teste manual de inicialização: Sistema BuxexCoin OK.")
