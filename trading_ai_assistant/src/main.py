import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, 
    QLabel, QTabWidget, QGridLayout, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
import pyqtgraph as pg
import pyautogui
import logging
from dotenv import load_dotenv
import json
from rich.logging import RichHandler
from trading.strategy import TradingStrategy
from automation.controller import TradingController

# Configure logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)

class TradingAssistant(QMainWindow):
    def __init__(self, config_file="config/trading_config.json"):
        super().__init__()
        self.config = self.load_config(config_file)
        self.setup_ui()
        self.setup_trading_components()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_trading_data)
        self.update_timer.start(60000)  # Update every minute
    
    def load_config(self, config_file):
        """Load trading configuration"""
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def setup_trading_components(self):
        """Initialize trading strategy and controller"""
        self.strategy = TradingStrategy(
            symbol=self.config.get('symbol', 'BTC/USD'),
            interval='1m'
        )
        self.controller = TradingController()
        self.is_trading = False
    
    def setup_ui(self):
        """Setup the main user interface"""
        self.setWindowTitle("Trading AI Assistant")
        self.setGeometry(100, 100, 1200, 800)
        self.setup_style()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Add tabs
        tabs.addTab(self.create_trading_tab(), "Trading")
        tabs.addTab(self.create_chart_tab(), "Charts")
        tabs.addTab(self.create_settings_tab(), "Settings")
    
    def setup_style(self):
        """Setup dark theme and styling"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        
        self.setPalette(palette)
    
    def create_trading_tab(self):
        """Create the main trading interface tab"""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        # Status section
        self.status_label = QLabel("Status: Ready")
        self.status_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.status_label, 0, 0, 1, 2)
        
        # Trading controls
        self.start_button = QPushButton("Start Trading Assistant")
        self.start_button.clicked.connect(self.start_trading)
        self.start_button.setMinimumHeight(50)
        layout.addWidget(self.start_button, 1, 0)
        
        self.stop_button = QPushButton("Emergency Stop")
        self.stop_button.clicked.connect(self.emergency_stop)
        self.stop_button.setStyleSheet("background-color: #8B0000; color: white;")
        self.stop_button.setMinimumHeight(50)
        layout.addWidget(self.stop_button, 1, 1)
        
        # Trading information
        info_widget = QWidget()
        info_layout = QGridLayout(info_widget)
        
        labels = ["Symbol:", "Position:", "Last Price:", "P&L:"]
        self.info_labels = {}
        
        for i, label in enumerate(labels):
            info_layout.addWidget(QLabel(label), i, 0)
            value_label = QLabel("--")
            value_label.setStyleSheet("color: #00FF00;")
            info_layout.addWidget(value_label, i, 1)
            self.info_labels[label] = value_label
        
        layout.addWidget(info_widget, 2, 0, 1, 2)
        
        return widget
    
    def create_chart_tab(self):
        """Create the chart display tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Create price chart
        self.price_plot = pg.PlotWidget()
        self.price_plot.setBackground('k')
        self.price_plot.showGrid(x=True, y=True)
        layout.addWidget(self.price_plot)
        
        # Create volume chart
        self.volume_plot = pg.PlotWidget()
        self.volume_plot.setBackground('k')
        self.volume_plot.showGrid(x=True, y=True)
        layout.addWidget(self.volume_plot)
        
        return widget
    
    def create_settings_tab(self):
        """Create the settings configuration tab"""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        # Trading pair selection
        layout.addWidget(QLabel("Trading Pair:"), 0, 0)
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["BTC/USD", "ETH/USD", "BNB/USD"])
        layout.addWidget(self.symbol_combo, 0, 1)
        
        # Risk settings
        layout.addWidget(QLabel("Risk % per Trade:"), 1, 0)
        self.risk_input = QLineEdit()
        self.risk_input.setText(str(self.config.get('risk_percentage', 1)))
        layout.addWidget(self.risk_input, 1, 1)
        
        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button, 2, 0, 1, 2)
        
        return widget
    
    def start_trading(self):
        """Toggle trading state"""
        if not self.is_trading:
            self.is_trading = True
            self.status_label.setText("Status: Trading Active")
            self.start_button.setText("Pause Trading")
            self.start_button.setStyleSheet("background-color: #4CAF50; color: white;")
            logging.info("Trading assistant started")
            self.update_trading_data()
        else:
            self.is_trading = False
            self.status_label.setText("Status: Trading Paused")
            self.start_button.setText("Start Trading Assistant")
            self.start_button.setStyleSheet("")
            logging.info("Trading assistant paused")
    
    def emergency_stop(self):
        """Handle emergency stop"""
        self.is_trading = False
        self.status_label.setText("Status: EMERGENCY STOP ACTIVATED")
        self.start_button.setText("Start Trading Assistant")
        self.start_button.setStyleSheet("")
        logging.warning("Emergency stop activated")
    
    def update_trading_data(self):
        """Update trading data and charts"""
        if not self.is_trading:
            return
        
        try:
            # Fetch new data
            data = self.strategy.fetch_data(period='1d')
            
            # Update charts
            self.update_charts(data)
            
            # Update info labels
            last_price = data['Close'].iloc[-1]
            self.info_labels["Last Price:"].setText(f"${last_price:.2f}")
            self.info_labels["Symbol:"].setText(self.strategy.symbol)
            
            # Generate trading signals
            buy_signal, sell_signal = self.strategy.generate_signals()
            
            if buy_signal:
                logging.info("Buy signal generated")
                self.controller.execute_buy()
            elif sell_signal:
                logging.info("Sell signal generated")
                self.controller.execute_sell()
                
        except Exception as e:
            logging.error(f"Error updating trading data: {str(e)}")
            self.emergency_stop()
    
    def update_charts(self, data):
        """Update price and volume charts"""
        # Clear previous data
        self.price_plot.clear()
        self.volume_plot.clear()
        
        # Plot price data
        self.price_plot.plot(data.index, data['Close'], pen='w')
        
        # Plot volume data
        self.volume_plot.plot(data.index, data['Volume'], pen='b')
    
    def save_settings(self):
        """Save current settings to config file"""
        self.config['symbol'] = self.symbol_combo.currentText()
        self.config['risk_percentage'] = float(self.risk_input.text())
        
        os.makedirs('config', exist_ok=True)
        with open('config/trading_config.json', 'w') as f:
            json.dump(self.config, f, indent=4)
        
        logging.info("Settings saved successfully")

def start_application():
    """Start the trading assistant application"""
    load_dotenv()
    pyautogui.FAILSAFE = True
    app = QApplication(sys.argv)
    window = TradingAssistant()
    window.show()
    return app.exec()

if __name__ == "__main__":
    start_application()
