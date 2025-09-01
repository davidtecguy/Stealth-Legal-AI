import React, { useState, useEffect } from 'react';
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
  loading: boolean;
  onNewDocument?: () => void;
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

  useEffect(() => {
    // Filter documents based on search term
    const filtered = documents.filter(doc =>
      doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.content.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredDocuments(filtered);
  }, [documents, searchTerm]);

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
            <Button size="sm" onClick={onNewDocument}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New
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

        {filteredDocuments.length === 0 ? (
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
        )}
      </CardContent>
    </Card>
  );
};
