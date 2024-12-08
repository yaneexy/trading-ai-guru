#!/usr/bin/env python
import sys
import logging
from rich.console import Console
from rich.logging import RichHandler
from src.cli import TradingCLI
from src.main import start_application

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)

console = Console()

def main():
    try:
        # Start with CLI interface
        cli = TradingCLI()
        cli.display_welcome()
        
        # Load existing config if available
        cli.config = cli.load_config()
        
        # Start the CLI interface
        import asyncio
        asyncio.run(cli.main_menu())
        
    except KeyboardInterrupt:
        console.print("\nGoodbye! Happy trading! 📈", style="bold blue")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}")
        logging.exception("An error occurred")
        sys.exit(1)

if __name__ == "__main__":
    main()
