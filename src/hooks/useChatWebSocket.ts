import { useEffect, useRef, useState, useCallback } from 'react';

interface UseChatWebSocketProps {
  onMessage: (content: string, isComplete: boolean) => void;
  onComplete: (sources: any[]) => void;
}

export const useChatWebSocket = ({ onMessage, onComplete }: UseChatWebSocketProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    const wsUrl = process.env.REACT_APP_WS_URL || 
      `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/chat/stream`;
    
    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setIsTyping(false);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          switch (data.type) {
            case 'response_chunk':
              if (data.data.is_final) {
                setIsTyping(false);
                onMessage('', true);
              } else {
                setIsTyping(true);
                onMessage(data.data.content, false);
              }
              break;
              
            case 'sources':
              onComplete(data.data.sources || []);
              break;
              
            case 'error':
              console.error('WebSocket error:', data.data.message);
              setIsTyping(false);
              onMessage(`Error: ${data.data.message}`, true);
              break;
              
            default:
              console.log('Unknown message type:', data.type);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        setIsTyping(false);
        
        // Attempt to reconnect after 3 seconds
        if (!event.wasClean) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, 3000);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
        setIsTyping(false);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setIsConnected(false);
    }
  }, [onMessage, onComplete]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Component unmounting');
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setIsTyping(false);
  }, []);

  const sendMessage = useCallback((query: string, conversationId?: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const message = {
        type: 'query',
        data: {
          query,
          conversation_id: conversationId,
        },
      };
      
      wsRef.current.send(JSON.stringify(message));
      setIsTyping(true);
    } else {
      console.error('WebSocket is not connected');
    }
  }, []);

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    isTyping,
    sendMessage,
    reconnect: connect,
  };
};