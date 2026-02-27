FROM python:3.10-slim

WORKDIR /app

# Instala dependências do sistema necessárias para algumas bibliotecas numéricas
RUN apt-get update && apt-get install -y build-essential gcc

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código fonte
COPY . .

# Define o volume para logs contínuos (Onde o SQLite será persistido na máquina host)
VOLUME ["/app/data"]

# Por padrão, roda o robô orquestrador
CMD ["python", "src/main.py"]
