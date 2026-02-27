import time
import sys
import os
from check_api import validate_binance_keys
from buxex_brain import BuxexBrain
from notifier import BuxexNotifier
import traceback
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
        self.notifier.enviar_email("Iniciando BuxexCoin Bot", "O robô de cripto BuxexCoin acabou de ser iniciado no servidor.")
        self.notifier.enviar_whatsapp("🚀 BuxexCoin SSAG Iniciado. Monitorando pares BTC/ETH/SOL.")

        while True:
            try:
                # Painel de Início do Ciclo
                table = Table(title=f"⏳ Status do Ciclo - {time.strftime('%Y-%m-%d %H:%M:%S')}")
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
