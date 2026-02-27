# Deploy do BuxexCoin via Plesk Obsidian

Dependendo das permissões do seu painel Plesk e se o **Docker Extension** do Plesk está instalado, você tem dois caminhos principais para colocar o seu bot para rodar.

---

## Opção A: Deploy Nativo via Extensão Docker (Recomendado se tiver licença)
No Plesk, se a extensão Docker (Docker integration) estiver ativada, use-a para gerenciar a imagem e rodar o container pelo próprio painel.

1. **Upload / Clone do Repositório Mestre**:
   - Vá ao seu painel Plesk -> **Domains** (Domínios) -> Selecione o seu domínio de controle.
   - Clique em **File Manager** (Gerenciador de Arquivos).
   - Crie uma pasta raiz fora do `httpdocs` como `buxexcoin`.
   - **Upload:** Envie todos os arquivos do GitHub, ou use a ferramenta **Git** do próprio Plesk para fazer o clone de `https://github.com/Marciommc/buxexcoin.git` na pasta.

2. **Criação do `.env` (Protegido)**:
   - Dentro da pasta clonada (`buxexcoin`) no **File Manager**, crie o seu arquivo `.env` usando o botão *New File*.
   - Cole todas as suas chaves e configs de sandbox, idênticas ao modelo que desenvolvemos.

3. **Criação e Bind da Pasta Data**:
   - Pelo File Manager, clique para criar um diretório dentro de `buxexcoin` com o nome **`data`**. 
   - Modifique as permissões (Change Permissions) para garantir Acesso Total (Leitura e Escrita), porque é aqui que o SQLite `buxex_data.db` vai habitar com segurança.

4. **Iniciando via Docker (Docker Extension)**:
   - Procure a ferramenta **Docker Proxy/Manager** ou **Docker** no menu esquerdo do Plesk.
   - Vá em *Local Image* ou crie um *Docker Compose* apontando para a pasta que hospeda o `docker-compose.yml`.
   - Como estamos usando 2 containeres interligados (Bot + Dashboard), o recomedado é usar a funcionalidade de Docker Compose Proxy Extension.
   - Suba os serviços declarativamente e mapeie no Proxy do Plesk a porta **5401** para ser mostrada em um subdomínio (ex: `bot.buxexcoin.com.br`).

---

## Opção B: Deploy Profundo via SSH / Terminal (Seguro & Definitivo)

Se o seu Plesk for focado apenas como hospedagem Web e não tiver o pacote Docker Full pago, não tem problema. O Plesk é um Ubuntu/AlmaLinux por baixo e vamos rodar isso via linha de comando, da forma mais garantida para robôs financeiros:

### Passo 1: Acesse sua máquina (VPS) via SSH
Utilize um cliente Terminal (como PuTTY ou OpenSSH no Windows) para entrar root.
```bash
ssh root@SEU_IP_OU_DOMINIO_DO_PLESK
```

### Passo 2: Copie e Execute o Script de Configuração

Nós geramos na fase anterior um arquivo interativo chamado `setup_vps.sh` justamente para essa finalidade.

1. Navegue para a pasta de projetos (ou raiz, se preferir): 
```bash
cd /root/
```
2. Baixe o script interativo que subimos pro Github:
```bash
wget https://raw.githubusercontent.com/Marciommc/buxexcoin/master/setup_vps.sh
chmod +x setup_vps.sh
```

### Passo 3: Magia Acontecendo 🌠

Agora, basta chamar o construtor interativo:
```bash
./setup_vps.sh
```

O Script vai:
1. Criar a pasta `/root/projects/buxexcoin`.
2. Fazer `git clone` de todo seu projeto.
3. Pausar e pedir para você colar a API Key, Secret Key e informações do WhatsApp (as preenchendo no `.env`).
4. Criar a sua pasta `data` com permissões `777` corretas para o Plesk não travar a edição.
5. Rodar o orquestrador multi-container usando o comando `docker-compose up -d --build`.

### Passo 4: Como Fazer o Proxy no Plesk (Para visualizar o Dashboard sem usar :5401)
Seu terminal rodou e a UI do Buxexcoin está rodando em plano de fundo no `localhost:5401`. Para facilitar o acesso sem digitar portas complexas no navegador:

1. Acesse o **Plesk Web Interface**.
2. Vá em **Add Domain** ou **Add Subdomain** (ex: `dashboard.seudominio.com`).
3. Nas configurações do domínio criado, vá até **Apache & nginx Settings** (ou apenas **Apache Settings** dependendo da sua versão).
4. Desça a rolagem até a seção **Additional directives for HTTP** e **Additional directives for HTTPS**, e cole as seguintes diretivas do Apache em ambas as caixas para fazer o proxy reverso:

```apache
ProxyRequests Off
ProxyPreserveHost On

<Proxy *>
    Require all granted
</Proxy>

ProxyPass / http://127.0.0.1:5401/
ProxyPassReverse / http://127.0.0.1:5401/
```

*Nota: Certifique-se de que os módulos `proxy` e `proxy_http` do Apache estejam ativados no seu servidor VPS.*

Clique em Aplicar/OK! Pronto! 🎉 
Você poderá acessar a Dashboard maravilhosamente pela URL pública em https, enquanto o Bot BuxexBrain fica orquestrando de forma indestrutível conectado ao SQLite no backend.
