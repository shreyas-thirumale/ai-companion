import React from 'react';
import { Bot, Sparkles } from 'lucide-react';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="flex justify-start animate-slide-up">
      <div className="flex items-start space-x-3 max-w-4xl">
        {/* Avatar */}
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center shadow-lg shadow-gray-500/20 relative">
          <Bot className="h-5 w-5 text-blue-300" />
          <Sparkles className="h-3 w-3 text-purple-300 absolute -top-1 -right-1 animate-pulse" />
        </div>

        {/* Typing animation */}
        <div className="message-assistant shadow-lg">
          <div className="typing-indicator">
            <div className="typing-dot" style={{ animationDelay: '0ms' }}></div>
            <div className="typing-dot" style={{ animationDelay: '150ms' }}></div>
            <div className="typing-dot" style={{ animationDelay: '300ms' }}></div>
          </div>
          <div className="text-xs text-gray-400 mt-2">AI is thinking...</div>
        </div>
      </div>
    </div>
  );
};