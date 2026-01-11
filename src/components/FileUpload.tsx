import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, FileText, Image, Music, Globe } from 'lucide-react';
import clsx from 'clsx';

interface FileUploadProps {
  onUpload: (files: File[]) => void;
  onClose: () => void;
  isUploading: boolean;
}

const getFileIcon = (fileType: string) => {
  if (fileType.startsWith('image/')) return Image;
  if (fileType.startsWith('audio/')) return Music;
  if (fileType.includes('pdf') || fileType.includes('document')) return FileText;
  return FileText;
};

const getFileTypeLabel = (file: File) => {
  const ext = file.name.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'pdf': return 'PDF Document';
    case 'docx': return 'Word Document';
    case 'txt': return 'Text File';
    case 'md': return 'Markdown';
    case 'mp3': case 'm4a': case 'wav': return 'Audio File';
    case 'jpg': case 'jpeg': case 'png': case 'gif': return 'Image';
    default: return 'Document';
  }
};

export const FileUpload: React.FC<FileUploadProps> = ({ onUpload, onClose, isUploading }) => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onUpload(acceptedFiles);
    }
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'audio/mpeg': ['.mp3'],
      'audio/mp4': ['.m4a'],
      'audio/wav': ['.wav'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/gif': ['.gif'],
    },
    multiple: true,
    disabled: isUploading,
  });

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Upload Documents</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={isUploading}
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Dropzone */}
          <div
            {...getRootProps()}
            className={clsx(
              'border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer',
              isDragActive
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-300 hover:border-gray-400',
              isUploading && 'opacity-50 cursor-not-allowed'
            )}
          >
            <input {...getInputProps()} />
            <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            {isDragActive ? (
              <p className="text-lg text-primary-600">Drop the files here...</p>
            ) : (
              <div>
                <p className="text-lg text-gray-900 mb-2">
                  Drag & drop files here, or click to select
                </p>
                <p className="text-sm text-gray-600">
                  Supports PDF, Word docs, text files, audio, and images
                </p>
              </div>
            )}
          </div>

          {/* File list */}
          {acceptedFiles.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-medium text-gray-900 mb-3">
                Selected Files ({acceptedFiles.length})
              </h3>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {acceptedFiles.map((file, index) => {
                  const Icon = getFileIcon(file.type);
                  return (
                    <div
                      key={index}
                      className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg"
                    >
                      <Icon className="h-5 w-5 text-gray-500" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {file.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {getFileTypeLabel(file)} • {(file.size / 1024 / 1024).toFixed(1)} MB
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Supported formats */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Supported Formats</h4>
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
              <div className="flex items-center space-x-2">
                <FileText className="h-3 w-3" />
                <span>PDF, Word, Text, Markdown</span>
              </div>
              <div className="flex items-center space-x-2">
                <Music className="h-3 w-3" />
                <span>MP3, M4A, WAV</span>
              </div>
              <div className="flex items-center space-x-2">
                <Image className="h-3 w-3" />
                <span>JPG, PNG, GIF</span>
              </div>
              <div className="flex items-center space-x-2">
                <Globe className="h-3 w-3" />
                <span>Web URLs (coming soon)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="btn-secondary"
            disabled={isUploading}
          >
            Cancel
          </button>
          <button
            onClick={() => acceptedFiles.length > 0 && onUpload(acceptedFiles)}
            disabled={acceptedFiles.length === 0 || isUploading}
            className="btn-primary"
          >
            {isUploading ? 'Uploading...' : `Upload ${acceptedFiles.length} file(s)`}
          </button>
        </div>
      </div>
    </div>
  );
};