import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Document } from '../types';
import { apiService } from '../services/api';
import { 
  DocumentIcon, 
  PlusIcon, 
  TrashIcon, 
  PencilIcon, 
  MagnifyingGlassIcon, 
  ArrowPathIcon 
} from '@heroicons/react/24/outline';
import { formatDate, truncateText } from '../lib/utils';

interface DocumentListProps {
  documents: Document[];
  onDocumentSelect: (document: Document) => void;
  onDocumentDeleted: (documentId: number) => void;
  onNewDocument: () => void;
  loading: boolean;
  selectedDocumentId?: number;
}

export const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  onDocumentSelect,
  onDocumentDeleted,
  loading,
  onNewDocument,
  selectedDocumentId
}) => {
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredDocuments, setFilteredDocuments] = useState<Document[]>([]);
  
  // New document form state
  const [showNewForm, setShowNewForm] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Filter documents based on search term
    const filtered = documents.filter(doc =>
      doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.content.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredDocuments(filtered);
  }, [documents, searchTerm]);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      const fileType = file.name.split('.').pop()?.toLowerCase();
      if (fileType && ['pdf', 'doc'].includes(fileType)) {
        setSelectedFile(file);
        setError(null);
        // Auto-fill title if not set
        if (!newTitle.trim()) {
          setNewTitle(file.name.replace(/\.[^/.]+$/, '')); // Remove extension
        }
      } else {
        setError('Please select a PDF or DOC file');
        setSelectedFile(null);
      }
    }
  };

  const handleCreateDocument = async () => {
    if (!newTitle.trim()) {
      setError('Title is required');
      return;
    }

    if (!selectedFile) {
      setError('Please select a file to upload');
      return;
    }

    setUploading(true);
    setError(null);
    
    try {
      setUploadProgress('Uploading document...');
      
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('title', newTitle);
      
      const newDoc = await apiService.uploadDocument(formData);
      
      // Reset form
      setShowNewForm(false);
      setNewTitle('');
      setSelectedFile(null);
      setUploadProgress('');
      setError(null);
      
      // Call the callback to refresh documents
      onNewDocument();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload document');
      setUploadProgress('');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (documentId: number) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      await apiService.deleteDocument(documentId);
      onDocumentDeleted(documentId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document');
    }
  };

  const handleDocumentClick = (document: Document) => {
    onDocumentSelect(document);
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <span className="ml-2">Loading documents...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <DocumentIcon className="h-5 w-5" />
            Documents
          </CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
              <ArrowPathIcon className="h-4 w-4" />
            </Button>
            <Button size="sm" onClick={() => setShowNewForm(!showNewForm)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              {showNewForm ? 'Cancel' : 'New'}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search documents..."
            className="pl-10"
          />
        </div>

        {error && (
          <div className="text-red-600 text-sm bg-red-50 p-3 rounded">
            {error}
          </div>
        )}

        {showNewForm ? (
          <div className="p-6 border rounded-lg bg-gray-50">
            <h3 className="text-lg font-medium mb-4">Create New Document</h3>
            <div className="grid gap-4">
              <div>
                <label htmlFor="new-title" className="block text-sm font-medium text-gray-700 mb-1">
                  Title
                </label>
                <Input
                  id="new-title"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="Enter document title"
                  className="mb-2"
                />
              </div>
              <div>
                <label htmlFor="new-file" className="block text-sm font-medium text-gray-700 mb-1">
                  File
                </label>
                <Input
                  type="file"
                  id="new-file"
                  onChange={handleFileSelect}
                  accept=".pdf,.doc,.docx"
                  className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-primary/80"
                />
                {selectedFile && (
                  <p className="mt-2 text-sm text-gray-500">Selected file: {selectedFile.name}</p>
                )}
                {error && (
                  <p className="mt-2 text-sm text-red-600">{error}</p>
                )}
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowNewForm(false)}>Cancel</Button>
                <Button onClick={handleCreateDocument} disabled={uploading}>
                  {uploading ? uploadProgress : 'Upload Document'}
                </Button>
              </div>
            </div>
          </div>
        ) : (
          filteredDocuments.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <DocumentIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
              {searchTerm ? (
                <p>No documents match your search</p>
              ) : (
                <div>
                  <p>No documents yet</p>
                  <Button 
                    variant="outline" 
                    className="mt-2"
                    onClick={onNewDocument}
                  >
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Create your first document
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredDocuments.map((document) => (
                <div
                  key={document.id}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedDocumentId === document.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                  onClick={() => handleDocumentClick(document)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-sm truncate">
                        {document.title}
                      </h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        {truncateText(document.content, 100)}
                      </p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        <span>Created: {formatDate(document.created_at)}</span>
                        {document.updated_at && (
                          <span>Updated: {formatDate(document.updated_at)}</span>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex gap-1 ml-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDocumentClick(document);
                        }}
                      >
                        <PencilIcon className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteDocument(document.id);
                        }}
                      >
                        <TrashIcon className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )
        )}
      </CardContent>
    </Card>
  );
};
