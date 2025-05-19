
import numpy as np
from sklearn.linear_model import LogisticRegression

def predict_maker_taker_proportion(bids, asks, quantity):
    """
    Predict the maker/taker proportion for a trade.
    
    Parameters:
    -----------
    bids : list
        List of bid price-quantity pairs [[price, quantity], ...]
    asks : list
        List of ask price-quantity pairs [[price, quantity], ...]
    quantity : float
        Order quantity in USD
    
    Returns:
    --------
    tuple : (maker_ratio, taker_ratio)
    """
    # For market orders, typically 100% taker
    # But we'll use a more sophisticated model that considers market conditions
    
    # Convert to numpy arrays
    bid_prices = np.array([float(bid[0]) for bid in bids])
    bid_quantities = np.array([float(bid[1]) for bid in bids])
    ask_prices = np.array([float(ask[0]) for ask in asks])
    ask_quantities = np.array([float(ask[1]) for ask in asks])
    
    # Calculate market metrics
    spread = np.min(ask_prices) - np.max(bid_prices) if len(ask_prices) > 0 and len(bid_prices) > 0 else 0
    mid_price = (np.min(ask_prices) + np.max(bid_prices)) / 2 if len(ask_prices) > 0 and len(bid_prices) > 0 else 0
    bid_depth = np.sum(bid_quantities)
    ask_depth = np.sum(ask_quantities)
    
    # Relative spread
    rel_spread = spread / mid_price if mid_price > 0 else 0
    
    # Order size relative to market depth
    rel_order_size = quantity / (ask_depth * mid_price) if ask_depth * mid_price > 0 else 1
    
    # For market orders, calculate taker ratio based on order size and market depth
    # This is a simplified model - in reality, this would use historical data and ML
    taker_ratio = min(1.0, max(0.95, rel_order_size))
    maker_ratio = 1 - taker_ratio
    
    return maker_ratio, taker_ratio
