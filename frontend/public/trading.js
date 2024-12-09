// Global variables
let ws;
let chart;
let candleSeries;
let volumeSeries;
let isAutoTrading = false;
let tradeHistory = [];
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 5000;

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

        // Start the initialization process
        startDataStream();

    } catch (error) {
        console.error('Error initializing chart:', error);
        updateConnectionStatus('Error: ' + error.message);
    }
}

// Start data stream
async function startDataStream() {
    try {
        await fetchHistoricalData();
        console.log('Historical data loaded');
        initWebSocket();
    } catch (error) {
        console.error('Error starting data stream:', error);
        updateConnectionStatus('Error: Failed to start data stream. Retrying...');
        setTimeout(startDataStream, RECONNECT_DELAY);
    }
}

// Fetch historical data
async function fetchHistoricalData() {
    try {
        updateConnectionStatus('Loading historical data...');
        const response = await fetch('https://api.binance.com/api/v3/klines?symbol=XRPUSDT&interval=1m&limit=1000');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!Array.isArray(data) || data.length === 0) {
            throw new Error('Invalid data received from API');
        }

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
        throw error; // Propagate error to be handled by startDataStream
    }
}

// Initialize WebSocket connection
function initWebSocket() {
    try {
        if (ws) {
            ws.close();
            ws = null;
        }

        updateConnectionStatus('Connecting to WebSocket...');
        ws = new WebSocket('wss://stream.binance.com:9443/ws/xrpusdt@kline_1m');
        
        ws.onopen = () => {
            console.log('WebSocket connected');
            updateConnectionStatus('Connected');
            reconnectAttempts = 0; // Reset reconnect attempts on successful connection
        };
        
        ws.onclose = (event) => {
            console.log('WebSocket disconnected:', event.code, event.reason);
            updateConnectionStatus('Disconnected');
            
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                updateConnectionStatus(`Reconnecting (Attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
                setTimeout(initWebSocket, RECONNECT_DELAY);
            } else {
                updateConnectionStatus('Connection failed. Please refresh the page.');
            }
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateConnectionStatus('Connection error. Attempting to reconnect...');
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (!data.k) {
                    console.error('Invalid message format:', data);
                    return;
                }

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
        
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            setTimeout(initWebSocket, RECONNECT_DELAY);
        }
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
        statusElement.className = 'connection-status';
        
        if (status === 'Connected') {
            statusElement.classList.add('connected');
        } else if (status.includes('Error') || status === 'Disconnected') {
            statusElement.classList.add('disconnected');
        } else {
            statusElement.classList.add('connecting');
        }
    }
}

// Initialize everything when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing chart...');
    initChart();
});

// Event listeners for trading controls
document.getElementById('toggleAutoTrading')?.addEventListener('click', () => {
    isAutoTrading = !isAutoTrading;
    const button = document.getElementById('toggleAutoTrading');
    if (button) {
        button.textContent = isAutoTrading ? 'Stop Auto Trading' : 'Start Auto Trading';
        updateStrategyPanel(isAutoTrading ? 'AUTO TRADING ENABLED' : 'AUTO TRADING DISABLED');
    }
});

document.getElementById('manualBuy')?.addEventListener('click', () => {
    const amount = document.getElementById('tradeAmount')?.value || '100';
    updateStrategyPanel('Manual Buy Signal');
    updateTradeHistory({
        type: 'BUY',
        price: candleSeries.lastPrice(),
        amount: parseFloat(amount)
    });
});

document.getElementById('manualSell')?.addEventListener('click', () => {
    const amount = document.getElementById('tradeAmount')?.value || '100';
    updateStrategyPanel('Manual Sell Signal');
    updateTradeHistory({
        type: 'SELL',
        price: candleSeries.lastPrice(),
        amount: parseFloat(amount)
    });
});
