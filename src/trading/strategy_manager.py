import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
import logging
from .solo_dex_trader import SoloDEXTrader
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    timestamp: int
    action: str  # 'buy' or 'sell'
    price: float
    confidence: float
    strategy: str
    indicators: Dict[str, float]
    amount: float = 0.0

class StrategyManager:
    def __init__(self, wallet_seed: str = None, node_url: str = "wss://s.devnet.rippletest.net:51233"):
        self.dex = SoloDEXTrader(wallet_seed, node_url) if wallet_seed else None
        self.strategies = {
            'sma_crossover': self.sma_crossover_strategy,
            'price_action': self.price_action_strategy,
            'combined': self.combined_strategy
        }
        self.current_strategy = 'combined'
        
        # Strategy parameters
        self.sma_params = {
            'short_period': 10,
            'long_period': 30,
        }
        
        self.price_action_params = {
            'lookback': 5,
            'threshold': 0.02,
        }

    def calculate_sma(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return data.rolling(window=period).mean()

    def sma_crossover_strategy(self, candles: pd.DataFrame) -> Optional[TradingSignal]:
        """Simple Moving Average Crossover Strategy"""
        if len(candles) < self.sma_params['long_period']:
            return None

        closes = candles['close']
        short_sma = self.calculate_sma(closes, self.sma_params['short_period'])
        long_sma = self.calculate_sma(closes, self.sma_params['long_period'])

        # Check for crossover
        if short_sma.iloc[-2] <= long_sma.iloc[-2] and short_sma.iloc[-1] > long_sma.iloc[-1]:
            return TradingSignal(
                timestamp=int(datetime.now().timestamp() * 1000),
                action='buy',
                price=closes.iloc[-1],
                confidence=0.8,
                strategy='sma_crossover',
                indicators={
                    'short_sma': short_sma.iloc[-1],
                    'long_sma': long_sma.iloc[-1]
                },
                amount=100.0
            )
        elif short_sma.iloc[-2] >= long_sma.iloc[-2] and short_sma.iloc[-1] < long_sma.iloc[-1]:
            return TradingSignal(
                timestamp=int(datetime.now().timestamp() * 1000),
                action='sell',
                price=closes.iloc[-1],
                confidence=0.8,
                strategy='sma_crossover',
                indicators={
                    'short_sma': short_sma.iloc[-1],
                    'long_sma': long_sma.iloc[-1]
                },
                amount=100.0
            )
        
        return None

    def price_action_strategy(self, candles: pd.DataFrame) -> Optional[TradingSignal]:
        """Price Action Strategy based on momentum"""
        if len(candles) < self.price_action_params['lookback']:
            return None

        closes = candles['close']
        momentum = (closes.iloc[-1] - closes.iloc[-self.price_action_params['lookback']]) / closes.iloc[-self.price_action_params['lookback']]

        if momentum > self.price_action_params['threshold']:
            return TradingSignal(
                timestamp=int(datetime.now().timestamp() * 1000),
                action='buy',
                price=closes.iloc[-1],
                confidence=abs(momentum),
                strategy='price_action',
                indicators={
                    'momentum': momentum,
                    'threshold': self.price_action_params['threshold']
                },
                amount=100.0
            )
        elif momentum < -self.price_action_params['threshold']:
            return TradingSignal(
                timestamp=int(datetime.now().timestamp() * 1000),
                action='sell',
                price=closes.iloc[-1],
                confidence=abs(momentum),
                strategy='price_action',
                indicators={
                    'momentum': momentum,
                    'threshold': -self.price_action_params['threshold']
                },
                amount=100.0
            )
        
        return None

    def combined_strategy(self, candles: pd.DataFrame) -> Optional[TradingSignal]:
        """Combined strategy using multiple signals"""
        sma_signal = self.sma_crossover_strategy(candles)
        price_signal = self.price_action_strategy(candles)

        if sma_signal and price_signal and sma_signal.action == price_signal.action:
            # Strong signal when both strategies agree
            confidence = (sma_signal.confidence + price_signal.confidence) / 2
            return TradingSignal(
                timestamp=int(datetime.now().timestamp() * 1000),
                action=sma_signal.action,
                price=candles['close'].iloc[-1],
                confidence=confidence,
                strategy='combined',
                indicators={
                    'sma_confidence': sma_signal.confidence,
                    'price_confidence': price_signal.confidence,
                    'combined_confidence': confidence
                },
                amount=100.0
            )
        
        return None

    async def execute_signal(self, signal: TradingSignal):
        """Execute a trading signal on Solo DEX"""
        if not self.dex:
            logger.warning("DEX trader not initialized. Skipping trade execution.")
            return
            
        try:
            # Get current orderbook
            orderbook = await self.dex.get_orderbook('XRP', 'SOLO')
            
            # Execute trade based on signal
            if signal.action == 'buy':
                response = await self.dex.place_market_order(
                    'buy',
                    'XRP',
                    'SOLO',
                    float(signal.amount)
                )
            else:
                response = await self.dex.place_market_order(
                    'sell',
                    'XRP',
                    'SOLO',
                    float(signal.amount)
                )
                
            logger.info(f"Trade executed: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            return None

    def get_trading_signal(self, candle_data: Dict) -> Optional[TradingSignal]:
        """Get trading signal from the current strategy"""
        # Convert candle data to DataFrame
        df = pd.DataFrame([candle_data])
        return self.strategies[self.current_strategy](df)
