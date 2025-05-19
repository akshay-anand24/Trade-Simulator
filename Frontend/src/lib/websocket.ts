
import { OrderbookData } from '@/types/trading';

interface WebSocketManagerOptions {
  onMessage: (data: OrderbookData, processingTime: number) => void;
  onOpen?: () => void;
  onError?: (error: Event) => void;
  onClose?: () => void;
}

export class WebSocketManager {
  private socket: WebSocket | null = null;
  private options: WebSocketManagerOptions;

  constructor(options: WebSocketManagerOptions) {
    this.options = options;
  }

  connect(url: string): void {
    if (this.socket) {
      this.socket.close();
    }

    try {
      this.socket = new WebSocket(url);

      this.socket.onopen = () => {
        if (this.options.onOpen) {
          this.options.onOpen();
        }
      };

      this.socket.onmessage = (event) => {
        const startTime = performance.now();
        
        try {
          const data = JSON.parse(event.data) as OrderbookData;
          const processingTime = performance.now() - startTime;
          this.options.onMessage(data, processingTime);
        } catch (error) {
          console.error('Error processing message:', error);
        }
      };

      this.socket.onerror = (error) => {
        if (this.options.onError) {
          this.options.onError(error);
        }
      };

      this.socket.onclose = () => {
        if (this.options.onClose) {
          this.options.onClose();
        }
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      if (this.options.onError) {
        this.options.onError(new Event('error'));
      }
    }
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }
}
