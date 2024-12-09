// Global variables
let ws;
let chart;
let isAutoTrading = false;
let tradeHistory = [];

// Wait for SoloDex SDK to load
document.addEventListener('DOMContentLoaded', function() {
    if (typeof SoloDex === 'undefined') {
        console.log('Waiting for SoloDex SDK to load...');
        const checkSDK = setInterval(() => {
            if (typeof SoloDex !== 'undefined') {
                console.log('SoloDex SDK loaded');
                clearInterval(checkSDK);
                initChart();
            }
        }, 100);
    } else {
        initChart();
    }
});

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
                updateConnectionStatus('Connected');
            },
            onError: (error) => {
                console.error('Chart error:', error);
                updateConnectionStatus('Error: ' + error.message);
            }
        });

    } catch (error) {
        console.error('Error initializing Solo Dex chart:', error);
        updateConnectionStatus('Error: ' + error.message);
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
            updateConnectionStatus('Connected');
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected');
            updateConnectionStatus('Disconnected');
            setTimeout(initWebSocket, 5000);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateConnectionStatus('Error: ' + error.message);
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
        updateConnectionStatus('Error: ' + error.message);
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

// Update connection status
function updateConnectionStatus(status) {
    document.getElementById('connectionStatus').textContent = status;
    if (status === 'Connected') {
        document.getElementById('connectionStatus').classList.add('connected');
        document.getElementById('connectionStatus').classList.remove('disconnected');
    } else {
        document.getElementById('connectionStatus').classList.remove('connected');
        document.getElementById('connectionStatus').classList.add('disconnected');
    }
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
