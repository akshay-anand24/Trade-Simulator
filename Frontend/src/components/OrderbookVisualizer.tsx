
import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts';
import { OrderbookData } from '@/types/trading';

interface OrderbookVisualizerProps {
  data: OrderbookData;
  quantity: number;
}

const OrderbookVisualizer: React.FC<OrderbookVisualizerProps> = ({ data, quantity }) => {
  const chartData = useMemo(() => {
    if (!data || !data.asks || !data.bids) return [];

    // Take top 10 levels from each side
    const asks = data.asks.slice(0, 10).map(level => ({
      price: parseFloat(level[0]),
      type: 'ask',
      quantity: parseFloat(level[1]),
      total: parseFloat(level[0]) * parseFloat(level[1])
    }));
    
    const bids = data.bids.slice(0, 10).map(level => ({
      price: parseFloat(level[0]),
      type: 'bid',
      quantity: parseFloat(level[1]),
      total: parseFloat(level[0]) * parseFloat(level[1])
    }));
    
    // Calculate mid price
    const bestAsk = asks.length > 0 ? asks[0].price : 0;
    const bestBid = bids.length > 0 ? bids[0].price : 0;
    const midPrice = (bestAsk + bestBid) / 2;
    
    // Return combined data sorted by price
    return [...asks, ...bids].sort((a, b) => a.price - b.price);
  }, [data]);

  const midPrice = useMemo(() => {
    if (!data || !data.asks || !data.bids || data.asks.length === 0 || data.bids.length === 0) return 0;
    const bestAsk = parseFloat(data.asks[0][0]);
    const bestBid = parseFloat(data.bids[0][0]);
    return (bestAsk + bestBid) / 2;
  }, [data]);

  const estimatedImpact = useMemo(() => {
    if (!data || !data.bids || data.bids.length === 0) return 0;
    
    // Simplified market impact estimation
    let remainingQuantity = quantity;
    let totalCost = 0;
    
    // For a buy order, we'll eat through the ask book
    for (const ask of data.asks) {
      const price = parseFloat(ask[0]);
      const size = parseFloat(ask[1]);
      const levelCost = price * size;
      
      if (remainingQuantity <= levelCost) {
        // We can fill the entire order at this level
        totalCost += remainingQuantity;
        remainingQuantity = 0;
        break;
      } else {
        // We consume this entire level and continue
        totalCost += levelCost;
        remainingQuantity -= levelCost;
      }
    }
    
    // If we still have remaining quantity, we'd need more levels
    // but for simplicity, we'll just return what we've calculated
    
    const averagePrice = totalCost / quantity;
    const impactPercentage = ((averagePrice - parseFloat(data.bids[0][0])) / parseFloat(data.bids[0][0])) * 100;
    
    return impactPercentage;
  }, [data, quantity]);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const dataPoint = payload[0].payload;
      return (
        <div className="bg-card p-2 border border-border rounded-md shadow-md">
          <p className="text-sm">{`Price: ${dataPoint.price.toFixed(2)}`}</p>
          <p className="text-sm">{`Size: ${dataPoint.quantity.toFixed(4)}`}</p>
          <p className="text-sm">{`Total: ${dataPoint.total.toFixed(2)} USDT`}</p>
          <p className="text-sm font-medium">
            {dataPoint.type === 'ask' ? 'Ask (Sell)' : 'Bid (Buy)'}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-[250px]">
      {chartData.length > 0 ? (
        <>
          <div className="flex justify-between mb-2">
            <span className="text-sm text-muted-foreground">Mid price: {midPrice.toFixed(2)}</span>
            <span className="text-sm text-muted-foreground">
              Est. Market Impact: <span className="negative">{estimatedImpact.toFixed(4)}%</span>
            </span>
          </div>
          <ResponsiveContainer width="100%" height="90%">
            <BarChart
              data={chartData}
              margin={{ top: 5, right: 5, left: 5, bottom: 5 }}
            >
              <XAxis 
                dataKey="price" 
                scale="linear"
                tick={{ fontSize: 10 }}
                tickFormatter={(value) => value.toFixed(1)}
              />
              <YAxis 
                hide 
                domain={[0, 'dataMax']}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine x={midPrice} stroke="#8884d8" />
              {/* Split into two bars with fixed colors instead of using a function */}
              <Bar
                dataKey="quantity"
                name="bid"
                fill="hsl(142, 76%, 36%)"
                stackId="stack"
                isAnimationActive={false}
              />
              <Bar
                dataKey={(entry) => entry.type === 'ask' ? entry.quantity : 0}
                name="ask"
                fill="hsl(0, 62.8%, 50.6%)"
                stackId="stack"
                isAnimationActive={false}
              />
            </BarChart>
          </ResponsiveContainer>
        </>
      ) : (
        <div className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">No orderbook data available</p>
        </div>
      )}
    </div>
  );
};

export default OrderbookVisualizer;
