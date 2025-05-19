
import React from 'react';
import TradingSimulator from '@/components/TradingSimulator';

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <header className="py-4 px-6 border-b border-border">
        <h1 className="text-2xl font-bold text-primary">Go Quant</h1>
        <p className="text-sm text-muted-foreground">High-Performance Trade Simulator</p>
      </header>
      
      <main className="container mx-auto p-4">
        <TradingSimulator />
      </main>
      
      <footer className="py-4 px-6 border-t border-border mt-8">
        <div className="text-sm text-muted-foreground flex justify-between">
          <p>© 2025 GO Quant</p>
          <p>Real-time L2 Orderbook Processing Engine</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
