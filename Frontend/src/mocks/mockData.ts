
import { OrderbookData } from '@/types/trading';

export const mockOrderbookData: OrderbookData = {
  timestamp: "2025-05-04T10:39:13Z",
  exchange: "OKX",
  symbol: "BTC-USDT-SWAP",
  asks: [
    ["95445.5", "9.06"],
    ["95448.0", "2.05"],
    ["95450.1", "5.32"],
    ["95451.8", "7.14"],
    ["95455.0", "10.53"],
    ["95457.2", "3.87"],
    ["95458.9", "6.25"],
    ["95460.4", "4.92"],
    ["95462.7", "8.44"],
    ["95464.3", "1.78"],
    ["95466.1", "5.99"],
    ["95468.5", "3.01"],
    ["95470.2", "6.33"],
    ["95472.7", "2.45"],
    ["95475.0", "9.21"]
  ],
  bids: [
    ["95445.4", "1104.23"],
    ["95445.3", "0.02"],
    ["95441.2", "5.64"],
    ["95440.0", "8.32"],
    ["95437.5", "12.47"],
    ["95435.8", "4.26"],
    ["95432.3", "7.58"],
    ["95430.6", "3.19"],
    ["95428.9", "9.75"],
    ["95427.1", "2.88"],
    ["95425.4", "6.03"],
    ["95424.2", "4.17"],
    ["95422.8", "5.92"],
    ["95420.1", "3.54"],
    ["95418.7", "8.10"]
  ]
};

// Mock function to generate slightly modified orderbook data
// This simulates receiving new ticks from the websocket
export function generateMockOrderbookTick(base: OrderbookData): OrderbookData {
  // Create a deep copy of the base data
  const newData = JSON.parse(JSON.stringify(base)) as OrderbookData;
  
  // Update timestamp
  newData.timestamp = new Date().toISOString();
  
  // Slightly modify some prices and sizes
  newData.asks = newData.asks.map(ask => {
    const price = parseFloat(ask[0]) * (1 + (Math.random() - 0.5) * 0.001);
    const size = parseFloat(ask[1]) * (1 + (Math.random() - 0.5) * 0.2);
    return [price.toFixed(1), size.toFixed(2)];
  });
  
  newData.bids = newData.bids.map(bid => {
    const price = parseFloat(bid[0]) * (1 + (Math.random() - 0.5) * 0.001);
    const size = parseFloat(bid[1]) * (1 + (Math.random() - 0.5) * 0.2);
    return [price.toFixed(1), size.toFixed(2)];
  });
  
  // Sort asks ascending by price
  newData.asks.sort((a, b) => parseFloat(a[0]) - parseFloat(b[0]));
  
  // Sort bids descending by price
  newData.bids.sort((a, b) => parseFloat(b[0]) - parseFloat(a[0]));
  
  return newData;
}
