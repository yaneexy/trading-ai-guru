// Global variables
let ws;
let chart;
let candleSeries;
let volumeSeries;
let isAutoTrading = false;
let tradeHistory = [];

// Initialize chart
function initChart() {
    try {
        console.log('Initializing chart...');
        const chartContainer = document.getElementById('tradingChart');
        
        if (!chartContainer) {
            console.error('Chart container not found');
            return;
        }

        // Initialize TradingView chart
        chart = LightweightCharts.createChart(chartContainer, {
            width: chartContainer.clientWidth,
            height: 500,
            layout: {
                background: { color: '#000000' },
                textColor: '#DDD',
            },
            grid: {
                vertLines: { color: '#404040' },
                horzLines: { color: '#404040' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            priceScale: {
                borderColor: '#cccccc',
            },
            timeScale: {
                borderColor: '#cccccc',
                timeVisible: true,
            },
        });

        // Add candlestick series
        candleSeries = chart.addCandlestickSeries({
            upColor: '#00ff00',
            downColor: '#ff0000',
            borderDownColor: '#ff0000',
            borderUpColor: '#00ff00',
            wickDownColor: '#ff0000',
            wickUpColor: '#00ff00',
        });

        // Add volume series
        volumeSeries = chart.addHistogramSeries({
            color: '#26a69a',
            priceFormat: {
                type: 'volume',
            },
            priceScaleId: '',
            scaleMargins: {
                top: 0.8,
                bottom: 0,
            },
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            if (chart) {
                chart.applyOptions({
                    width: chartContainer.clientWidth
                });
            }
        });

        // Fetch initial data and start WebSocket
        fetchHistoricalData().then(() => {
            console.log('Historical data loaded');
            initWebSocket();
        });

    } catch (error) {
        console.error('Error initializing chart:', error);
        updateConnectionStatus('Error: ' + error.message);
    }
}

// Fetch historical data
async function fetchHistoricalData() {
    try {
        updateConnectionStatus('Loading historical data...');
        const response = await fetch('https://api.binance.com/api/v3/klines?symbol=XRPUSDT&interval=1m&limit=1000');
        const data = await response.json();
        
        const candleData = data.map(d => ({
            time: d[0] / 1000,
            open: parseFloat(d[1]),
            high: parseFloat(d[2]),
            low: parseFloat(d[3]),
            close: parseFloat(d[4]),
        }));

        const volumeData = data.map(d => ({
            time: d[0] / 1000,
            value: parseFloat(d[5]),
            color: parseFloat(d[4]) >= parseFloat(d[1]) ? 'rgba(0, 150, 136, 0.8)' : 'rgba(255,82,82, 0.8)',
        }));

        candleSeries.setData(candleData);
        volumeSeries.setData(volumeData);
        updateConnectionStatus('Historical data loaded');
    } catch (error) {
        console.error('Error fetching historical data:', error);
        updateConnectionStatus('Error loading data: ' + error.message);
    }
}

// Initialize WebSocket connection
function initWebSocket() {
    try {
        updateConnectionStatus('Connecting to WebSocket...');
        ws = new WebSocket('wss://stream.binance.com:9443/ws/xrpusdt@kline_1m');
        
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
                const candle = data.k;
                
                candleSeries.update({
                    time: candle.t / 1000,
                    open: parseFloat(candle.o),
                    high: parseFloat(candle.h),
                    low: parseFloat(candle.l),
                    close: parseFloat(candle.c)
                });

                volumeSeries.update({
                    time: candle.t / 1000,
                    value: parseFloat(candle.v),
                    color: parseFloat(candle.c) >= parseFloat(candle.o) ? 'rgba(0, 150, 136, 0.8)' : 'rgba(255,82,82, 0.8)',
                });
            } catch (error) {
                console.error('Error processing WebSocket message:', error);
            }
        };
    } catch (error) {
        console.error('Error initializing WebSocket:', error);
        updateConnectionStatus('Error: ' + error.message);
    }
}

// Update strategy panel with trading signals
function updateStrategyPanel(signal) {
    const panel = document.getElementById('strategyPanel');
    if (panel) {
        panel.innerHTML = `
            <div class="strategy-header">
                <div class="cyber-text">${signal}</div>
            </div>
        `;
    }
}

// Update trade history
function updateTradeHistory(trade) {
    tradeHistory.push(trade);
    // Implement trade history display if needed
}

// Update connection status
function updateConnectionStatus(status) {
    const statusElement = document.getElementById('connectionStatus');
    if (statusElement) {
        statusElement.textContent = status;
        if (status === 'Connected') {
            statusElement.classList.add('connected');
            statusElement.classList.remove('disconnected');
        } else {
            statusElement.classList.remove('connected');
            statusElement.classList.add('disconnected');
        }
    }
}

// Event listeners for trading controls
document.getElementById('toggleAutoTrading')?.addEventListener('click', function() {
    isAutoTrading = !isAutoTrading;
    this.textContent = isAutoTrading ? 'Stop Auto Trading' : 'Start Auto Trading';
    updateStrategyPanel(isAutoTrading ? 'Auto Trading Active' : 'Auto Trading Disabled');
});

document.getElementById('manualBuy')?.addEventListener('click', function() {
    const amount = document.getElementById('tradeAmount')?.value || '100';
    updateStrategyPanel('Manual Buy Signal');
    updateTradeHistory({
        type: 'BUY',
        price: candleSeries.lastPrice(),
        amount: parseFloat(amount)
    });
});

document.getElementById('manualSell')?.addEventListener('click', function() {
    const amount = document.getElementById('tradeAmount')?.value || '100';
    updateStrategyPanel('Manual Sell Signal');
    updateTradeHistory({
        type: 'SELL',
        price: candleSeries.lastPrice(),
        amount: parseFloat(amount)
    });
});

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', initChart);
