import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Document, ChangeOperation } from '../types';
import { apiService } from '../services/api';
import { 
  DocumentIcon, 
  PencilIcon, 
  DocumentArrowDownIcon, 
  ArrowPathIcon 
} from '@heroicons/react/24/outline';

interface DocumentEditorProps {
  selectedDocument: Document | null;
  onDocumentCreated: (document: Document) => void;
  onDocumentUpdated: (document: Document) => void;
}

export const DocumentEditor: React.FC<DocumentEditorProps> = ({ 
  selectedDocument, 
  onDocumentCreated,
  onDocumentUpdated
}) => {
  const [document, setDocument] = useState<Document | null>(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Change tracking
  const [targetText, setTargetText] = useState('');
  const [occurrence, setOccurrence] = useState(1);
  const [replacementText, setReplacementText] = useState('');
  const [startPos, setStartPos] = useState(0);
  const [endPos, setEndPos] = useState(0);
  const [useRange] = useState(false);

  useEffect(() => {
    if (selectedDocument) {
      setDocument(selectedDocument);
      setTitle(selectedDocument.title);
      setContent(selectedDocument.content);
    } else {
      setDocument(null);
      setTitle('');
      setContent('');
    }
  }, [selectedDocument]);



  const handleSave = async () => {
    if (!title.trim() || !content.trim()) {
      setError('Title and content are required');
      return;
    }

    setLoading(true);
    
    if (!document) {
      // Create new document
      try {
        const newDoc = await apiService.createDocument({ title, content });
        setDocument(newDoc);
        onDocumentCreated(newDoc);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create document');
      } finally {
        setLoading(false);
      }
    } else {
      // Update existing document - create a change operation for title/content update
      try {
        setLoading(true);
        
        // Create a change operation to update the entire document
        const change: ChangeOperation = {
          operation: 'replace',
          replacement: content
        };
        
        const updatedDoc = await apiService.updateDocument(
          document.id,
          { changes: [change] },
          document.etag
        );
        setDocument(updatedDoc);
        onDocumentUpdated(updatedDoc);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to update document');
      } finally {
        setLoading(false);
      }
    }
  };

  const applyChange = async () => {
    if (!document) {
      setError('No document loaded');
      return;
    }

    try {
      setLoading(true);
      
      let change: ChangeOperation;
      
      if (useRange) {
        change = {
          operation: 'replace',
          range: { start: startPos, end: endPos },
          replacement: replacementText
        };
      } else {
        change = {
          operation: 'replace',
          target: { text: targetText, occurrence },
          replacement: replacementText
        };
      }

      const updatedDoc = await apiService.updateDocument(
        document.id,
        { changes: [change] },
        document.etag
      );

      setDocument(updatedDoc);
      setContent(updatedDoc.content);
      setError(null);
      
      // Clear change form
      setTargetText('');
      setReplacementText('');
      setStartPos(0);
      setEndPos(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply change');
    } finally {
      setLoading(false);
    }
  };

  const handleContentChange = (newContent: string) => {
    setContent(newContent);
    if (document) {
      // Update document object with new content for ETag calculation
      setDocument({ ...document, content: newContent });
    }
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <span className="ml-2">Loading...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DocumentIcon className="h-5 w-5" />
            {document ? 'Edit Document' : 'Create New Document'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Title</label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Document title"
              className="mt-1"
            />
          </div>
          
          <div>
            <label className="text-sm font-medium">Content</label>
            <Textarea
              value={content}
              onChange={(e) => handleContentChange(e.target.value)}
              placeholder="Document content..."
              className="mt-1 min-h-[300px]"
            />
          </div>

          {error && (
            <div className="text-red-600 text-sm bg-red-50 p-3 rounded">
              {error}
            </div>
          )}

          <div className="flex gap-2">
            <Button onClick={handleSave} disabled={loading}>
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              {document ? 'Update' : 'Create'}
            </Button>
            {document && (
              <Button variant="outline" onClick={() => {
                setDocument(selectedDocument);
                setTitle(selectedDocument?.title || '');
                setContent(selectedDocument?.content || '');
              }}>
                <ArrowPathIcon className="h-4 w-4 mr-2" />
                Reload
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {document && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PencilIcon className="h-5 w-5" />
              Apply Changes (Redlining)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="text" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="text">Text-based</TabsTrigger>
                <TabsTrigger value="range">Range-based</TabsTrigger>
              </TabsList>
              
              <TabsContent value="text" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Target Text</label>
                    <Input
                      value={targetText}
                      onChange={(e) => setTargetText(e.target.value)}
                      placeholder="Text to find and replace"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Occurrence</label>
                    <Input
                      type="number"
                      min="1"
                      value={occurrence}
                      onChange={(e) => setOccurrence(parseInt(e.target.value) || 1)}
                      className="mt-1"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium">Replacement Text</label>
                  <Input
                    value={replacementText}
                    onChange={(e) => setReplacementText(e.target.value)}
                    placeholder="New text"
                    className="mt-1"
                  />
                </div>
              </TabsContent>
              
              <TabsContent value="range" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Start Position</label>
                    <Input
                      type="number"
                      min="0"
                      value={startPos}
                      onChange={(e) => setStartPos(parseInt(e.target.value) || 0)}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">End Position</label>
                    <Input
                      type="number"
                      min="0"
                      value={endPos}
                      onChange={(e) => setEndPos(parseInt(e.target.value) || 0)}
                      className="mt-1"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium">Replacement Text</label>
                  <Input
                    value={replacementText}
                    onChange={(e) => setReplacementText(e.target.value)}
                    placeholder="New text"
                    className="mt-1"
                  />
                </div>
              </TabsContent>
            </Tabs>
            
            <Button 
              onClick={applyChange} 
              disabled={loading || (!targetText && !useRange) || !replacementText}
              className="mt-4"
            >
              <PencilIcon className="h-4 w-4 mr-2" />
              Apply Change
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
