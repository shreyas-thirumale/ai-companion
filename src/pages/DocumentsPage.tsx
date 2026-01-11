import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FileText, Trash2, Upload, Search, Filter } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { api, Document } from '../services/api';
import { FileUpload } from '../components/FileUpload';
import clsx from 'clsx';

const getSourceTypeIcon = (sourceType: string) => {
  switch (sourceType) {
    case 'pdf': return '📄';
    case 'audio': return '🎵';
    case 'image': return '🖼️';
    case 'web': return '🌐';
    default: return '📝';
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed': return 'bg-green-100 text-green-800';
    case 'processing': return 'bg-yellow-100 text-yellow-800';
    case 'failed': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

export const DocumentsPage: React.FC = () => {
  const [showUpload, setShowUpload] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [sourceTypeFilter, setSourceTypeFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  
  const queryClient = useQueryClient();

  // Fetch documents
  const { data: documentsData, isLoading } = useQuery({
    queryKey: ['documents', page, sourceTypeFilter],
    queryFn: () => api.getDocuments(page, 20, sourceTypeFilter || undefined),
  });

  // Delete document mutation
  const deleteMutation = useMutation({
    mutationFn: api.deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const handleFileUpload = async (files: File[]) => {
    setIsUploading(true);
    try {
      for (const file of files) {
        await api.uploadDocument(file);
      }
      setShowUpload(false);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = (documentId: string) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      deleteMutation.mutate(documentId);
    }
  };

  const filteredDocuments = documentsData?.documents.filter(doc =>
    searchQuery === '' || 
    doc.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.source_path.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Documents</h1>
            <p className="text-sm text-gray-600">
              Manage your uploaded documents and knowledge base
            </p>
          </div>
          <button
            onClick={() => setShowUpload(true)}
            className="btn-primary flex items-center"
            disabled={isUploading}
          >
            <Upload className="h-4 w-4 mr-2" />
            Upload Documents
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input-field pl-10"
              />
            </div>
          </div>

          {/* Source Type Filter */}
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={sourceTypeFilter}
              onChange={(e) => setSourceTypeFilter(e.target.value)}
              className="input-field w-40"
            >
              <option value="">All Types</option>
              <option value="pdf">PDF</option>
              <option value="text">Text</option>
              <option value="audio">Audio</option>
              <option value="image">Image</option>
              <option value="web">Web</option>
            </select>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-6 py-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchQuery || sourceTypeFilter ? 'No documents found' : 'No documents yet'}
            </h3>
            <p className="text-gray-600 mb-6">
              {searchQuery || sourceTypeFilter 
                ? 'Try adjusting your search or filters'
                : 'Upload your first document to get started'
              }
            </p>
            {!searchQuery && !sourceTypeFilter && (
              <button
                onClick={() => setShowUpload(true)}
                className="btn-primary"
              >
                Upload Documents
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Documents Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredDocuments.map((document) => (
                <div key={document.id} className="card hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <span className="text-2xl">
                        {getSourceTypeIcon(document.source_type)}
                      </span>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-gray-900 truncate">
                          {document.title || 'Untitled'}
                        </h3>
                        <p className="text-sm text-gray-500 truncate">
                          {document.source_path.split('/').pop()}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDelete(document.id)}
                      className="text-gray-400 hover:text-red-600 transition-colors"
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>

                  <div className="space-y-2">
                    {/* Status */}
                    <div className="flex items-center justify-between">
                      <span className={clsx(
                        'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
                        getStatusColor(document.processing_status)
                      )}>
                        {document.processing_status}
                      </span>
                      <span className="text-xs text-gray-500">
                        {document.chunk_count} chunks
                      </span>
                    </div>

                    {/* Metadata */}
                    <div className="text-xs text-gray-500 space-y-1">
                      {document.author && (
                        <p>Author: {document.author}</p>
                      )}
                      {document.file_size && (
                        <p>Size: {(document.file_size / 1024 / 1024).toFixed(1)} MB</p>
                      )}
                      <p>
                        Uploaded {formatDistanceToNow(new Date(document.created_at), { addSuffix: true })}
                      </p>
                    </div>

                    {/* Tags */}
                    {document.tags && document.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {document.tags.slice(0, 3).map((tag, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-primary-100 text-primary-800"
                          >
                            {tag.name}
                          </span>
                        ))}
                        {document.tags.length > 3 && (
                          <span className="text-xs text-gray-500">
                            +{document.tags.length - 3} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {documentsData && documentsData.total > 20 && (
              <div className="flex items-center justify-between pt-6">
                <p className="text-sm text-gray-700">
                  Showing {((page - 1) * 20) + 1} to {Math.min(page * 20, documentsData.total)} of {documentsData.total} documents
                </p>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="btn-secondary disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage(p => p + 1)}
                    disabled={!documentsData.has_next}
                    className="btn-secondary disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
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