import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';

import { 
  CpuChipIcon, 
  DocumentIcon, 
  ExclamationTriangleIcon, 
  LightBulbIcon, 
  ClockIcon, 
  BoltIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { 
  LLMAnalysisResponse, 
  DocumentAnalysis, 
  LegalSuggestion, 
  LegalTerm, 
  DocumentClassification,
  LLMStatus 
} from '../types';
import { apiService } from '../services/api';

interface LLMAnalysisProps {
  documentId: number;
  documentTitle: string;
  documentContent: string;
}

export const LLMAnalysis: React.FC<LLMAnalysisProps> = ({ 
  documentId, 
  documentTitle, 
  documentContent 
}) => {
  const [analysis, setAnalysis] = useState<LLMAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [llmStatus, setLlmStatus] = useState<LLMStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkLLMStatus();
  }, []);

  const checkLLMStatus = async () => {
    try {
      const status = await apiService.getLLMStatus();
      setLlmStatus(status);
    } catch (err) {
      console.error('Failed to check LLM status:', err);
    }
  };

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiService.analyzeDocumentLLM(documentId);
      setAnalysis(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = () => {
    if (!llmStatus) return <InformationCircleIcon className="h-4 w-4" />;
    return llmStatus.enabled ? <CheckCircleIcon className="h-4 w-4 text-green-500" /> : <XCircleIcon className="h-4 w-4 text-red-500" />;
  };

  const getStatusColor = () => {
    if (!llmStatus) return "bg-gray-100 text-gray-800";
    return llmStatus.enabled ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800";
  };

  if (!llmStatus) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CpuChipIcon className="h-5 w-5" />
            LLM Legal AI Analysis
          </CardTitle>
          <CardDescription>
            Checking LLM service status...
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CpuChipIcon className="h-5 w-5" />
          LLM Legal AI Analysis
        </CardTitle>
        <CardDescription>
          Intelligent document analysis powered by AI
        </CardDescription>
        
        {/* LLM Status */}
        <div className="flex items-center gap-2">
          <Badge className={getStatusColor()}>
            {getStatusIcon()}
            {llmStatus.enabled ? 'LLM Enabled' : 'LLM Disabled'}
          </Badge>
          {llmStatus.enabled && (
            <>
              <Badge variant="outline">
                                    <BoltIcon className="h-3 w-3 mr-1" />
                {llmStatus.model}
              </Badge>
              <Badge variant="outline">
                                    <ClockIcon className="h-3 w-3 mr-1" />
                {llmStatus.max_tokens} tokens
              </Badge>
            </>
          )}
        </div>
      </CardHeader>

      <CardContent>
        {!llmStatus.enabled ? (
          <div className="text-center py-8">
                            <XCircleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">LLM Service Unavailable</h3>
            <p className="text-gray-600 mb-4">
              OpenAI API key not configured. LLM features are disabled.
            </p>
            <p className="text-sm text-gray-500">
              Set OPENAI_API_KEY environment variable to enable AI-powered analysis.
            </p>
          </div>
        ) : (
          <>
            <div className="mb-6">
              <Button 
                onClick={runAnalysis} 
                disabled={loading}
                className="w-full"
              >
                {loading ? (
                  <>
                    <ClockIcon className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing Document...
                  </>
                ) : (
                  <>
                    <CpuChipIcon className="h-4 w-4 mr-2" />
                    Run AI Analysis
                  </>
                )}
              </Button>
            </div>

            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center gap-2 text-red-800">
                  <ExclamationTriangleIcon className="h-4 w-4" />
                  <span className="font-medium">Analysis Error</span>
                </div>
                <p className="text-red-700 mt-1">{error}</p>
              </div>
            )}

            {analysis && (
              <Tabs defaultValue="overview" className="w-full">
                <TabsList className="grid w-full grid-cols-5">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="terms">Terms</TabsTrigger>
                  <TabsTrigger value="risks">Risks</TabsTrigger>
                  <TabsTrigger value="suggestions">Suggestions</TabsTrigger>
                  <TabsTrigger value="classification">Classification</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">Document Type</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-2xl font-bold">{analysis.analysis.document_type}</p>
                        <p className="text-sm text-gray-600">AI Classification</p>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">Processing Time</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-2xl font-bold">{analysis.processing_time.toFixed(2)}s</p>
                        <p className="text-sm text-gray-600">AI Analysis</p>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm font-medium">Summary</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-gray-700">{analysis.analysis.summary}</p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm font-medium">Key Terms Found</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        {analysis.analysis.key_terms.map((term, index) => (
                          <Badge key={index} variant="secondary">
                            {term}
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="terms" className="space-y-4">
                  <div className="space-y-4">
                    {analysis.terms.map((term, index) => (
                      <Card key={index}>
                        <CardHeader>
                          <CardTitle className="text-sm font-medium">{term.term}</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                          <div>
                            <span className="font-medium text-sm">Meaning:</span>
                            <p className="text-gray-700">{term.meaning}</p>
                          </div>
                          <div>
                            <span className="font-medium text-sm">Context:</span>
                            <p className="text-gray-700">{term.context}</p>
                          </div>
                          <div>
                            <span className="font-medium text-sm">Implications:</span>
                            <p className="text-gray-700">{term.implications}</p>
                          </div>
                          <Badge variant="outline" className="text-xs">
                            {term.source}
                          </Badge>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="risks" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <ExclamationTriangleIcon className="h-4 w-4 text-orange-500" />
                        Identified Risks
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {analysis.analysis.risks.map((risk, index) => (
                          <div key={index} className="flex items-start gap-3 p-3 bg-orange-50 rounded-lg">
                            <ExclamationTriangleIcon className="h-4 w-4 text-orange-500 mt-0.5 flex-shrink-0" />
                            <span className="text-orange-800">{risk}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="suggestions" className="space-y-4">
                  <div className="space-y-4">
                    {analysis.suggestions.map((suggestion, index) => (
                      <Card key={index}>
                        <CardHeader>
                          <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <LightBulbIcon className="h-4 w-4 text-yellow-500" />
                            {suggestion.type.charAt(0).toUpperCase() + suggestion.type.slice(1)} Improvement
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                          <p className="text-gray-700">{suggestion.suggestion}</p>
                          <div className="bg-gray-50 p-3 rounded-lg">
                            <span className="font-medium text-sm">Example:</span>
                            <p className="text-gray-600 text-sm mt-1">{suggestion.example}</p>
                          </div>
                          <Badge variant="outline" className="text-xs">
                            {suggestion.source}
                          </Badge>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="classification" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm font-medium">Document Classification</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <span className="text-sm font-medium text-gray-600">Type:</span>
                          <p className="font-medium">{analysis.classification.document_type}</p>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-600">Category:</span>
                          <p className="font-medium">{analysis.classification.category}</p>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-600">Complexity:</span>
                          <p className="font-medium">{analysis.classification.complexity}</p>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-600">Confidence:</span>
                          <p className="font-medium">{(analysis.classification.confidence * 100).toFixed(1)}%</p>
                        </div>
                      </div>
                      <hr className="my-4" />
                      <div>
                        <span className="text-sm font-medium text-gray-600">Source:</span>
                        <Badge variant="outline" className="ml-2">
                          {analysis.classification.source}
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};
