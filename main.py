import os
import sys
import json
import time
import threading
from datetime import datetime
import websocket
import numpy as np
import subprocess
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QLineEdit, QPushButton, QDoubleSpinBox,
    QSpinBox, QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QTabWidget, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont, QPalette, QColor, QBrush
import pyqtgraph as pg

# Import our modules
from models.market_impact import calculate_market_impact
from models.slippage import estimate_slippage
from models.fees import calculate_fees
from models.maker_taker import predict_maker_taker_proportion
from utils.orderbook_processor import OrderbookProcessor

class WebSocketThread(QThread):
    message_received = pyqtSignal(dict)
    connection_error = pyqtSignal(str)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.running = True
    
    def run(self):
        def on_message(ws, message):
            try:
                data = json.loads(message)
                self.message_received.emit(data)
            except Exception as e:
                print(f"Error processing message: {e}")
        
        def on_error(ws, error):
            print(f"WebSocket error: {error}")
            self.connection_error.emit(str(error))
        
        def on_close(ws, close_status_code, close_msg):
            print("WebSocket connection closed")
        
        def on_open(ws):
            print("WebSocket connection opened")
        
        while self.running:
            try:
                ws = websocket.WebSocketApp(
                    self.url,
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close,
                    on_open=on_open
                )
                ws.run_forever()
                if not self.running:
                    break
                time.sleep(5)  # Wait before reconnecting
            except Exception as e:
                print(f"Connection attempt failed: {e}")
                time.sleep(5)  # Wait before reconnecting
    
    def stop(self):
        self.running = False
        self.wait()

class OrderbookVisualizerWidget(QWidget):
    """Enhanced orderbook visualization widget with advanced PyQt5 features"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Create tab widget for different visualization options
        self.tabs = QTabWidget()
        
        # Tab 1: Bar Chart Visualization
        self.bar_chart_tab = QWidget()
        self.bar_chart_layout = QVBoxLayout(self.bar_chart_tab)
        
        # Create pyqtgraph plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('k')  # black background
        self.plot_widget.setTitle("Orderbook Depth", color='w', size='14pt')
        self.plot_widget.setLabel('left', 'Quantity', color='w', size='12pt')
        self.plot_widget.setLabel('bottom', 'Price', color='w', size='12pt')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Create bid and ask bars
        self.bid_bars = pg.BarGraphItem(x=[], height=[], width=0.1, brush='g')
        self.ask_bars = pg.BarGraphItem(x=[], height=[], width=0.1, brush='r')
        self.plot_widget.addItem(self.bid_bars)
        self.plot_widget.addItem(self.ask_bars)
        
        # Add indicator for current price
        self.price_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', width=1))
        self.plot_widget.addItem(self.price_line)
        
        # Summary labels
        self.summary_label = QLabel("Waiting for orderbook data...")
        self.summary_label.setStyleSheet("color: white;")
        
        # Add to layout
        self.bar_chart_layout.addWidget(self.plot_widget)
        self.bar_chart_layout.addWidget(self.summary_label)
        
        # Tab 2: Heatmap Visualization
        self.heatmap_tab = QWidget()
        self.heatmap_layout = QVBoxLayout(self.heatmap_tab)
        
        # Create heatmap view
        self.heatmap_view = pg.ImageView()
        self.heatmap_view.setColorMap(pg.colormap.get('viridis'))
        self.heatmap_layout.addWidget(self.heatmap_view)
        
        # Tab 3: Raw Data
        self.raw_data_tab = QWidget()
        self.raw_data_layout = QVBoxLayout(self.raw_data_tab)
        
        # Create tables for bids and asks
        self.bids_table = QTableWidget(0, 3)
        self.bids_table.setHorizontalHeaderLabels(["Price", "Size", "Total"])
        self.bids_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.bids_table.setStyleSheet("color: white; background-color: #222;")
        
        self.asks_table = QTableWidget(0, 3)
        self.asks_table.setHorizontalHeaderLabels(["Price", "Size", "Total"])
        self.asks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.asks_table.setStyleSheet("color: white; background-color: #222;")
        
        # Add labels and tables
        self.raw_data_layout.addWidget(QLabel("Asks (Sell Orders)"))
        self.raw_data_layout.addWidget(self.asks_table)
        self.raw_data_layout.addWidget(QLabel("Bids (Buy Orders)"))
        self.raw_data_layout.addWidget(self.bids_table)
        
        # Add tabs to tab widget
        self.tabs.addTab(self.bar_chart_tab, "Bar Chart")
        self.tabs.addTab(self.heatmap_tab, "Heatmap")
        self.tabs.addTab(self.raw_data_tab, "Raw Data")
        self.tabs.setStyleSheet("color: white; background-color: #333;")
        
        # Add tab widget to main layout
        self.layout.addWidget(self.tabs)
        
        # Set up styling
        self.setStyleSheet("background-color: #222; color: white;")
    
    def update_visualization(self, bids, asks, mid_price=None):
        """Update the visualization with new orderbook data"""
        if not bids or not asks:
            return
        
        # Extract data
        bid_prices = [float(bid[0]) for bid in bids[:20]]
        bid_quantities = [float(bid[1]) for bid in bids[:20]]
        ask_prices = [float(ask[0]) for ask in asks[:20]]
        ask_quantities = [float(ask[1]) for ask in asks[:20]]
        
        # Update bar chart
        self.bid_bars.setOpts(x=bid_prices, height=bid_quantities, width=(max(bid_prices) - min(bid_prices))/50 if len(bid_prices) > 1 else 0.1)
        self.ask_bars.setOpts(x=ask_prices, height=ask_quantities, width=(max(ask_prices) - min(ask_prices))/50 if len(ask_prices) > 1 else 0.1)
        
        # Set price line
        if mid_price:
            self.price_line.setValue(mid_price)
        
        # Auto-scale the view
        self.plot_widget.autoRange()
        
        # Update heatmap
        # Create a 2D array for the heatmap
        all_prices = sorted(bid_prices + ask_prices)
        price_range = max(all_prices) - min(all_prices)
        price_step = price_range / 100 if price_range > 0 else 0.1
        
        heatmap_data = np.zeros((100, 2))  # 100 price levels, 2 columns (bid/ask)
        
        for i, price in enumerate(np.linspace(min(all_prices), max(all_prices), 100)):
            # Sum bid quantities for this price level
            bid_quantity = sum(qty for p, qty in zip(bid_prices, bid_quantities) if abs(float(p) - price) < price_step)
            # Sum ask quantities for this price level
            ask_quantity = sum(qty for p, qty in zip(ask_prices, ask_quantities) if abs(float(p) - price) < price_step)
            
            heatmap_data[i, 0] = bid_quantity
            heatmap_data[i, 1] = ask_quantity
        
        # Normalize data
        max_val = np.max(heatmap_data) if np.max(heatmap_data) > 0 else 1
        heatmap_data = heatmap_data / max_val
        
        # Update heatmap view
        self.heatmap_view.setImage(heatmap_data.T)  # Transpose to show price on y-axis
        
        # Update raw data tables
        self.update_tables(bids, asks)
        
        # Update summary
        spread = float(asks[0][0]) - float(bids[0][0]) if asks and bids else 0
        self.summary_label.setText(
            f"Mid Price: {mid_price:.2f} | Spread: {spread:.2f} | "
            f"Best Bid: {bids[0][0]} ({bids[0][1]}) | Best Ask: {asks[0][0]} ({asks[0][1]})"
        )
    
    def update_tables(self, bids, asks):
        """Update the raw data tables"""
        # Update asks table
        self.asks_table.setRowCount(min(len(asks), 10))
        for i, ask in enumerate(asks[:10]):
            price = float(ask[0])
            quantity = float(ask[1])
            total = price * quantity
            
            self.asks_table.setItem(i, 0, QTableWidgetItem(f"{price:.2f}"))
            self.asks_table.setItem(i, 1, QTableWidgetItem(f"{quantity:.4f}"))
            self.asks_table.setItem(i, 2, QTableWidgetItem(f"{total:.2f}"))
            
            # Set color
            for j in range(3):
                item = self.asks_table.item(i, j)
                item.setForeground(QBrush(QColor(255, 100, 100)))
        
        # Update bids table
        self.bids_table.setRowCount(min(len(bids), 10))
        for i, bid in enumerate(bids[:10]):
            price = float(bid[0])
            quantity = float(bid[1])
            total = price * quantity
            
            self.bids_table.setItem(i, 0, QTableWidgetItem(f"{price:.2f}"))
            self.bids_table.setItem(i, 1, QTableWidgetItem(f"{quantity:.4f}"))
            self.bids_table.setItem(i, 2, QTableWidgetItem(f"{total:.2f}"))
            
            # Set color
            for j in range(3):
                item = self.bids_table.item(i, j)
                item.setForeground(QBrush(QColor(100, 255, 100)))

class PerformanceMetricsWidget(QWidget):
    """Widget to display performance metrics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Create metrics grid
        metrics_group = QGroupBox("System Performance")
        metrics_layout = QGridLayout()
        
        # Add metric labels
        metrics_layout.addWidget(QLabel("Processing Time:"), 0, 0)
        self.processing_time_label = QLabel("N/A")
        metrics_layout.addWidget(self.processing_time_label, 0, 1)
        
        metrics_layout.addWidget(QLabel("Update Frequency:"), 1, 0)
        self.update_frequency_label = QLabel("N/A")
        metrics_layout.addWidget(self.update_frequency_label, 1, 1)
        
        metrics_layout.addWidget(QLabel("Memory Usage:"), 2, 0)
        self.memory_usage_label = QLabel("N/A")
        metrics_layout.addWidget(self.memory_usage_label, 2, 1)
        
        metrics_group.setLayout(metrics_layout)
        
        # Create performance plot
        plot_group = QGroupBox("Latency History")
        plot_layout = QVBoxLayout()
        
        self.performance_plot = pg.PlotWidget()
        self.performance_plot.setBackground('k')
        self.performance_plot.setLabel('left', 'Processing Time (ms)')
        self.performance_plot.setLabel('bottom', 'Updates')
        self.performance_plot.showGrid(x=True, y=True, alpha=0.3)
        self.performance_curve = self.performance_plot.plot(pen='y')
        
        plot_layout.addWidget(self.performance_plot)
        plot_group.setLayout(plot_layout)
        
        # Add widgets to layout
        self.layout.addWidget(metrics_group)
        self.layout.addWidget(plot_group)
        
        # Set styling
        self.setStyleSheet("background-color: #222; color: white;")
    
    def update_metrics(self, processing_time, update_frequency, processing_times):
        """Update performance metrics displays"""
        self.processing_time_label.setText(f"{processing_time:.2f} ms")
        self.update_frequency_label.setText(f"{update_frequency:.2f} Hz")
        
        # Update memory usage (simple approximation)
        import psutil
        process = psutil.Process()
        memory_usage = process.memory_info().rss / (1024 * 1024)  # MB
        self.memory_usage_label.setText(f"{memory_usage:.2f} MB")
        
        # Update performance plot
        if processing_times:
            self.performance_curve.setData(processing_times)

class TradingSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.orderbook_processor = OrderbookProcessor()
        self.orderbook_data = None
        self.last_update_time = None
        self.processing_times = []
        
        # Set up the main UI
        self.init_ui()
        
        # Start WebSocket connection
        self.start_websocket()
        
        # Setup timer for UI updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(100)  # Update every 100ms
    
    def init_ui(self):
        self.setWindowTitle("High-Performance Trading Simulator")
        self.setGeometry(100, 100, 1280, 720)
        
        # Set up dark theme
        self.setup_dark_theme()
        
        # Main layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel (inputs)
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Input parameters group
        input_group = QGroupBox("Input Parameters")
        input_layout = QGridLayout()
        input_group.setLayout(input_layout)
        
        # Exchange
        input_layout.addWidget(QLabel("Exchange:"), 0, 0)
        self.exchange_combo = QComboBox()
        self.exchange_combo.addItem("OKX")
        input_layout.addWidget(self.exchange_combo, 0, 1)
        
        # Asset
        input_layout.addWidget(QLabel("Spot Asset:"), 1, 0)
        self.asset_combo = QComboBox()
        self.asset_combo.addItems(["BTC-USDT", "ETH-USDT", "SOL-USDT"])
        self.asset_combo.currentTextChanged.connect(self.on_asset_changed)
        input_layout.addWidget(self.asset_combo, 1, 1)
        
        # Order Type
        input_layout.addWidget(QLabel("Order Type:"), 2, 0)
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItem("market")
        input_layout.addWidget(self.order_type_combo, 2, 1)
        
        # Quantity
        input_layout.addWidget(QLabel("Quantity (USD):"), 3, 0)
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(1, 10000)
        self.quantity_spin.setValue(100)
        self.quantity_spin.setSingleStep(10)
        input_layout.addWidget(self.quantity_spin, 3, 1)
        
        # Volatility
        input_layout.addWidget(QLabel("Volatility (%):"), 4, 0)
        self.volatility_spin = QDoubleSpinBox()
        self.volatility_spin.setRange(0.1, 200)
        self.volatility_spin.setValue(5.0)
        self.volatility_spin.setSingleStep(0.5)
        input_layout.addWidget(self.volatility_spin, 4, 1)
        
        # Fee Tier
        input_layout.addWidget(QLabel("Fee Tier:"), 5, 0)
        self.fee_tier_combo = QComboBox()
        self.fee_tier_combo.addItems(["VIP 0", "VIP 1", "VIP 2", "VIP 3", "VIP 4"])
        input_layout.addWidget(self.fee_tier_combo, 5, 1)
        
        # Add run button
        self.run_button = QPushButton("Run Simulation")
        self.run_button.clicked.connect(self.run_simulation)
        input_layout.addWidget(self.run_button, 6, 0, 1, 2)
        
        left_layout.addWidget(input_group)
        
        # Add the enhanced orderbook visualizer to the left panel
        self.orderbook_visualizer = OrderbookVisualizerWidget()
        left_layout.addWidget(self.orderbook_visualizer)
        
        # Right panel (outputs)
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Output parameters group
        output_group = QGroupBox("Simulation Results")
        output_layout = QGridLayout()
        output_group.setLayout(output_layout)
        
        # Output fields
        output_layout.addWidget(QLabel("Expected Slippage:"), 0, 0)
        self.slippage_label = QLabel("N/A")
        output_layout.addWidget(self.slippage_label, 0, 1)
        
        output_layout.addWidget(QLabel("Expected Fees:"), 1, 0)
        self.fees_label = QLabel("N/A")
        output_layout.addWidget(self.fees_label, 1, 1)
        
        output_layout.addWidget(QLabel("Expected Market Impact:"), 2, 0)
        self.market_impact_label = QLabel("N/A")
        output_layout.addWidget(self.market_impact_label, 2, 1)
        
        output_layout.addWidget(QLabel("Net Cost:"), 3, 0)
        self.net_cost_label = QLabel("N/A")
        output_layout.addWidget(self.net_cost_label, 3, 1)
        
        output_layout.addWidget(QLabel("Maker/Taker Proportion:"), 4, 0)
        self.maker_taker_label = QLabel("N/A")
        output_layout.addWidget(self.maker_taker_label, 4, 1)
        
        right_layout.addWidget(output_group)
        
        # Add performance metrics widget
        self.performance_metrics = PerformanceMetricsWidget()
        right_layout.addWidget(self.performance_metrics)
        
        # Add simulation log
        log_group = QGroupBox("Simulation Log")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #111; color: #ddd;")
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 600])  # Initial sizes
        
        self.statusBar().showMessage("Ready")
        self.show()
    
    def log_message(self, message):
        """Add a message to the simulation log"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_text.append(f"[{timestamp}] {message}")
        # Scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def setup_dark_theme(self):
        dark_palette = QPalette()
        dark_color = QColor(53, 53, 53)
        dark_palette.setColor(QPalette.Window, dark_color)
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, dark_color)
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, dark_color)
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        
        self.setPalette(dark_palette)
    
    def start_websocket(self):
        # Set up WebSocket connection
        asset = self.asset_combo.currentText().replace('-', '')
        url = f"wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP"
        self.ws_thread = WebSocketThread(url)
        self.ws_thread.message_received.connect(self.on_websocket_message)
        self.ws_thread.connection_error.connect(self.on_websocket_error)
        self.ws_thread.start()
        self.statusBar().showMessage("Connecting to WebSocket...")
        self.log_message(f"Connecting to {url}...")
    
    def on_asset_changed(self):
        # Restart WebSocket with new asset
        if hasattr(self, 'ws_thread'):
            self.ws_thread.stop()
        self.start_websocket()
        self.log_message(f"Asset changed to {self.asset_combo.currentText()}")
    
    def on_websocket_message(self, data):
        start_time = time.time()
        
        # Process orderbook data
        self.orderbook_data = data
        self.orderbook_processor.update(data)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # in ms
        self.processing_times.append(processing_time)
        if len(self.processing_times) > 100:
            self.processing_times.pop(0)
        
        # Update last update time
        self.last_update_time = datetime.now()
        
        # Update status
        self.statusBar().showMessage(f"Last update: {self.last_update_time.strftime('%H:%M:%S.%f')[:-3]}")
    
    def on_websocket_error(self, error_msg):
        self.statusBar().showMessage(f"WebSocket error: {error_msg}")
        self.log_message(f"ERROR: WebSocket error: {error_msg}")
    
    def update_ui(self):
        if not self.orderbook_data:
            return
        
        # Update orderbook visualization
        bids = self.orderbook_processor.get_bids()
        asks = self.orderbook_processor.get_asks()
        
        if len(bids) > 0 and len(asks) > 0:
            # Get mid price
            mid_price = self.orderbook_processor.get_mid_price()
            
            # Update visualizer
            self.orderbook_visualizer.update_visualization(bids, asks, mid_price)
        
        # Calculate update frequency
        update_frequency = 0
        if self.last_update_time:
            time_diff = (datetime.now() - self.last_update_time).total_seconds()
            if time_diff < 5:  # Only show if recent
                update_frequency = 1 / time_diff if time_diff > 0 else 0
        
        # Update performance metrics
        if self.processing_times:
            avg_time = sum(self.processing_times) / len(self.processing_times)
            self.performance_metrics.update_metrics(avg_time, update_frequency, self.processing_times)
    
    def run_simulation(self):
        if not self.orderbook_data:
            self.statusBar().showMessage("No orderbook data available. Please wait for data.")
            self.log_message("ERROR: No orderbook data available. Please wait for data.")
            return
        
        try:
            # Get input parameters
            quantity = self.quantity_spin.value()
            volatility = self.volatility_spin.value() / 100.0  # Convert to decimal
            fee_tier = self.fee_tier_combo.currentText()
            
            # Get orderbook data
            bids = self.orderbook_processor.get_bids()
            asks = self.orderbook_processor.get_asks()
            
            if not bids or not asks:
                self.statusBar().showMessage("Insufficient orderbook data for simulation.")
                self.log_message("ERROR: Insufficient orderbook data for simulation.")
                return
            
            # Calculate mid price
            mid_price = (float(asks[0][0]) + float(bids[0][0])) / 2
            
            # Start timer for performance measurement
            start_time = time.time()
            
            # Calculate expected slippage
            slippage = estimate_slippage(bids, asks, quantity, mid_price)
            self.slippage_label.setText(f"{slippage:.4f} USD ({(slippage/quantity)*100:.4f}%)")
            
            # Calculate expected fees
            fees = calculate_fees(quantity, fee_tier)
            self.fees_label.setText(f"{fees:.4f} USD ({(fees/quantity)*100:.4f}%)")
            
            # Calculate expected market impact
            market_impact = calculate_market_impact(bids, asks, quantity, volatility, mid_price)
            self.market_impact_label.setText(f"{market_impact:.4f} USD ({(market_impact/quantity)*100:.4f}%)")
            
            # Calculate net cost
            net_cost = slippage + fees + market_impact
            self.net_cost_label.setText(f"{net_cost:.4f} USD ({(net_cost/quantity)*100:.4f}%)")
            
            # Predict maker/taker proportion
            maker_ratio, taker_ratio = predict_maker_taker_proportion(bids, asks, quantity)
            self.maker_taker_label.setText(f"Maker: {maker_ratio*100:.2f}% | Taker: {taker_ratio*100:.2f}%")
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000  # in ms
            
            # Add success message to log
            self.log_message(f"Simulation completed in {processing_time:.2f}ms")
            self.log_message(f"Order: {quantity} USD at {mid_price} (Volatility: {volatility:.4f})")
            self.log_message(f"Results: Slippage {slippage:.4f} USD, Fees {fees:.4f} USD, Impact {market_impact:.4f} USD")
            self.log_message(f"Total Cost: {net_cost:.4f} USD ({(net_cost/quantity)*100:.4f}%)")
            
            self.statusBar().showMessage(f"Simulation completed successfully in {processing_time:.2f}ms")
        except Exception as e:
            self.statusBar().showMessage(f"Simulation error: {str(e)}")
            self.log_message(f"ERROR in simulation: {str(e)}")
            import traceback
            self.log_message(traceback.format_exc())
    
    def closeEvent(self, event):
        if hasattr(self, 'ws_thread'):
            self.ws_thread.stop()
        event.accept()

def run_npm_dev():

    # Run `npm run dev` inside the Frontend folder
    current_dir = os.getcwd()  # get current directory
    frontend_dir = os.path.join(current_dir, "Frontend")

    print("Starting Frontend folder...")
    subprocess.run([r"C:\Program Files\nodejs\npm.cmd", "run", "dev"], cwd="Frontend", check=True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    simulator = TradingSimulator()
    # run_npm_dev()
    sys.exit(app.exec_())
