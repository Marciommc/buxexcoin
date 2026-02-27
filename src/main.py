import time
import sys
import os
from check_api import validate_binance_keys
from buxex_brain import BuxexBrain
from notifier import BuxexNotifier
import traceback
from datetime import datetime
import pytz
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

class BuxexMasterCore:
    def __init__(self):
        console.print(Panel("[bold cyan]Iniciando BuxexMasterCore...[/bold cyan]\nCarregando módulos de inteligência artificial.", title="🤖 BuxexCoin SSAG"))
        self.notifier = BuxexNotifier()
        self.brain = BuxexBrain()
        self.delay_segundos = 15 * 60 # 15 minutos entre varreduras
        
    def run_forever(self):
        manaustz = pytz.timezone('America/Manaus')
        hora_agora = datetime.now(manaustz).strftime("%d/%m/%Y %H:%M:%S")

        self.notifier.enviar_email(
             f"BuxexCoin SSAG Iniciado - {hora_agora}", 
             f"O robô (modo {self.brain.executor.mode}) acabou de subir no horário de Manaus, configurado para R$ {self.brain.risk_manager.meta_diaria_usd} de meta."
        )
        self.notifier.enviar_whatsapp(f"🚀 *BuxexCoin SSAG UP!*\nHorário (MAO): {hora_agora}\nModo: {self.brain.executor.mode}")

        while True:
            try:
                # Painel de Início do Ciclo
                hora_ciclo = datetime.now(manaustz).strftime("%Y-%m-%d %H:%M:%S")
                table = Table(title=f"⏳ Status do Ciclo - {hora_ciclo}")
                table.add_column("Módulo", justify="left", style="cyan", no_wrap=True)
                table.add_column("Ação", style="magenta")
                table.add_column("Status", justify="right", style="green")

                table.add_row("🧠 BuxexBrain", "Análise e Risco", "[bold yellow]PROCESSANDO...[/bold yellow]")
                table.add_row("🕸️ Sentimento", "Medo & Ganância", "OK")
                console.print(table)
                
                # Executa o cérebro
                self.brain.loop_decision()
                
                console.print(Panel(f"[bold green]Ciclo Finalizado![/bold green] \nO robô entrará em estado de stand-by (dormindo) por {self.delay_segundos / 60} minutos para poupar recursos da API.", style="green"))
                time.sleep(self.delay_segundos)
                
            except KeyboardInterrupt:
                console.print("\n[bold red]⚠️  Robô BuxexCoin interrompido pelo usuário no terminal.[/bold red]")
                self.notifier.enviar_whatsapp("⚠️ BuxexCoin parado manualmente.")
                sys.exit(0)
                
            except Exception as e:
                erro_msg = traceback.format_exc()
                print(f"\n[CRITICAL ERROR] O bot sofreu um erro não tratado:\n{erro_msg}")
                self.notifier.enviar_email("CRITICAL ERROR - BuxexCoin caiu!", erro_msg)
                self.notifier.enviar_whatsapp(f"🚨 ERRO CRÍTICO no BuxexCoin. Tentando religar em 5 min. Erro base: {str(e)[:50]}")
                time.sleep(300) # Dorme 5 minutos em caso de queda de API/Timeout e tenta de novo

if __name__ == "__main__":
    if not validate_binance_keys():
        print("Finalizando robô prematuramente devido a erro grave nas credenciais de API.")
        sys.exit(1)
        
    master = BuxexMasterCore()
    master.run_forever()
