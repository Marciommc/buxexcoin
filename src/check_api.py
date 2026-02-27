import os
import ccxt

def validate_binance_keys() -> bool:
    """
    Valida as credenciais da Binance de forma rápida antes de iniciar o loop principal.
    Evita erros de HTTP 401 e IP Ban.
    """
    api_key = os.getenv("BINANCE_API_KEY")
    secret_key = os.getenv("BINANCE_SECRET_KEY")
    use_testnet = os.getenv("USE_TESTNET", "false").lower() == "true"

    if not api_key or not secret_key:
        print("[CheckAPI] ❌ Chaves da Binance ausentes no ambiente/arquivo .env!")
        return False

    print("[CheckAPI] ⏳ Validando credenciais e conexão com a Binance API...")
    try:
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
        })
        
        if use_testnet:
             exchange.set_sandbox_mode(True)
             
        # Tenta buscar os saldos, que exige autenticação
        exchange.fetch_balance()
        print("[CheckAPI] ✅ Autenticação Binance validadas com sucesso. Conexão estável!")
        return True
        
    except ccxt.AuthenticationError:
        print("[CheckAPI] ❌ Erro de Autenticação (401): Suas chaves de API da Binance são inválidas ou expiraram!")
        return False
    except Exception as e:
        print(f"[CheckAPI] ⚠️ Falha na pré-validação (Rede ou Manutenção): {str(e)}")
        # Dependendo do projeto pode retornar True para tentar no loop se for apenas erro passageiro.
        # Aqui seremos restritivos por segurança:
        return False

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    if not validate_binance_keys():
        exit(1)
