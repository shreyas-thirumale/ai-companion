import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export interface Document {
  id: string;
  source_path: string;
  source_type: string;
  title?: string;
  author?: string;
  created_at: string;
  ingested_at: string;
  file_size?: number;
  processing_status: string;
  metadata?: any;
  tags: any[];
  chunk_count: number;
}

export interface Conversation {
  id: string;
  query: string;
  response?: string;
  created_at: string;
  response_time_ms?: number;
}

export interface QueryResponse {
  conversation_id: string;
  response: string;
  sources: any[];
  response_time_ms: number;
  created_at: string;
}

export interface Analytics {
  total_documents: number;
  total_chunks: number;
  total_queries: number;
  avg_response_time_ms: number;
  storage_usage_mb: number;
  popular_tags: Array<{ tag: string; count: number }>;
  query_trends: Array<{ date: string; query_count: number }>;
}

export const api = {
  // Documents
  async uploadDocument(file: File, tags?: string[]): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    if (tags && tags.length > 0) {
      formData.append('tags', JSON.stringify(tags));
    }

    const response = await apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async getDocuments(page = 1, limit = 20, sourceType?: string): Promise<{
    documents: Document[];
    total: number;
    page: number;
    limit: number;
    has_next: boolean;
  }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    
    if (sourceType) {
      params.append('source_type', sourceType);
    }

    const response = await apiClient.get(`/documents?${params}`);
    return response.data;
  },

  async deleteDocument(documentId: string): Promise<void> {
    await apiClient.delete(`/documents/${documentId}`);
  },

  // Conversations
  async getConversations(page = 1, limit = 20): Promise<{
    conversations: Conversation[];
    total: number;
    page: number;
    limit: number;
  }> {
    const response = await apiClient.get(`/conversations?page=${page}&limit=${limit}`);
    return response.data;
  },

  // Query
  async submitQuery(query: string, conversationId?: string, filters?: any): Promise<QueryResponse> {
    const response = await apiClient.post('/query', {
      query,
      conversation_id: conversationId,
      filters,
    });
    return response.data;
  },

  // Search
  async search(query: string, filters?: any): Promise<{
    results: any[];
    total: number;
    query_time_ms: number;
  }> {
    const params = new URLSearchParams({ q: query });
    
    if (filters?.source_type) {
      filters.source_type.forEach((type: string) => {
        params.append('source_type', type);
      });
    }
    
    if (filters?.date_from) {
      params.append('date_from', filters.date_from);
    }
    
    if (filters?.date_to) {
      params.append('date_to', filters.date_to);
    }

    const response = await apiClient.get(`/search?${params}`);
    return response.data;
  },

  // Analytics
  async getAnalytics(): Promise<Analytics> {
    const response = await apiClient.get('/analytics');
    return response.data;
  },

  // Tags
  async getTags(): Promise<any[]> {
    const response = await apiClient.get('/tags');
    return response.data;
  },

  async createTag(name: string, color?: string): Promise<any> {
    const response = await apiClient.post('/tags', { name, color });
    return response.data;
  },
};

export default api;