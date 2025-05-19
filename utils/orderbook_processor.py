
import numpy as np
import pandas as pd
from datetime import datetime
import json

class OrderbookProcessor:
    def __init__(self):
        self.bids = []
        self.asks = []
        self.timestamp = None
        self.exchange = None
        self.symbol = None
        self.mid_price = None
        self.spread = None
        self.update_count = 0
        self.historical_mid_prices = []
    
    def update(self, data):
        """
        Update the orderbook with new data.
        
        Parameters:
        -----------
        data : dict
            Orderbook data from WebSocket
        """
        try:
            self.timestamp = data.get("timestamp", datetime.now().isoformat())
            self.exchange = data.get("exchange")
            self.symbol = data.get("symbol")
            
            # Update bids and asks
            if "bids" in data:
                self.bids = data["bids"]
            
            if "asks" in data:
                self.asks = data["asks"]
            
            # Sort bids and asks
            if self.bids:
                self.bids.sort(key=lambda x: float(x[0]), reverse=True)
            
            if self.asks:
                self.asks.sort(key=lambda x: float(x[0]))
            
            # Calculate mid price and spread
            if self.bids and self.asks:
                best_bid = float(self.bids[0][0])
                best_ask = float(self.asks[0][0])
                self.mid_price = (best_bid + best_ask) / 2
                self.spread = best_ask - best_bid
                
                # Store historical mid prices (for volatility calculation)
                self.historical_mid_prices.append(self.mid_price)
                if len(self.historical_mid_prices) > 100:
                    self.historical_mid_prices.pop(0)
            
            self.update_count += 1
            
            return True
        except Exception as e:
            print(f"Error updating orderbook: {e}")
            return False
    
    def get_bids(self):
        """Get current bids"""
        return self.bids
    
    def get_asks(self):
        """Get current asks"""
        return self.asks
    
    def get_mid_price(self):
        """Get current mid price"""
        return self.mid_price
    
    def get_spread(self):
        """Get current spread"""
        return self.spread
    
    def calculate_volatility(self, window=20):
        """
        Calculate recent price volatility.
        
        Parameters:
        -----------
        window : int
            Number of recent mid prices to use
        
        Returns:
        --------
        float : Volatility as standard deviation / mean
        """
        if len(self.historical_mid_prices) < window:
            return 0.0
        
        recent_prices = self.historical_mid_prices[-window:]
        return np.std(recent_prices) / np.mean(recent_prices) if np.mean(recent_prices) > 0 else 0.0
    
    def to_dict(self):
        """Convert current state to dictionary"""
        return {
            "timestamp": self.timestamp,
            "exchange": self.exchange,
            "symbol": self.symbol,
            "mid_price": self.mid_price,
            "spread": self.spread,
            "best_bid": self.bids[0] if self.bids else None,
            "best_ask": self.asks[0] if self.asks else None,
            "bid_depth": sum(float(bid[1]) for bid in self.bids) if self.bids else 0,
            "ask_depth": sum(float(ask[1]) for ask in self.asks) if self.asks else 0,
            "update_count": self.update_count,
            "volatility": self.calculate_volatility()
        }
