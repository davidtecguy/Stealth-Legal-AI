import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { SearchResult } from '../types';
import { apiService } from '../services/api';
import { FaSearch, FaFileAlt, FaExternalLinkAlt } from 'react-icons/fa';

interface SearchPanelProps {
  documentId?: number;
  onDocumentSelect?: (documentId: number) => void;
}

export const SearchPanel: React.FC<SearchPanelProps> = ({ 
  documentId, 
  onDocumentSelect 
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const limit = 10;

  const performSearch = async (searchOffset = 0) => {
    if (!query.trim()) return;

    try {
      setLoading(true);
      setError(null);

      const response = documentId 
        ? await apiService.searchDocument(documentId, query, limit, searchOffset)
        : await apiService.searchDocuments(query, limit, searchOffset);

      setResults(response.results);
      setTotal(response.total_results);
      setOffset(searchOffset);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      setResults([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(0);
  };

  const handleNextPage = () => {
    performSearch(offset + limit);
  };

  const handlePrevPage = () => {
    performSearch(Math.max(0, offset - limit));
  };

  const highlightText = (text: string, query: string) => {
    if (!query) return text;
    
    const regex = new RegExp(`(${query})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 px-1 rounded">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FaSearch className="h-5 w-5" />
          {documentId ? 'Search in Document' : 'Search All Documents'}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleSearch} className="flex gap-2">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter search query..."
            className="flex-1"
          />
          <Button type="submit" disabled={loading || !query.trim()}>
            <FaSearch className="h-4 w-4 mr-2" />
            Search
          </Button>
        </form>

        {error && (
          <div className="text-red-600 text-sm bg-red-50 p-3 rounded">
            {error}
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            <span className="ml-2">Searching...</span>
          </div>
        )}

        {results.length > 0 && (
          <div className="space-y-4">
            <div className="text-sm text-muted-foreground">
              Found {total} result{total !== 1 ? 's' : ''}
            </div>
            
            <div className="space-y-3">
              {results.map((result, index) => (
                <Card key={index} className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <FaFileAlt className="h-4 w-4 text-muted-foreground" />
                        <h4 className="font-medium">{result.title}</h4>
                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                          Score: {result.relevance_score}
                        </span>
                      </div>
                      
                      <div className="space-y-2">
                        {result.context.map((context, ctxIndex) => (
                          <div key={ctxIndex} className="text-sm text-muted-foreground bg-gray-50 p-2 rounded">
                            "...{highlightText(context, query)}..."
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    {!documentId && onDocumentSelect && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onDocumentSelect(result.id)}
                        className="ml-2"
                      >
                        <FaExternalLinkAlt className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </Card>
              ))}
            </div>

            {total > limit && (
              <div className="flex items-center justify-between">
                <Button
                  variant="outline"
                  onClick={handlePrevPage}
                  disabled={offset === 0 || loading}
                >
                  Previous
                </Button>
                
                <span className="text-sm text-muted-foreground">
                  {offset + 1}-{Math.min(offset + limit, total)} of {total}
                </span>
                
                <Button
                  variant="outline"
                  onClick={handleNextPage}
                  disabled={offset + limit >= total || loading}
                >
                  Next
                </Button>
              </div>
            )}
          </div>
        )}

        {!loading && results.length === 0 && query && !error && (
          <div className="text-center py-8 text-muted-foreground">
            <FaSearch className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No results found for "{query}"</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
