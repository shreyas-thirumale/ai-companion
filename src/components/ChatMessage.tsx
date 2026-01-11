import React from 'react';
import ReactMarkdown from 'react-markdown';
import { User, Bot, ExternalLink, Sparkles } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: any[];
}

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.type === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-slide-up`}>
      <div className={`flex max-w-4xl ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start space-x-3`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center relative ${
          isUser 
            ? 'bg-gradient-to-br from-blue-600 to-purple-600 ml-3 shadow-lg shadow-blue-500/30' 
            : 'bg-gradient-to-br from-gray-700 to-gray-800 mr-3 shadow-lg shadow-gray-500/20'
        }`}>
          {isUser ? (
            <User className="h-5 w-5 text-white" />
          ) : (
            <>
              <Bot className="h-5 w-5 text-blue-300" />
              <Sparkles className="h-3 w-3 text-purple-300 absolute -top-1 -right-1 animate-pulse" />
            </>
          )}
        </div>

        {/* Message content */}
        <div className={`flex-1 ${isUser ? 'text-right' : 'text-left'}`}>
          <div className={`inline-block rounded-2xl px-4 py-3 max-w-2xl ${
            isUser 
              ? 'message-user shadow-lg shadow-blue-500/20' 
              : 'message-assistant shadow-lg'
          }`}>
            {isUser ? (
              <p className="whitespace-pre-wrap text-white">{message.content}</p>
            ) : (
              <div className="prose prose-sm max-w-none text-gray-200">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            )}
          </div>

          {/* Timestamp */}
          <div className={`mt-2 text-xs text-gray-500 ${isUser ? 'text-right' : 'text-left'}`}>
            {formatDistanceToNow(message.timestamp, { addSuffix: true })}
          </div>

          {/* Sources */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="mt-4 space-y-2">
              <p className="text-xs font-medium text-gray-400 flex items-center">
                <ExternalLink className="h-3 w-3 mr-1" />
                Sources:
              </p>
              <div className="space-y-2">
                {message.sources.slice(0, 3).map((source, index) => (
                  <div
                    key={source.chunk_id || index}
                    className="glass-effect rounded-lg p-3 text-xs border border-gray-700/30 hover:border-blue-500/30 transition-all duration-300"
                  >
                    <div className="flex items-start space-x-2">
                      <ExternalLink className="h-3 w-3 text-blue-400 mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-white truncate">
                          {source.title || 'Untitled'}
                        </p>
                        <p className="text-gray-300 line-clamp-2 mt-1">
                          {source.excerpt}
                        </p>
                        <div className="flex items-center space-x-3 mt-2">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-blue-600/20 to-purple-600/20 text-blue-300 border border-blue-500/30">
                            {source.source_type}
                          </span>
                          <span className="text-gray-400 flex items-center">
                            <div className="w-2 h-2 bg-green-400 rounded-full mr-1 animate-pulse"></div>
                            {Math.round(source.relevance_score * 100)}% match
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};