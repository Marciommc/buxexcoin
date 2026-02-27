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
        
        # Configuração WhatsApp (CallMeBot API Gratuita)
        self.whatsapp_apikey = os.getenv("CALLMEBOT_API_KEY", "")
        self.destinatario_zap = os.getenv("WHATSAPP_DESTINO", "+5592992790506")

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
        if not self.whatsapp_apikey:
            print(f"[Notifier] WhatsApp simulado (API KEY Não configurada): {texto}")
            return
            
        import urllib.parse
        texto_codificado = urllib.parse.quote(texto)
        
        url_callmebot = f"https://api.callmebot.com/whatsapp.php?phone={self.destinatario_zap}&text={texto_codificado}&apikey={self.whatsapp_apikey}"
        
        try:
            resp = requests.get(url_callmebot, timeout=10)
            if resp.status_code == 200:
                print("📲 Alerta enviado para o WhatsApp com sucesso (CallMeBot).")
            else:
                print(f"❌ Erro ao enviar WhatsApp do CallMeBot: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"❌ Erro de conexão com a CallMeBot API: {e}")

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
