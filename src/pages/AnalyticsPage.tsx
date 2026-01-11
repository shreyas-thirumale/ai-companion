import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileText, MessageCircle, Clock, HardDrive, TrendingUp, Tag } from 'lucide-react';
import { api } from '../services/api';

const StatCard: React.FC<{
  title: string;
  value: string | number;
  icon: React.ElementType;
  subtitle?: string;
  trend?: string;
}> = ({ title, value, icon: Icon, subtitle, trend }) => (
  <div className="card">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <p className="text-2xl font-semibold text-gray-900">{value}</p>
        {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
      </div>
      <div className="p-3 bg-primary-100 rounded-lg">
        <Icon className="h-6 w-6 text-primary-600" />
      </div>
    </div>
    {trend && (
      <div className="mt-2 flex items-center text-sm text-green-600">
        <TrendingUp className="h-4 w-4 mr-1" />
        {trend}
      </div>
    )}
  </div>
);

export const AnalyticsPage: React.FC = () => {
  const { data: analytics, isLoading } = useQuery({
    queryKey: ['analytics'],
    queryFn: api.getAnalytics,
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Failed to load analytics</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Analytics</h1>
          <p className="text-sm text-gray-600">
            Overview of your knowledge base usage and performance
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="px-6 py-6 space-y-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Documents"
            value={analytics.total_documents.toLocaleString()}
            icon={FileText}
            subtitle="Across all formats"
          />
          <StatCard
            title="Content Chunks"
            value={analytics.total_chunks.toLocaleString()}
            icon={MessageCircle}
            subtitle="Searchable pieces"
          />
          <StatCard
            title="Total Queries"
            value={analytics.total_queries.toLocaleString()}
            icon={MessageCircle}
            subtitle="Questions asked"
          />
          <StatCard
            title="Avg Response Time"
            value={`${Math.round(analytics.avg_response_time_ms)}ms`}
            icon={Clock}
            subtitle="Query processing"
          />
        </div>

        {/* Storage Usage */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Storage Usage</h3>
            <HardDrive className="h-5 w-5 text-gray-400" />
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Used Storage</span>
                <span>{analytics.storage_usage_mb.toFixed(1)} MB</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-primary-600 h-2 rounded-full" 
                  style={{ width: `${Math.min((analytics.storage_usage_mb / 1000) * 100, 100)}%` }}
                ></div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {analytics.storage_usage_mb < 100 ? 'Plenty of space available' : 'Consider archiving old documents'}
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Popular Tags */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Popular Tags</h3>
              <Tag className="h-5 w-5 text-gray-400" />
            </div>
            {analytics.popular_tags.length > 0 ? (
              <div className="space-y-3">
                {analytics.popular_tags.slice(0, 5).map((tag, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-900">{tag.tag}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-primary-600 h-2 rounded-full" 
                          style={{ 
                            width: `${(tag.count / Math.max(...analytics.popular_tags.map(t => t.count))) * 100}%` 
                          }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-600 w-8 text-right">{tag.count}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No tags found</p>
            )}
          </div>

          {/* Query Trends */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Query Trends</h3>
              <TrendingUp className="h-5 w-5 text-gray-400" />
            </div>
            {analytics.query_trends.length > 0 ? (
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-gray-600 mb-2">
                  <span>Last 30 Days</span>
                  <span>Queries per Day</span>
                </div>
                <div className="h-32 flex items-end space-x-1">
                  {analytics.query_trends.slice(-14).map((trend, index) => {
                    const maxQueries = Math.max(...analytics.query_trends.map(t => t.query_count));
                    const height = maxQueries > 0 ? (trend.query_count / maxQueries) * 100 : 0;
                    return (
                      <div
                        key={index}
                        className="flex-1 bg-primary-200 rounded-t"
                        style={{ height: `${Math.max(height, 4)}%` }}
                        title={`${trend.date}: ${trend.query_count} queries`}
                      ></div>
                    );
                  })}
                </div>
                <div className="flex justify-between text-xs text-gray-500">
                  <span>2 weeks ago</span>
                  <span>Today</span>
                </div>
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No query data available</p>
            )}
          </div>
        </div>

        {/* Performance Insights */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Insights</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-semibold text-green-600">
                {analytics.total_documents > 0 ? Math.round(analytics.total_chunks / analytics.total_documents) : 0}
              </div>
              <div className="text-sm text-green-700">Avg chunks per document</div>
              <div className="text-xs text-green-600 mt-1">Good chunking efficiency</div>
            </div>
            
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-semibold text-blue-600">
                {analytics.avg_response_time_ms < 2000 ? '🚀' : analytics.avg_response_time_ms < 5000 ? '⚡' : '🐌'}
              </div>
              <div className="text-sm text-blue-700">Response Speed</div>
              <div className="text-xs text-blue-600 mt-1">
                {analytics.avg_response_time_ms < 2000 ? 'Excellent' : 
                 analytics.avg_response_time_ms < 5000 ? 'Good' : 'Needs optimization'}
              </div>
            </div>
            
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-semibold text-purple-600">
                {analytics.total_queries > 0 ? Math.round((analytics.total_queries / analytics.total_documents) * 10) / 10 : 0}
              </div>
              <div className="text-sm text-purple-700">Queries per document</div>
              <div className="text-xs text-purple-600 mt-1">Usage engagement</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};