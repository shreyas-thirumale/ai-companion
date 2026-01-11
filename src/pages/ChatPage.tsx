import React, { useState, useRef, useEffect } from 'react';
import { Send, Upload, Paperclip, Zap, Sparkles } from 'lucide-react';
import { ChatMessage } from '../components/ChatMessage';
import { TypingIndicator } from '../components/TypingIndicator';
import { FileUpload } from '../components/FileUpload';
import { useChatWebSocket } from '../hooks/useChatWebSocket';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: any[];
}

export const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const { sendMessage, isConnected, isTyping } = useChatWebSocket({
    onMessage: (content: string, isComplete: boolean) => {
      if (isComplete) {
        return;
      }

      setMessages(prev => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage && lastMessage.type === 'assistant' && lastMessage.id === 'streaming') {
          return prev.map(msg => 
            msg.id === 'streaming' 
              ? { ...msg, content: msg.content + content }
              : msg
          );
        } else {
          return [...prev, {
            id: 'streaming',
            type: 'assistant',
            content: content,
            timestamp: new Date()
          }];
        }
      });
    },
    onComplete: (sources: any[]) => {
      setMessages(prev => 
        prev.map(msg => 
          msg.id === 'streaming' 
            ? { ...msg, id: Date.now().toString(), sources }
            : msg
        )
      );
    }
  });

  // Load conversation history
  const { data: conversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => api.getConversations(1, 50),
  });

  useEffect(() => {
    if (conversations?.conversations) {
      const historyMessages: Message[] = [];
      conversations.conversations.reverse().forEach(conv => {
        historyMessages.push({
          id: `${conv.id}-query`,
          type: 'user',
          content: conv.query,
          timestamp: new Date(conv.created_at)
        });
        if (conv.response) {
          historyMessages.push({
            id: `${conv.id}-response`,
            type: 'assistant',
            content: conv.response,
            timestamp: new Date(conv.created_at)
          });
        }
      });
      setMessages(historyMessages);
    }
  }, [conversations]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !isConnected) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');

    sendMessage(input.trim());
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleFileUpload = async (files: File[]) => {
    setIsUploading(true);
    try {
      for (const file of files) {
        await api.uploadDocument(file);
      }
      setShowUpload(false);
      const successMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: `✨ Successfully uploaded ${files.length} file(s)! You can now ask questions about the content. Try asking me about what's in your documents!`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, successMessage]);
    } catch (error) {
      console.error('Upload failed:', error);
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: '❌ Sorry, there was an error uploading your files. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="glass-effect border-b border-gray-700/50 px-6 py-4 backdrop-blur-md">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Zap className="h-8 w-8 text-blue-400 glow-effect float-animation" />
              <Sparkles className="h-4 w-4 text-purple-400 absolute -top-1 -right-1 animate-pulse" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                AI Chat
              </h1>
              <p className="text-sm text-gray-400">
                Ask questions about your documents and knowledge base
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowUpload(true)}
              className="btn-secondary flex items-center space-x-2"
              disabled={isUploading}
            >
              <Upload className="h-4 w-4" />
              <span>Upload</span>
            </button>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 shadow-lg shadow-green-400/50' : 'bg-red-400 shadow-lg shadow-red-400/50'} animate-pulse`} />
              <span className="text-xs text-gray-400">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6 scrollbar-thin">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md">
              <div className="relative mb-6">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-600/20 to-purple-600/20 rounded-full flex items-center justify-center mx-auto glow-effect">
                  <Send className="h-10 w-10 text-blue-400" />
                </div>
                <div className="absolute -top-2 -right-2">
                  <Sparkles className="h-6 w-6 text-purple-400 animate-pulse" />
                </div>
              </div>
              <h3 className="text-xl font-semibold text-white mb-3 glow-text">
                Start a conversation
              </h3>
              <p className="text-gray-400 leading-relaxed">
                Upload some documents and start asking questions about your content.
                I'll help you find and understand information from your knowledge base with the power of AI.
              </p>
              <div className="mt-6 flex justify-center space-x-4">
                <div className="glass-effect rounded-lg p-3 text-xs text-gray-300">
                  💡 Try: "What's in my documents?"
                </div>
                <div className="glass-effect rounded-lg p-3 text-xs text-gray-300">
                  🔍 Or: "Summarize my notes"
                </div>
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isTyping && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <div className="glass-effect border-t border-gray-700/50 px-6 py-4 backdrop-blur-md">
        <form onSubmit={handleSubmit} className="flex items-end space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about your documents..."
              className="input-field resize-none pr-12"
              rows={1}
              style={{
                minHeight: '44px',
                maxHeight: '120px',
                height: 'auto'
              }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                target.style.height = target.scrollHeight + 'px';
              }}
            />
            <button
              type="button"
              onClick={() => setShowUpload(true)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 text-gray-400 hover:text-blue-400 transition-colors"
              disabled={isUploading}
            >
              <Paperclip className="h-4 w-4" />
            </button>
          </div>
          <button
            type="submit"
            disabled={!input.trim() || !isConnected}
            className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-4 w-4" />
            <span className="hidden sm:inline">Send</span>
          </button>
        </form>
      </div>

      {/* File Upload Modal */}
      {showUpload && (
        <FileUpload
          onUpload={handleFileUpload}
          onClose={() => setShowUpload(false)}
          isUploading={isUploading}
        />
      )}
    </div>
  );
};