import React, { useState, useEffect } from 'react';
import { DocumentList } from './components/DocumentList';
import { DocumentEditor } from './components/DocumentEditor';
import { SearchPanel } from './components/SearchPanel';
import { LLMAnalysis } from './components/LLMAnalysis';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Document } from './types';
import { apiService } from './services/api';
import { 
  CpuChipIcon, 
  DocumentIcon, 
  MagnifyingGlassIcon, 
  PencilIcon 
} from '@heroicons/react/24/outline';

function App() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("documents");

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const docs = await apiService.getDocuments();
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentCreated = (newDocument: Document) => {
    setDocuments(prev => [newDocument, ...prev]);
    setSelectedDocument(newDocument);
    setActiveTab("documents"); // Switch back to documents tab to show the new document
  };

  const handleDocumentUpdated = (updatedDocument: Document) => {
    setDocuments(prev => prev.map(doc => 
      doc.id === updatedDocument.id ? updatedDocument : doc
    ));
    setSelectedDocument(updatedDocument);
  };

  const handleDocumentDeleted = (documentId: number) => {
    setDocuments(prev => prev.filter(doc => doc.id !== documentId));
    if (selectedDocument?.id === documentId) {
      setSelectedDocument(null);
    }
  };

  const handleDocumentSelect = (document: Document) => {
    setSelectedDocument(document);
    setActiveTab("editor"); // Automatically switch to editor tab
  };

  const handleNewDocument = () => {
    // Refresh documents list instead of switching tabs
    fetchDocuments();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Stealth Legal AI
          </h1>
          <p className="text-xl text-gray-600">
            Intelligent Document Management & Legal Analysis
          </p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                      <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="documents" className="flex items-center gap-2">
                <DocumentIcon className="h-4 w-4" />
                Documents
              </TabsTrigger>
              <TabsTrigger value="editor" className="flex items-center gap-2">
                <PencilIcon className="h-4 w-4" />
                Editor
              </TabsTrigger>
              <TabsTrigger value="search" className="flex items-center gap-2">
                <MagnifyingGlassIcon className="h-4 w-4" />
                Search
              </TabsTrigger>
              <TabsTrigger value="ai-analysis" className="flex items-center gap-2">
                <CpuChipIcon className="h-4 w-4" />
                AI Analysis
              </TabsTrigger>
            </TabsList>

          <TabsContent value="documents" className="mt-6">
            <DocumentList
              documents={documents}
              onDocumentSelect={handleDocumentSelect}
              onDocumentDeleted={handleDocumentDeleted}
              onNewDocument={handleNewDocument}
              loading={loading}
            />
          </TabsContent>

          <TabsContent value="editor" className="mt-6">
            <DocumentEditor
              selectedDocument={selectedDocument}
              onDocumentCreated={handleDocumentCreated}
              onDocumentUpdated={handleDocumentUpdated}
            />
          </TabsContent>

          <TabsContent value="search" className="mt-6">
            <SearchPanel />
          </TabsContent>

          <TabsContent value="ai-analysis" className="mt-6">
            {selectedDocument ? (
              <LLMAnalysis
                documentId={selectedDocument.id}
                documentTitle={selectedDocument.title}
                documentContent={selectedDocument.content}
              />
            ) : (
              <div className="text-center py-12">
                <CpuChipIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Select a Document for AI Analysis
                </h3>
                <p className="text-gray-600">
                  Choose a document from the Documents tab to analyze it with our AI-powered legal analysis tools.
                </p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default App;
