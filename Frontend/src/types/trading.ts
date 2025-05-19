
export interface OrderbookData {
  timestamp: string;
  exchange: string;
  symbol: string;
  asks: [string, string][]; // [price, size][]
  bids: [string, string][]; // [price, size][]
}

export interface SimulationResults {
  slippage: number;        // Percentage
  fees: number;            // In USDT
  marketImpact: number;    // Percentage
  netCost: number;         // In USDT
  makerProportion: number; // Percentage
  takerProportion: number; // Percentage
  internalLatency: number; // In milliseconds
}

export interface MetricsParams {
  orderbook: OrderbookData;
  quantity: number;
  orderType: string;
  volatility: number;
  feeTier: string;
  exchange: string;
}
