from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path
import os
from dotenv import load_dotenv
import json
from typing import List
from trading.strategy_manager import StrategyManager, TradingSignal
import logging

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your Netlify domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize strategy manager
strategy_manager = StrategyManager(
    wallet_seed=os.getenv("XRPL_SEED"),
    node_url=os.getenv("XRPL_NODE_URL", "wss://s.devnet.rippletest.net:51233")
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "price_update":
                candle = data["candle"]
                signal = strategy_manager.get_trading_signal(candle)
                
                if signal:
                    if data.get("auto_trading", False):
                        trade_response = await strategy_manager.execute_signal(signal)
                        if trade_response:
                            await manager.broadcast({
                                "type": "trade_execution",
                                "trade": trade_response
                            })
                    
                    await manager.broadcast({
                        "type": "strategy_signal",
                        "signal": signal.dict()
                    })
                
                await manager.broadcast({
                    "type": "price_update",
                    "candle": candle
                })
            
            elif data["type"] == "manual_trade":
                trade_response = await strategy_manager.execute_manual_trade(
                    action=data["action"],
                    amount=data["amount"]
                )
                if trade_response:
                    await manager.broadcast({
                        "type": "trade_execution",
                        "trade": trade_response
                    })
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
