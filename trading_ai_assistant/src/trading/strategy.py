import yfinance as yf
import pandas as pd
import numpy as np
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
import logging
from typing import Optional, Tuple

class TradingStrategy:
    def __init__(self, symbol: str, interval: str = '1h'):
        self.symbol = symbol
        self.interval = interval
        self.data: Optional[pd.DataFrame] = None
        
    def fetch_data(self, period: str = '1mo') -> pd.DataFrame:
        """Fetch market data for the symbol"""
        try:
            ticker = yf.Ticker(self.symbol)
            self.data = ticker.history(period=period, interval=self.interval)
            logging.info(f"Fetched {len(self.data)} data points for {self.symbol}")
            return self.data
        except Exception as e:
            logging.error(f"Error fetching data: {str(e)}")
            raise
    
    def calculate_indicators(self) -> pd.DataFrame:
        """Calculate technical indicators"""
        if self.data is None:
            raise ValueError("No data available. Call fetch_data first.")
        
        # Calculate SMA
        sma_20 = SMAIndicator(close=self.data['Close'], window=20)
        self.data['SMA20'] = sma_20.sma_indicator()
        
        # Calculate RSI
        rsi = RSIIndicator(close=self.data['Close'])
        self.data['RSI'] = rsi.rsi()
        
        return self.data
    
    def generate_signals(self) -> Tuple[bool, bool]:
        """Generate buy/sell signals based on indicators"""
        if self.data is None or 'SMA20' not in self.data.columns:
            raise ValueError("Indicators not calculated. Call calculate_indicators first.")
        
        last_close = self.data['Close'].iloc[-1]
        last_sma = self.data['SMA20'].iloc[-1]
        last_rsi = self.data['RSI'].iloc[-1]
        
        # Simple strategy: Buy if price is above SMA20 and RSI < 70
        buy_signal = last_close > last_sma and last_rsi < 70
        
        # Sell if price is below SMA20 and RSI > 30
        sell_signal = last_close < last_sma and last_rsi > 30
        
        logging.info(f"Signals generated - Buy: {buy_signal}, Sell: {sell_signal}")
        return buy_signal, sell_signal
    
    def calculate_position_size(self, account_balance: float, risk_percentage: float = 1.0) -> float:
        """Calculate position size based on account balance and risk percentage"""
        if self.data is None:
            raise ValueError("No data available. Call fetch_data first.")
        
        # Calculate position size based on risk
        max_risk_amount = account_balance * (risk_percentage / 100)
        last_price = self.data['Close'].iloc[-1]
        
        # Calculate position size (units)
        position_size = max_risk_amount / last_price
        
        return position_size
