import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { MessageCircle, FileText, BarChart3, Brain, Sparkles } from 'lucide-react';
import clsx from 'clsx';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();

  const navigation = [
    { name: 'Chat', href: '/', icon: MessageCircle },
    { name: 'Documents', href: '/documents', icon: FileText },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  ];

  return (
    <div className="min-h-screen animated-bg">
      {/* Animated background particles */}
      <div className="particles">
        <div className="absolute top-20 left-20 w-2 h-2 bg-blue-400 rounded-full opacity-60 animate-pulse"></div>
        <div className="absolute top-40 right-32 w-1 h-1 bg-purple-400 rounded-full opacity-40 animate-ping"></div>
        <div className="absolute bottom-32 left-1/4 w-1.5 h-1.5 bg-blue-300 rounded-full opacity-50 animate-pulse"></div>
        <div className="absolute top-1/3 right-1/4 w-1 h-1 bg-purple-300 rounded-full opacity-30 animate-ping"></div>
      </div>

      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 z-50 w-64 sidebar shadow-2xl">
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center px-6 border-b border-gray-700/50">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <Brain className="h-8 w-8 text-blue-400 glow-effect" />
                <Sparkles className="h-4 w-4 text-purple-400 absolute -top-1 -right-1 animate-pulse" />
              </div>
              <div>
                <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent glow-text">
                  Second Brain
                </span>
                <div className="text-xs text-gray-400">AI Companion</div>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={clsx(
                    'nav-item',
                    isActive && 'nav-item-active'
                  )}
                >
                  <item.icon className="h-5 w-5 mr-3" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-700/50">
            <div className="glass-effect rounded-lg p-3">
              <p className="text-xs text-gray-300 text-center">
                🧠 Your personal AI companion
              </p>
              <div className="flex justify-center mt-2">
                <div className="flex space-x-1">
                  <div className="w-1 h-1 bg-green-400 rounded-full animate-pulse"></div>
                  <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                  <div className="w-1 h-1 bg-purple-400 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="pl-64">
        <main className="min-h-screen">
          {children}
        </main>
      </div>
    </div>
  );
};