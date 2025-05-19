
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

class SlippageModel:
    def __init__(self):
        # Initialize model
        self.model = LinearRegression()
        # Historical data for model training (would be accumulated in a real system)
        self.historical_data = []
    
    def train(self):
        """Train the slippage model on historical data"""
        if len(self.historical_data) < 5:
            return False
        
        # Extract features and targets
        X = np.array([[d['order_size'], d['market_depth'], d['volatility']] for d in self.historical_data])
        y = np.array([d['slippage'] for d in self.historical_data])
        
        # Train model
        self.model.fit(X, y)
        return True
    
    def predict(self, order_size, market_depth, volatility):
        """Predict slippage based on order parameters"""
        if len(self.historical_data) < 5:
            # Fall back to heuristic model if not enough data
            return order_size * 0.001 * (1 + volatility * 10) * (order_size / market_depth if market_depth > 0 else 0.01)
        
        # Use trained model
        X = np.array([[order_size, market_depth, volatility]])
        return max(0, self.model.predict(X)[0])
    
    def add_observation(self, order_size, market_depth, volatility, slippage):
        """Add an observation to historical data"""
        self.historical_data.append({
            'order_size': order_size,
            'market_depth': market_depth,
            'volatility': volatility,
            'slippage': slippage
        })
        
        # Limit size of historical data
        if len(self.historical_data) > 1000:
            self.historical_data.pop(0)

# Global model instance
_slippage_model = SlippageModel()

def estimate_slippage(bids, asks, quantity, mid_price):
    """
    Estimate slippage for a market order.
    
    Parameters:
    -----------
    bids : list
        List of bid price-quantity pairs [[price, quantity], ...]
    asks : list
        List of ask price-quantity pairs [[price, quantity], ...]
    quantity : float
        Order quantity in USD
    mid_price : float
        Current mid price
    
    Returns:
    --------
    float : Expected slippage in USD
    """
    # Calculate order size in base currency
    order_size_base = quantity / mid_price
    
    # Calculate market depth
    asks_cum = 0
    weighted_avg_price = 0
    remaining = order_size_base
    
    # Simulate market order execution
    for ask_price, ask_size in asks:
        ask_price = float(ask_price)
        ask_size = float(ask_size)
        
        if remaining <= 0:
            break
        
        executed = min(ask_size, remaining)
        weighted_avg_price += ask_price * executed
        asks_cum += executed
        remaining -= executed
    
    # If there's not enough liquidity, use the last price
    if remaining > 0 and asks:
        last_price = float(asks[-1][0])
        weighted_avg_price += last_price * remaining
        asks_cum += remaining
    
    # Calculate realized price
    if asks_cum > 0:
        realized_price = weighted_avg_price / asks_cum
    else:
        realized_price = mid_price
    
    # Calculate slippage
    slippage = (realized_price - mid_price) * order_size_base
    
    return max(0, slippage)  # Slippage cannot be negative
