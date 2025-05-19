
import React from 'react';
import { Progress } from '@/components/ui/progress';
import { Card } from '@/components/ui/card';

interface PerformanceMetricsProps {
  latency: number;
  connected: boolean;
}

const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ latency, connected }) => {
  // Calculate performance indicators
  const getLatencyClass = (latency: number) => {
    if (latency < 50) return 'latency-good';
    if (latency < 150) return 'latency-warning';
    return 'latency-critical';
  };

  const getLatencyPercentage = (latency: number) => {
    // Map 0-300ms to 0-100%
    const percentage = Math.min((latency / 300) * 100, 100);
    return percentage;
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <div className="flex justify-between">
          <span className="text-sm">Processing Latency</span>
          <span className="text-sm font-medium">{connected ? `${latency.toFixed(2)} ms` : '-'}</span>
        </div>
        {connected ? (
          <div className="w-full">
            <Progress value={getLatencyPercentage(latency)} className={getLatencyClass(latency)} />
          </div>
        ) : (
          <div className="w-full">
            <Progress value={0} className="bg-muted" />
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Card className="p-2">
          <div className="text-xs text-muted-foreground">Memory Usage</div>
          <div className="text-sm font-medium">
            {connected ? 'Active' : 'Idle'}
          </div>
        </Card>
        
        <Card className="p-2">
          <div className="text-xs text-muted-foreground">Connection Status</div>
          <div className="text-sm font-medium">
            {connected ? (
              <span className="text-success">Connected</span>
            ) : (
              <span className="text-muted-foreground">Disconnected</span>
            )}
          </div>
        </Card>
        
        <Card className="p-2">
          <div className="text-xs text-muted-foreground">Processing</div>
          <div className="text-sm font-medium">
            {connected ? `${(1000 / Math.max(latency, 1)).toFixed(1)} ticks/s` : '-'}
          </div>
        </Card>
        
        <Card className="p-2">
          <div className="text-xs text-muted-foreground">Performance</div>
          <div className="text-sm font-medium">
            {connected ? (
              latency < 50 ? (
                <span className="text-success">Optimal</span>
              ) : latency < 150 ? (
                <span className="text-yellow-500">Good</span>
              ) : (
                <span className="text-destructive">Degraded</span>
              )
            ) : '-'}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default PerformanceMetrics;
