
def calculate_fees(quantity, fee_tier):
    """
    Calculate trading fees based on the fee tier.
    
    Parameters:
    -----------
    quantity : float
        Order quantity in USD
    fee_tier : str
        Fee tier (VIP 0, VIP 1, etc.)
    
    Returns:
    --------
    float : Expected fees in USD
    """
    # OKX fee tiers (as of May 2025)
    fee_schedule = {
        "VIP 0": {"maker": 0.0008, "taker": 0.0010},
        "VIP 1": {"maker": 0.0006, "taker": 0.0008},
        "VIP 2": {"maker": 0.0004, "taker": 0.0007},
        "VIP 3": {"maker": 0.0002, "taker": 0.0006},
        "VIP 4": {"maker": 0.0000, "taker": 0.0005},
    }
    
    # For market orders, we use taker fees
    if fee_tier in fee_schedule:
        taker_fee_rate = fee_schedule[fee_tier]["taker"]
    else:
        # Default to VIP 0 if fee tier not found
        taker_fee_rate = 0.0010
    
    # Calculate fees
    fees = quantity * taker_fee_rate
    
    return fees
