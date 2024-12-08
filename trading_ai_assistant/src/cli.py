import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
import sys
import os
from typing import Dict, Any
import json

console = Console()

class TradingCLI:
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.config_file = "config/trading_config.json"
    
    def display_welcome(self):
        """Display welcome message and ASCII art"""
        welcome_text = """
╔════════════════════════════════════════════╗
║           Trading AI Assistant             ║
║        Your Smart Trading Companion        ║
╚════════════════════════════════════════════╝
        """
        console.print(Panel(welcome_text, style="bold blue"))
    
    def load_config(self) -> Dict[str, Any]:
        """Load existing configuration if available"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_config(self):
        """Save configuration to file"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    async def configure_trading(self):
        """Configure trading parameters through interactive prompts"""
        trading_mode = await questionary.select(
            "Select trading mode:",
            choices=[
                "Paper Trading",
                "Live Trading (Real Money)",
            ]
        ).ask_async()
        
        exchange = await questionary.select(
            "Select trading exchange:",
            choices=[
                "Binance",
                "Coinbase",
                "MetaTrader 5",
                "Custom Platform",
            ]
        ).ask_async()
        
        symbol = await questionary.text(
            "Enter trading symbol (e.g., BTC/USD):",
            validate=lambda text: len(text) > 0
        ).ask_async()
        
        risk_percentage = await questionary.text(
            "Enter risk percentage per trade (1-5%):",
            validate=lambda text: text.isdigit() and 1 <= int(text) <= 5
        ).ask_async()
        
        self.config.update({
            "trading_mode": trading_mode,
            "exchange": exchange,
            "symbol": symbol,
            "risk_percentage": float(risk_percentage)
        })
        
        self.save_config()
        self.display_config()
    
    def display_config(self):
        """Display current configuration in a nice table"""
        table = Table(title="Trading Configuration", box=box.ROUNDED)
        table.add_column("Parameter", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in self.config.items():
            table.add_row(key.replace("_", " ").title(), str(value))
        
        console.print(table)
    
    async def main_menu(self):
        """Display and handle main menu options"""
        while True:
            choice = await questionary.select(
                "What would you like to do?",
                choices=[
                    "Configure Trading Parameters",
                    "Start Trading Assistant",
                    "View Current Configuration",
                    "Exit"
                ]
            ).ask_async()
            
            if choice == "Configure Trading Parameters":
                await self.configure_trading()
            elif choice == "Start Trading Assistant":
                console.print("Starting trading assistant...", style="green")
                # Import and start the main GUI application
                from main import start_application
                start_application()
                break
            elif choice == "View Current Configuration":
                self.display_config()
            else:
                console.print("Goodbye! Happy trading!", style="bold blue")
                sys.exit(0)

def main():
    cli = TradingCLI()
    cli.display_welcome()
    
    # Load existing config if available
    cli.config = cli.load_config()
    
    # Start the CLI interface
    import asyncio
    asyncio.run(cli.main_menu())

if __name__ == "__main__":
    main()
