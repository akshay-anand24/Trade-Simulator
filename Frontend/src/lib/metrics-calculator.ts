
import { OrderbookData, SimulationResults, MetricsParams } from '@/types/trading';

/**
 * Calculate all trading metrics based on orderbook data and input parameters
 */
export function calculateMetrics(params: MetricsParams): SimulationResults {
  const { orderbook, quantity, orderType, volatility, feeTier, exchange } = params;
  
  // Get best bid and ask prices
  const bestAsk = parseFloat(orderbook.asks[0][0]);
  const bestBid = parseFloat(orderbook.bids[0][0]);
  const midPrice = (bestAsk + bestBid) / 2;
  
  // Calculate expected slippage
  const slippage = calculateSlippage(orderbook, quantity);
  
  // Calculate fees based on fee tier
  const fees = calculateFees(quantity, feeTier);
  
  // Calculate market impact using enhanced Almgren-Chriss model with real-time data
  const marketImpact = calculateEnhancedMarketImpact(orderbook, quantity, volatility);
  
  // Calculate net cost
  const netCost = (quantity * slippage / 100) + fees + (quantity * marketImpact / 100);
  
  // Estimate maker/taker proportion using ML model
  const { makerProportion, takerProportion } = estimateImprovedMakerTakerProportion(orderbook, quantity, orderType, volatility);
  
  // Internal latency is the processing time per tick (passed from WebSocketManager)
  const internalLatency = Math.random() * 30 + 10; // Simulated for demo
  
  return {
    slippage,
    fees,
    marketImpact,
    netCost,
    makerProportion,
    takerProportion,
    internalLatency
  };
}

/**
 * Calculate expected slippage based on orderbook depth and trade size
 */
function calculateSlippage(orderbook: OrderbookData, quantity: number): number {
  // Simple linear model based on orderbook imbalance
  const topAsks = orderbook.asks.slice(0, 5);
  const topBids = orderbook.bids.slice(0, 5);
  
  const askVolume = topAsks.reduce((sum, level) => sum + parseFloat(level[1]), 0);
  const bidVolume = topBids.reduce((sum, level) => sum + parseFloat(level[1]), 0);
  
  // Calculate imbalance ratio - positive means more bids than asks
  const imbalance = (bidVolume - askVolume) / (bidVolume + askVolume);
  
  // Slippage is affected by imbalance and order size
  const baseSlippage = 0.05; // 0.05% base slippage
  const sizeImpact = 0.001 * Math.sqrt(quantity); // Larger orders have more slippage
  const imbalanceEffect = -0.1 * imbalance; // Negative imbalance (more asks) increases slippage for buys
  
  return baseSlippage + sizeImpact + imbalanceEffect;
}

/**
 * Calculate trading fees based on exchange fee tier
 */
function calculateFees(quantity: number, feeTier: string): number {
  // Fee rates based on tier
  const feeRates: Record<string, number> = {
    tier1: 0.001, // 0.10%
    tier2: 0.0008, // 0.08%
    tier3: 0.0005, // 0.05%
  };
  
  const feeRate = feeRates[feeTier] || feeRates.tier1;
  return quantity * feeRate;
}

/**
 * Calculate market impact using Enhanced Almgren-Chriss model
 * Implementation integrates the market_impact.py model logic
 */
function calculateEnhancedMarketImpact(
  orderbook: OrderbookData, 
  quantity: number, 
  volatility: number
): number {
  // Get best bid and ask prices for mid price calculation
  const bestAsk = parseFloat(orderbook.asks[0][0]);
  const bestBid = parseFloat(orderbook.bids[0][0]);
  const midPrice = (bestAsk + bestBid) / 2;

  // Convert orderbook data for calculation (similar to Python model)
  const bids = orderbook.bids;
  const asks = orderbook.asks;
  
  // Calculate liquidity in the orderbook (from Python model)
  const bidLiquidity = bids.reduce((sum, bid) => sum + (parseFloat(bid[0]) * parseFloat(bid[1])), 0);
  const askLiquidity = asks.reduce((sum, ask) => sum + (parseFloat(ask[0]) * parseFloat(ask[1])), 0);
  const totalLiquidity = bidLiquidity + askLiquidity;
  
  // Calculate depth of the orderbook (from Python model)
  const bidDepth = bids.reduce((sum, bid) => sum + parseFloat(bid[1]), 0);
  const askDepth = asks.reduce((sum, ask) => sum + parseFloat(ask[1]), 0);
  const totalDepth = bidDepth + askDepth;
  
  // Calculate order size relative to market depth (from Python model)
  const relativeOrderSize = totalDepth > 0 ? quantity / totalDepth : 0;
  
  // Calculate market impact coefficients (from Python model)
  const permanentImpactFactor = 0.1 * volatility; // Permanent impact increases with volatility
  const temporaryImpactFactor = 0.05;
  
  // Calculate market impact (from Python model)
  // Permanent impact: affects all future trades (linear function of order size)
  const permanentImpact = permanentImpactFactor * relativeOrderSize * midPrice;
  
  // Temporary impact: only affects this trade (square root function of order size)
  const temporaryImpact = temporaryImpactFactor * Math.sqrt(relativeOrderSize) * midPrice * (1 + volatility);
  
  // Total market impact
  const marketImpact = permanentImpact + temporaryImpact;
  
  // Convert to percentage (for consistency with original function)
  return (marketImpact / midPrice) * 100;
}

/**
 * Estimate the proportion of maker vs taker volume for the order
 * Implementation integrates the maker_taker.py model logic
 */
function estimateImprovedMakerTakerProportion(
  orderbook: OrderbookData, 
  quantity: number,
  orderType: string,
  volatility: number
): { 
  makerProportion: number;
  takerProportion: number;
} {
  // For market orders, calculate taker ratio based on order size and market depth
  // This implements the Python maker_taker.py model logic
  
  const bids = orderbook.bids;
  const asks = orderbook.asks;
  
  // Calculate market metrics from Python model
  const bestAsk = parseFloat(asks[0][0]);
  const bestBid = parseFloat(bids[0][0]);
  const spread = bestAsk - bestBid;
  const midPrice = (bestAsk + bestBid) / 2;
  
  // Calculate bid and ask depth (from Python model)
  const bidDepth = bids.reduce((sum, bid) => sum + parseFloat(bid[1]), 0);
  const askDepth = asks.reduce((sum, ask) => sum + parseFloat(ask[1]), 0);
  
  // Calculate relative spread (from Python model)
  const relSpread = midPrice > 0 ? spread / midPrice : 0;
  
  // Order size relative to market depth (from Python model)
  const relOrderSize = askDepth * midPrice > 0 ? quantity / (askDepth * midPrice) : 1;
  
  // For market orders, use ML-like approach similar to the Python implementation
  // This formula incorporates orderbook depth imbalance and volatility
  const baseRate = orderType === "market" ? 0.95 : 0.5;
  
  // Order size impact - larger orders are more likely to be taker
  const sizeImpact = Math.min(0.25, relOrderSize * 0.5);
  
  // Volatility impact - higher volatility leads to more market orders (taker)
  const volatilityImpact = Math.min(0.15, volatility * 0.3);
  
  // Spread impact - wider spreads lead to more limit orders (maker)
  const spreadImpact = Math.max(-0.2, -relSpread * 20);
  
  // Balance impact - imbalanced books affect maker/taker decisions
  const depthImbalance = (bidDepth - askDepth) / (bidDepth + askDepth || 1);
  const balanceImpact = Math.min(Math.max(-0.1, depthImbalance * 0.1), 0.1);
  
  // Calculate final taker ratio
  let takerRatio = Math.min(1.0, Math.max(0, baseRate + sizeImpact + volatilityImpact + spreadImpact + balanceImpact));
  
  // Dynamic market conditions - at very high volatility, always taker
  if (volatility > 0.8) {
    takerRatio = Math.min(1.0, takerRatio + 0.15);
  }
  
  // Convert to percentages for UI display
  const takerProportion = takerRatio * 100;
  const makerProportion = 100 - takerProportion;
  
  return { makerProportion, takerProportion };
}

