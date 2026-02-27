# 📦 BuxexCoin — Guia Oficial de Deploy

## Infraestrutura

| Serviço | Tecnologia | Porta |
|---|---|---|
| Robô de trading | Docker (`buxex_core_bot`) | — |
| Dashboard | Docker (`buxex_dashboard`) → Streamlit | `5501` |
| Proxy reverso | Apache (Plesk) | `443 (HTTPS)` |
| Banco de dados | SQLite (`/app/data/buxex_data.db`) | — |
| URL pública | https://scalpcoin.ssagtecnologia.com | — |

> ⚠️ A porta `5401` é **reservada** para o `ssag-controlplane`. Não utilizar para o BuxexCoin.

---

## Pré-requisitos na VPS

- Docker + Docker Compose V2
- Apache com módulos: `proxy`, `proxy_http`, `proxy_wstunnel`, `rewrite`

```bash
# Ativar módulos (apenas uma vez)
a2enmod proxy proxy_http proxy_wstunnel rewrite
systemctl reload apache2
```

---

## Configuração do Apache (Plesk)

> ⚠️ **NUNCA edite** `/etc/apache2/plesk.conf.d/vhosts/scalpcoin.ssagtecnologia.com.conf` — ele é gerado automaticamente pelo Plesk.
> 
> As customizações devem ir **exclusivamente** nos arquivos abaixo:

**HTTPS** → `/var/www/vhosts/system/scalpcoin.ssagtecnologia.com/conf/vhost_ssl.conf`

```apache
ProxyPreserveHost On

RewriteEngine On
RewriteCond %{HTTP:Upgrade} =websocket [NC]
RewriteRule /(.*) ws://localhost:5501/$1 [P,L]

ProxyPass / http://localhost:5501/
ProxyPassReverse / http://localhost:5501/
```

Após editar, sempre validar e recarregar:
```bash
apache2ctl configtest && systemctl reload apache2
```

---

## Deploy / Atualização

```bash
cd /root/projects/buxexcoin

# 1. Puxar alterações
git pull

# 2. Subir containers (rebuild apenas se houver mudança de código)
docker compose down
docker compose up -d --build

# 3. Verificar se subiram corretamente
docker ps --filter "name=buxex"
```

---

## Verificação de Saúde

```bash
# Logs do robô (últimas 50 linhas)
docker logs buxex_core_bot --tail 50

# Testar Streamlit localmente
curl -s -o /dev/null -w "%{http_code}" http://localhost:5501
# Esperado: 200

# Verificar banco de dados
docker exec buxex_core_bot python3 -c "
import sqlite3
conn = sqlite3.connect('/app/data/buxex_data.db')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM trades')
print('Trades:', cur.fetchone()[0])
conn.close()
"
```

---

## Variáveis de Ambiente (`.env`)

| Variável | Descrição |
|---|---|
| `BINANCE_API_KEY` | Chave da API Binance |
| `BINANCE_SECRET_KEY` | Secret da API Binance |
| `SANDBOX_MODE` | `true` = paper trading, `false` = real |
| `META_DIARIA_USD` | Meta diária em USD (padrão: `35.0`) |
| `TRADE_STRATEGY` | `scalping` ou `swing_trade` |
| `ENABLE_TRAILING_STOP` | `true` / `false` |
| `WHATSAPP_DESTINO` | Número para notificações WhatsApp |
| `CALLMEBOT_API_KEY` | Chave CallMeBot para WhatsApp |

---

## Problemas Conhecidos e Soluções

| Sintoma | Causa | Solução |
|---|---|---|
| Dashboard branco / loading infinito | WebSocket não configurado no Apache | Verificar `vhost_ssl.conf` com as diretivas de proxy |
| Porta já alocada ao subir container | Conflito com outro serviço | Verificar Portas: `5401=ssag-controlplane`, `5501=buxexcoin` |
| `git pull` falha com "local changes" | VPS tem alterações não commitadas | `git stash && git pull` |
| Robô não executa trades | Dados mock ativos no código | Garantir que `buxex_brain.py` usa `fetch_ohlcv` real |
| Banco vazio após subir | Volume Docker não compartilhado | Usar volume nomeado `buxex_data` no `docker-compose.yml` |
