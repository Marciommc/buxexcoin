#!/bin/bash
# Script Inteligente de Deploy SSAG - BuxexCoin

# 1. Parâmetros SSAG
TARGET_DIR="/root/projects/buxexcoin"
REPO_URL="https://github.com/Marciommc/buxexcoin.git"

echo "============================================="
echo "🌟 SSAG BUILDER: Iniciando Deploy BuxexCoin"
echo "============================================="

# 2. Prepara o Diretório Base
echo "[1] Configurando Diretório Hospedeiro..."
mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR" || exit 1

# 3. Download do Projeto
echo "[2] Clonando/Atualizando Repositório do BuxexCoin..."
if [ -d ".git" ]; then
    git pull origin main
else
    git clone "$REPO_URL" .
fi

# 4. Injetando Segurança (Interativo)
echo ""
echo "[3] Geração Interativa de Chaves SSAG e Segurança (.env)"
echo "--------------------------------------------------------"
if [ ! -f ".env" ]; then
    echo "⚠️ Arquivo .env não encontrado. Vamos criar juntos agora para rodar em produção segregrada:"
    
    read -p "BINANCE_API_KEY: " API_KEY
    read -sp "BINANCE_SECRET_KEY: " SECRET_KEY
    echo ""
    read -p "EMAIL_USER (Notificações): " EMAIL_USER
    read -sp "EMAIL_PASS (Notificações): " EMAIL_PASS
    echo ""
    read -p "EMAIL_DESTINO (Alvos dos reports): " EMAIL_DEST
    read -p "CALLMEBOT_API_KEY (Envie mensagem apikey p/ bot do Zap): " CALL_KEY
    echo ""
    read -p "WHATSAPP_DESTINO (Exato com sinal + Ex: +5592992790506): " WPP_DEST
    
    echo "BINANCE_API_KEY=$API_KEY" > .env
    echo "BINANCE_SECRET_KEY=$SECRET_KEY" >> .env
    echo "CMC_API_KEY=" >> .env
    echo "EMAIL_USER=$EMAIL_USER" >> .env
    echo "EMAIL_PASS=$EMAIL_PASS" >> .env
    echo "EMAIL_DESTINO=$EMAIL_DEST" >> .env
    echo "CALLMEBOT_API_KEY=$CALL_KEY" >> .env
    echo "WHATSAPP_DESTINO=$WPP_DEST" >> .env
    echo "" >> .env
    echo "TRADE_STRATEGY=SSAG-v2" >> .env
    echo "TAKE_PROFIT_PERCENT=5.0" >> .env
    echo "STOP_LOSS_PERCENT=3.0" >> .env
    echo "MAX_RISK_PER_TRADE=2.5" >> .env
    echo "META_DIARIA_USD=35.0" >> .env
    echo "ENABLE_TRAILING_STOP=true" >> .env
    echo "TRAILING_ACTIVATION_PCT=0.8" >> .env
    echo "SANDBOX_MODE=true" >> .env
    
    echo "✅ .env preenchido com segurança."
else
    echo "✅ .env já existe, pulando formulário."
fi

# 5. Prepara os volumes persistentes do SSAG
echo "[4] Criando links para Volumes SSAG Containerizados..."
mkdir -p ./data
chmod -R 777 ./data

# 6. Ignição do SSAG
echo "[5] Orquestrando Multi-Contêineres..."
docker-compose down
docker-compose up -d --build

echo "============================================="
echo "🚀 DEPLOY FINALIZADO! "
echo "O BuxexCoin já está trabalhando em background. Acesse o Dashboard em:"
echo "🌐 http://<IP_DA_MAQUINA>:5401"
echo "============================================="
