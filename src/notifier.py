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
        self.whatsapp_webhook = os.getenv("WHATSAPP_WEBHOOK", "https://seu-webhook.com/api/send")

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
        if self.whatsapp_webhook == "https://seu-webhook.com/api/send":
            print(f"[Notifier] WhatsApp simulado: {texto}")
            return
            
        payload = {"message": f"🤖 *BuxexCoin:* \n{texto}"}
        try:
            # Substitua pelo método de envio da sua API de preferência
            requests.post(self.whatsapp_webhook, json=payload, timeout=5)
            print("📲 Alerta enviado para o WhatsApp.")
        except Exception as e:
            print(f"❌ Erro ao enviar WhatsApp: {e}")

# --- EXEMPLO DE USO NO BOT ---
if __name__ == "__main__":
    notifier = BuxexNotifier()
    notifier.enviar_whatsapp("Teste manual de inicialização: Sistema BuxexCoin OK.")
