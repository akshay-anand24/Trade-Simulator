
import numpy as np
import pandas as pd

def calculate_market_impact(bids, asks, quantity, volatility, mid_price):
    """
    Calculate the market impact using the Almgren-Chriss model.
    
    Parameters:
    -----------
    bids : list
        List of bid price-quantity pairs [[price, quantity], ...]
    asks : list
        List of ask price-quantity pairs [[price, quantity], ...]
    quantity : float
        Order quantity in USD
    volatility : float
        Market volatility as a decimal (0.01 = 1%)
    mid_price : float
        Current mid price
    
    Returns:
    --------
    float : Expected market impact in USD
    """
    # Convert to numpy arrays for efficient calculation
    bid_prices = np.array([float(bid[0]) for bid in bids])
    bid_quantities = np.array([float(bid[1]) for bid in bids])
    ask_prices = np.array([float(ask[0]) for ask in asks])
    ask_quantities = np.array([float(ask[1]) for ask in asks])
    
    # Calculate liquidity in the orderbook
    bid_liquidity = np.sum(bid_prices * bid_quantities)
    ask_liquidity = np.sum(ask_prices * ask_quantities)
    total_liquidity = bid_liquidity + ask_liquidity
    
    # Calculate depth of the orderbook
    bid_depth = np.sum(bid_quantities)
    ask_depth = np.sum(ask_quantities)
    total_depth = bid_depth + ask_depth
    
    # Calculate order size relative to market depth
    relative_order_size = quantity / total_depth if total_depth > 0 else 0
    
    # Calculate market impact coefficients
    # These are simplified coefficients based on Almgren-Chriss model
    # In a production system, these would be calibrated based on historical data
    permanent_impact_factor = 0.1 * volatility  # Permanent impact increases with volatility
    temporary_impact_factor = 0.05
    
    # Calculate market impact
    # Permanent impact: affects all future trades (linear function of order size)
    permanent_impact = permanent_impact_factor * relative_order_size * mid_price
    
    # Temporary impact: only affects this trade (square root function of order size)
    temporary_impact = temporary_impact_factor * np.sqrt(relative_order_size) * mid_price * (1 + volatility)
    
    # Total market impact
    market_impact = permanent_impact + temporary_impact
    
    # Convert to USD
    market_impact_usd = market_impact * (quantity / mid_price)
    
    return market_impact_usd
