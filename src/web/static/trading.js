// Global variables
let ws;
let chart;
let candlestickSeries;
let volumeSeries;
let strategyOverlay;
let isAutoTrading = false;
let tradeHistory = [];

// Initialize WebSocket connection
function initWebSocket() {
    ws = new WebSocket('ws://localhost:8000/ws');
    
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
        
        // Attempt to reconnect after 5 seconds
        setTimeout(initWebSocket, 5000);
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
}

// Initialize TradingView chart
function initChart() {
    const chartContainer = document.getElementById('tradingChart');
    
    chart = LightweightCharts.createChart(chartContainer, {
        width: chartContainer.clientWidth,
        height: 500,
        layout: {
            backgroundColor: '#0a0a0a',
            textColor: '#00ffff',
        },
        grid: {
            vertLines: { color: 'rgba(0, 255, 255, 0.1)' },
            horzLines: { color: 'rgba(0, 255, 255, 0.1)' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        priceScale: {
            borderColor: '#00ffff',
        },
        timeScale: {
            borderColor: '#00ffff',
            timeVisible: true,
        },
    });
    
    candlestickSeries = chart.addCandlestickSeries({
        upColor: '#39ff14',
        downColor: '#ff00ff',
        borderUpColor: '#39ff14',
        borderDownColor: '#ff00ff',
        wickUpColor: '#39ff14',
        wickDownColor: '#ff00ff',
    });
    
    volumeSeries = chart.addHistogramSeries({
        color: '#00ffff',
        priceFormat: {
            type: 'volume',
        },
        priceScaleId: '',
        scaleMargins: {
            top: 0.8,
            bottom: 0,
        },
    });
    
    strategyOverlay = chart.addLineSeries({
        color: 'rgba(0, 255, 242, 0.4)',
        lineWidth: 2,
        priceLineVisible: false,
    });
    
    return chart;
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'price_update':
            updateChart(data.candle);
            break;
            
        case 'strategy_signal':
            handleStrategySignal(data.signal);
            break;
            
        case 'trade_execution':
            handleTradeExecution(data.trade);
            break;
    }
}

// Update chart with new candle data
function updateChart(candle) {
    const candleData = {
        time: candle.timestamp / 1000,
        open: parseFloat(candle.open),
        high: parseFloat(candle.high),
        low: parseFloat(candle.low),
        close: parseFloat(candle.close),
    };
    
    const volumeData = {
        time: candle.timestamp / 1000,
        value: parseFloat(candle.volume),
        color: parseFloat(candle.close) >= parseFloat(candle.open) ? '#39ff14' : '#ff00ff',
    };
    
    candlestickSeries.update(candleData);
    volumeSeries.update(volumeData);
}

// Handle strategy signals
function handleStrategySignal(signal) {
    const signalMarker = {
        time: signal.timestamp / 1000,
        position: signal.action === 'buy' ? 'belowBar' : 'aboveBar',
        color: signal.action === 'buy' ? '#39ff14' : '#ff00ff',
        shape: signal.action === 'buy' ? 'arrowUp' : 'arrowDown',
        text: `${signal.strategy} (${Math.round(signal.confidence * 100)}%)`,
    };
    
    candlestickSeries.setMarkers([signalMarker]);
    updateStrategyPanel(signal);
}

// Update strategy panel with signal information
function updateStrategyPanel(signal) {
    const panel = document.getElementById('strategyPanel');
    
    let html = `
        <div class="strategy-header">
            <div class="cyber-text">${signal.strategy.toUpperCase()} SIGNAL</div>
            <div class="signal-confidence" style="color: ${signal.action === 'buy' ? 'var(--neon-green)' : 'var(--neon-pink)'}">
                ${Math.round(signal.confidence * 100)}% Confidence
            </div>
        </div>
        <div class="strategy-indicators">
    `;
    
    for (const [key, value] of Object.entries(signal.indicators)) {
        html += `
            <div class="indicator-item">
                <span class="indicator-name">${key.replace(/_/g, ' ').toUpperCase()}</span>
                <span class="indicator-value">${typeof value === 'number' ? value.toFixed(4) : value}</span>
            </div>
        `;
    }
    
    html += `</div>`;
    panel.innerHTML = html;
}

// Handle trade execution
function handleTradeExecution(trade) {
    tradeHistory.unshift(trade);
    updateTradeHistory();
}

// Update trade history display
function updateTradeHistory() {
    const container = document.getElementById('tradeHistory');
    let html = '';
    
    for (const trade of tradeHistory.slice(0, 10)) {
        html += `
            <div class="trade-item ${trade.side}">
                <span>${trade.timestamp}</span>
                <span>${trade.side.toUpperCase()}</span>
                <span>${trade.amount} XRP</span>
                <span>$${trade.price}</span>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// Event listeners
document.getElementById('toggleAutoTrading').addEventListener('click', function() {
    isAutoTrading = !isAutoTrading;
    this.textContent = isAutoTrading ? 'Stop Auto Trading' : 'Start Auto Trading';
    this.classList.toggle('active');
});

document.getElementById('manualBuy').addEventListener('click', function() {
    const amount = document.getElementById('tradeAmount').value;
    ws.send(JSON.stringify({
        type: 'manual_trade',
        action: 'buy',
        amount: amount,
        timestamp: Date.now(),
        price: candlestickSeries.lastPrice(),
    }));
});

document.getElementById('manualSell').addEventListener('click', function() {
    const amount = document.getElementById('tradeAmount').value;
    ws.send(JSON.stringify({
        type: 'manual_trade',
        action: 'sell',
        amount: amount,
        timestamp: Date.now(),
        price: candlestickSeries.lastPrice(),
    }));
});

// Initialize everything when the page loads
window.onload = function() {
    initChart();
    initWebSocket();
};
