# Trading AI Assistant

An intelligent trading assistant that combines AI-driven market analysis with automated execution through mouse and keyboard control.

## Features

- Real-time market data analysis
- Technical indicator calculations
- AI-powered trading signals
- Automated trade execution via GUI automation
- Risk management controls
- User-friendly interface

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
- Copy `.env.example` to `.env`
- Add your API keys and trading parameters

## Project Structure

- `src/` - Main source code
  - `trading/` - Trading logic and algorithms
  - `automation/` - Mouse and keyboard control
  - `ui/` - User interface components
  - `models/` - AI models and predictions
- `config/` - Configuration files
- `data/` - Market data and model training data
- `tests/` - Unit tests

## Usage

1. Start the application:
```bash
python src/main.py
```

2. Configure your trading parameters in the UI
3. Monitor the AI predictions and automated trades

## Safety Features

- Built-in stop-loss mechanisms
- Position size limits
- Maximum daily loss limits
- Emergency stop button

## Disclaimer

This software is for educational purposes only. Trading carries significant risks. Always verify automated trades and use appropriate risk management strategies.
