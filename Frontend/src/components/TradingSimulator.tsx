
import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import OrderbookVisualizer from './OrderbookVisualizer';
import PerformanceMetrics from './PerformanceMetrics';
import { WebSocketManager } from '@/lib/websocket';
import { calculateMetrics } from '@/lib/metrics-calculator';
import { OrderbookData, SimulationResults } from '@/types/trading';

const TradingSimulator = () => {
  const { toast } = useToast();
  const websocket = useRef<WebSocketManager | null>(null);
  
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [orderbookData, setOrderbookData] = useState<OrderbookData | null>(null);
  const [latency, setLatency] = useState<number>(0);
  
  // Input parameters
  const [exchange, setExchange] = useState<string>('OKX');
  const [symbol, setSymbol] = useState<string>('BTC-USDT');
  const [orderType, setOrderType] = useState<string>('market');
  const [quantity, setQuantity] = useState<number>(100);
  const [volatility, setVolatility] = useState<number>(0.5);
  const [feeTier, setFeeTier] = useState<string>('tier1');
  
  // Output results
  const [results, setResults] = useState<SimulationResults | null>(null);
  
  // Available symbols for the selected exchange
  const availableSymbols = {
    'OKX': ['BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'DOGE-USDT']
  };
  
  useEffect(() => {
    return () => {
      if (websocket.current) {
        websocket.current.disconnect();
      }
    };
  }, []);
  
  const handleConnect = () => {
    setLoading(true);
    
    try {
      websocket.current = new WebSocketManager({
        onMessage: handleWebSocketMessage,
        onOpen: () => {
          setConnected(true);
          setLoading(false);
          toast({
            title: "Connection established",
            description: `Connected to ${exchange} ${symbol} orderbook feed`,
          });
        },
        onError: (error) => {
          console.error("WebSocket error:", error);
          setConnected(false);
          setLoading(false);
          toast({
            title: "Connection error",
            description: "Failed to connect to orderbook feed",
            variant: "destructive",
          });
        },
        onClose: () => {
          setConnected(false);
          setLoading(false);
          toast({
            title: "Connection closed",
            description: "Disconnected from orderbook feed",
          });
        }
      });
      
      // Connect to the WebSocket endpoint
      // Note: In a real implementation, the URL would be constructed based on exchange and symbol
      websocket.current.connect('wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP');
    } catch (error) {
      console.error("Failed to initialize WebSocket:", error);
      setLoading(false);
      toast({
        title: "Initialization error",
        description: "Failed to initialize WebSocket connection",
        variant: "destructive",
      });
    }
  };
  
  const handleDisconnect = () => {
    if (websocket.current) {
      websocket.current.disconnect();
    }
  };
  
  const handleWebSocketMessage = (data: OrderbookData, processingTime: number) => {
    setOrderbookData(data);
    setLatency(processingTime);
    
    // Calculate all the metrics based on the orderbook data and input parameters
    const simulationResults = calculateMetrics({
      orderbook: data,
      quantity,
      orderType,
      volatility,
      feeTier,
      exchange
    });
    
    setResults(simulationResults);
  };
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Left Panel - Input Parameters */}
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Input Parameters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Exchange</label>
              <Select value={exchange} onValueChange={setExchange} disabled={connected}>
                <SelectTrigger>
                  <SelectValue placeholder="Select exchange" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="OKX">OKX</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Symbol</label>
              <Select value={symbol} onValueChange={setSymbol} disabled={connected}>
                <SelectTrigger>
                  <SelectValue placeholder="Select symbol" />
                </SelectTrigger>
                <SelectContent>
                  {availableSymbols[exchange as keyof typeof availableSymbols]?.map(sym => (
                    <SelectItem key={sym} value={sym}>{sym}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Order Type</label>
              <Select value={orderType} onValueChange={setOrderType}>
                <SelectTrigger>
                  <SelectValue placeholder="Select order type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="market">Market</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Quantity (USD)</label>
              <Input 
                type="number" 
                value={quantity.toString()} 
                onChange={(e) => setQuantity(Number(e.target.value))} 
                min="1"
                max="10000"
              />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-sm font-medium">Volatility</label>
                <span className="text-sm text-muted-foreground">{volatility}</span>
              </div>
              <Slider
                value={[volatility]}
                min={0.1}
                max={1}
                step={0.1}
                onValueChange={(values) => setVolatility(values[0])}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Fee Tier</label>
              <Select value={feeTier} onValueChange={setFeeTier}>
                <SelectTrigger>
                  <SelectValue placeholder="Select fee tier" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="tier1">Tier 1 (0.10%)</SelectItem>
                  <SelectItem value="tier2">Tier 2 (0.08%)</SelectItem>
                  <SelectItem value="tier3">Tier 3 (0.05%)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex space-x-2 pt-4">
              {!connected ? (
                <Button onClick={handleConnect} disabled={loading} className="flex-1">
                  {loading ? 'Connecting...' : 'Connect to Orderbook'}
                </Button>
              ) : (
                <Button onClick={handleDisconnect} variant="destructive" className="flex-1">
                  Disconnect
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Performance Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <PerformanceMetrics latency={latency} connected={connected} />
          </CardContent>
        </Card>
      </div>
      
      {/* Right Panel - Output Parameters */}
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Simulation Results</CardTitle>
              {connected && (
                <Badge variant={latency < 50 ? 'outline' : 'secondary'}>
                  {latency.toFixed(2)}ms
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {!connected ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>Connect to orderbook to see simulation results</p>
              </div>
            ) : !results ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>Processing orderbook data...</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Expected Slippage</p>
                    <p className={`text-xl font-medium ${results.slippage >= 0 ? 'negative' : 'positive'}`}>
                      {results.slippage.toFixed(4)}%
                    </p>
                  </div>
                  
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Expected Fees</p>
                    <p className="text-xl font-medium">{results.fees.toFixed(4)} USDT</p>
                  </div>
                  
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Market Impact</p>
                    <p className="text-xl font-medium negative">{results.marketImpact.toFixed(4)}%</p>
                  </div>
                  
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Net Cost</p>
                    <p className="text-xl font-medium">{results.netCost.toFixed(4)} USDT</p>
                  </div>
                  
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Maker/Taker</p>
                    <p className="text-xl font-medium">{results.makerProportion.toFixed(0)}% / {results.takerProportion.toFixed(0)}%</p>
                  </div>
                  
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Internal Latency</p>
                    <p className="text-xl font-medium">{results.internalLatency.toFixed(2)} ms</p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Orderbook Data</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="visualization">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="visualization">Visualization</TabsTrigger>
                <TabsTrigger value="raw">Raw Data</TabsTrigger>
              </TabsList>
              <TabsContent value="visualization" className="mt-4">
                {connected && orderbookData ? (
                  <OrderbookVisualizer data={orderbookData} quantity={quantity} />
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <p>Connect to see orderbook visualization</p>
                  </div>
                )}
              </TabsContent>
              <TabsContent value="raw" className="mt-4">
                {connected && orderbookData ? (
                  <div className="orderbook-container">
                    <div className="mb-2">
                      <h3 className="text-sm font-medium mb-1">Asks (Sell Orders)</h3>
                      <div className="max-h-32 overflow-y-auto">
                        <table className="w-full table-auto">
                          <thead>
                            <tr className="text-xs text-muted-foreground">
                              <th className="text-left py-1">Price</th>
                              <th className="text-right py-1">Size</th>
                              <th className="text-right py-1">Total</th>
                            </tr>
                          </thead>
                          <tbody>
                            {orderbookData.asks.slice(0, 10).map((ask, index) => (
                              <tr key={`ask-${index}`} className="ask-row text-sm">
                                <td className="text-left py-1 text-destructive">{ask[0]}</td>
                                <td className="text-right py-1">{ask[1]}</td>
                                <td className="text-right py-1">{(parseFloat(ask[0]) * parseFloat(ask[1])).toFixed(2)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                    <div>
                      <h3 className="text-sm font-medium mb-1">Bids (Buy Orders)</h3>
                      <div className="max-h-32 overflow-y-auto">
                        <table className="w-full table-auto">
                          <thead>
                            <tr className="text-xs text-muted-foreground">
                              <th className="text-left py-1">Price</th>
                              <th className="text-right py-1">Size</th>
                              <th className="text-right py-1">Total</th>
                            </tr>
                          </thead>
                          <tbody>
                            {orderbookData.bids.slice(0, 10).map((bid, index) => (
                              <tr key={`bid-${index}`} className="bid-row text-sm">
                                <td className="text-left py-1 text-success">{bid[0]}</td>
                                <td className="text-right py-1">{bid[1]}</td>
                                <td className="text-right py-1">{(parseFloat(bid[0]) * parseFloat(bid[1])).toFixed(2)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <p>Connect to see raw orderbook data</p>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TradingSimulator;
