// Global variables
let ws;
let chart;
let isAutoTrading = false;
let tradeHistory = [];

// Initialize Solo Dex chart
function initChart() {
    try {
        console.log('Initializing Solo Dex chart...');
        const chartContainer = document.getElementById('tradingChart');
        
        if (!chartContainer) {
            console.error('Chart container not found');
            return;
        }

        // Initialize Solo Dex chart
        chart = new SoloDex.Chart({
            container: 'tradingChart',
            symbol: 'XRPUSDT',
            exchange: 'binance',
            interval: '1m',
            theme: 'dark',
            height: 500,
            indicators: [
                {
                    name: 'RSI',
                    settings: { period: 14 }
                },
                {
                    name: 'MACD',
                    settings: {
                        fastPeriod: 12,
                        slowPeriod: 26,
                        signalPeriod: 9
                    }
                },
                {
                    name: 'Volume'
                }
            ],
            onReady: () => {
                console.log('Solo Dex chart initialized successfully');
                initWebSocket();
            }
        });

    } catch (error) {
        console.error('Error initializing Solo Dex chart:', error);
        const chartContainer = document.getElementById('tradingChart');
        if (chartContainer) {
            chartContainer.innerHTML = `Error initializing chart: ${error.message}`;
        }
    }
}

// Initialize WebSocket connection
function initWebSocket() {
    try {
        const wsUrl = window.location.hostname === 'localhost' 
            ? 'ws://localhost:8000/ws'
            : `wss://${window.location.hostname}/api/ws`;
        
        console.log('Connecting to WebSocket:', wsUrl);
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log('WebSocket connected');
            document.getElementById('connectionStatus').textContent = 'Connected';
            document.getElementById('connectionStatus').classList.add('connected');
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected');
            document.getElementById('connectionStatus').textContent = 'Disconnected';
            document.getElementById('connectionStatus').classList.remove('connected');
            document.getElementById('connectionStatus').classList.add('disconnected');
            setTimeout(initWebSocket, 5000);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            document.getElementById('connectionStatus').textContent = 'Connection Error';
            document.getElementById('connectionStatus').classList.add('disconnected');
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('Received data:', data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error processing message:', error);
            }
        };
    } catch (error) {
        console.error('Error initializing WebSocket:', error);
    }
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    if (!data || !data.type) return;

    switch (data.type) {
        case 'strategy_signal':
            updateStrategyPanel(data.signal);
            break;
        case 'trade_execution':
            updateTradeHistory(data.trade);
            break;
    }
}

// Update strategy panel
function updateStrategyPanel(signal) {
    const panel = document.getElementById('strategyPanel');
    if (!panel) return;

    const header = panel.querySelector('.strategy-header .cyber-text');
    if (header) {
        header.textContent = signal.message || 'Strategy Signal Received';
    }
}

// Update trade history
function updateTradeHistory(trade) {
    tradeHistory.unshift(trade);
    // Implement trade history display if needed
}

// Event listeners for trading controls
document.getElementById('toggleAutoTrading')?.addEventListener('click', function() {
    isAutoTrading = !isAutoTrading;
    this.textContent = isAutoTrading ? 'Stop Auto Trading' : 'Start Auto Trading';
    
    ws.send(JSON.stringify({
        type: 'auto_trading',
        enabled: isAutoTrading
    }));
});

document.getElementById('manualBuy')?.addEventListener('click', function() {
    const amount = document.getElementById('tradeAmount')?.value || 100;
    ws.send(JSON.stringify({
        type: 'manual_trade',
        action: 'BUY',
        amount: parseFloat(amount)
    }));
});

document.getElementById('manualSell')?.addEventListener('click', function() {
    const amount = document.getElementById('tradeAmount')?.value || 100;
    ws.send(JSON.stringify({
        type: 'manual_trade',
        action: 'SELL',
        amount: parseFloat(amount)
    }));
});

// Initialize everything when the page loads
window.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded, initializing...');
    // Wait for Solo Dex script to load
    setTimeout(() => {
        initChart();
    }, 1000);
});
