'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useOrganization } from '@clerk/nextjs';
import { ArrowLeft, Zap, FileText, ExternalLink, Loader2, CheckCircle2, AlertTriangle } from 'lucide-react';
import { api, DocumentDetail, MergeResult } from '@/lib/api';

function MergePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { organization } = useOrganization();
  
  const pairId = searchParams.get('pairId');
  
  const [mergeData, setMergeData] = useState<MergeResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [merging, setMerging] = useState(false);
  const [applying, setApplying] = useState(false);
  const [mergedContent, setMergedContent] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!pairId || !organization?.id) {
      setError('Missing pair ID or organization');
      setLoading(false);
      return;
    }

    loadMergeData();
  }, [pairId, organization?.id]);

  const loadMergeData = async () => {
    if (!pairId || !organization?.id) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const data = await api.getMergeDocuments(parseInt(pairId), organization.id);
      setMergeData(data);
    } catch (err) {
      setError('Failed to load documents for merging');
    } finally {
      setLoading(false);
    }
  };

  const handleMerge = async () => {
    if (!pairId || !organization?.id) return;
    
    setMerging(true);
    setError(null);
    
    try {
      const result = await api.performMerge({
        pair_id: parseInt(pairId),
        organization_id: organization.id
      });
      
      setMergedContent(result.merged_content);
      setSuccess('Documents merged successfully!');
    } catch (err) {
      setError('Failed to merge documents');
    } finally {
      setMerging(false);
    }
  };

  const handleApplyMerge = async (keepMain: boolean) => {
    if (!pairId || !organization?.id || !mergedContent) return;
    
    setApplying(true);
    setError(null);
    
    try {
      const result = await api.applyMerge({
        pair_id: parseInt(pairId),
        organization_id: organization.id,
        merged_content: mergedContent,
        keep_main: keepMain
      });
      
      setSuccess('Merge applied successfully to Confluence!');
      
      // Redirect back to main app with content-report page and refresh
      setTimeout(() => {
        router.push('/?page=content-report&refresh=true');
      }, 2000);
    } catch (err) {
      setError('Failed to apply merge to Confluence');
    } finally {
      setApplying(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="flex items-center space-x-3">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
              <span className="text-lg text-foreground">Loading documents...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !mergeData) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-destructive" />
            <h2 className="text-xl font-semibold mb-2 text-foreground">Unable to Load Documents</h2>
            <p className="text-muted-foreground mb-4">{error}</p>
            <button
              onClick={() => router.push('/?page=content-report&refresh=true')}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
            >
              Back to Content Report
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <button
              onClick={() => router.push('/?page=content-report&refresh=true')}
              className="flex items-center space-x-2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
              <span>Back to Content Report</span>
            </button>
          </div>
          
          <h1 className="text-3xl font-bold mb-2 text-foreground">
            Merge Documents
          </h1>
          <p className="text-muted-foreground">
            Compare similar documents and merge them with AI assistance
          </p>
          
          {mergeData && (
            <div className="mt-4 flex items-center space-x-3">
              <span className="text-lg font-semibold text-foreground">
                Similarity: {Math.round(mergeData.similarity * 100)}%
              </span>
              <span className={`text-sm px-3 py-1 rounded-full font-medium ${
                mergeData.similarity >= 0.9 ? 'bg-red-100 text-red-800' :
                mergeData.similarity >= 0.8 ? 'bg-orange-100 text-orange-800' :
                mergeData.similarity >= 0.7 ? 'bg-yellow-100 text-yellow-800' :
                'bg-green-100 text-green-800'
              }`}>
                {mergeData.similarity >= 0.9 ? 'Very High' :
                 mergeData.similarity >= 0.8 ? 'High' :
                 mergeData.similarity >= 0.7 ? 'Medium' : 'Low'} Similarity
              </span>
            </div>
          )}
        </div>

        {/* Status Messages */}
        {error && (
          <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              <span className="text-destructive">{error}</span>
            </div>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-green-100 border border-green-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <span className="text-green-800">{success}</span>
            </div>
          </div>
        )}

        {mergeData && (
          <>
            {/* Side by Side Document Comparison */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* Primary Document */}
              <div className="bg-card rounded-lg border border-border p-6">
                <div className="flex items-start space-x-3 mb-4">
                  <FileText className="h-5 w-5 text-primary mt-1 flex-shrink-0" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-foreground mb-2">
                      Primary Document
                    </h3>
                    <h4 className="text-lg font-medium text-foreground mb-2">
                      {mergeData.main_doc.title}
                    </h4>
                    {mergeData.main_doc.space && (
                      <div className="mb-3">
                        <span className="bg-primary/10 text-primary px-2 py-1 rounded text-sm">
                          Space: {mergeData.main_doc.space}
                        </span>
                      </div>
                    )}
                    <a
                      href={mergeData.main_doc.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1 text-sm text-primary hover:underline mb-4"
                    >
                      <span>View Original</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                </div>
                
                <div className="bg-muted/30 rounded-lg p-4 max-h-96 overflow-y-auto">
                  <div 
                    className="prose prose-sm max-w-none text-foreground"
                    dangerouslySetInnerHTML={{ __html: mergeData.main_doc.content.substring(0, 1000) + (mergeData.main_doc.content.length > 1000 ? '...' : '') }}
                  />
                </div>
              </div>

              {/* Similar Document */}
              <div className="bg-card rounded-lg border border-border p-6">
                <div className="flex items-start space-x-3 mb-4">
                  <FileText className="h-5 w-5 text-orange-500 mt-1 flex-shrink-0" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-foreground mb-2">
                      Similar Document
                    </h3>
                    <h4 className="text-lg font-medium text-foreground mb-2">
                      {mergeData.similar_doc.title}
                    </h4>
                    {mergeData.similar_doc.space && (
                      <div className="mb-3">
                        <span className="bg-orange-100 text-orange-800 px-2 py-1 rounded text-sm">
                          Space: {mergeData.similar_doc.space}
                        </span>
                      </div>
                    )}
                    <a
                      href={mergeData.similar_doc.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1 text-sm text-primary hover:underline mb-4"
                    >
                      <span>View Original</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                </div>
                
                <div className="bg-muted/30 rounded-lg p-4 max-h-96 overflow-y-auto">
                  <div 
                    className="prose prose-sm max-w-none text-foreground"
                    dangerouslySetInnerHTML={{ __html: mergeData.similar_doc.content.substring(0, 1000) + (mergeData.similar_doc.content.length > 1000 ? '...' : '') }}
                  />
                </div>
              </div>
            </div>

            {/* Merge Controls */}
            <div className="bg-card rounded-lg border border-border p-6 mb-8">
              <h3 className="text-xl font-semibold mb-4 text-foreground">
                AI Document Merge
              </h3>
              
              {!mergedContent ? (
                <div className="text-center">
                  <p className="text-muted-foreground mb-6">
                    Use AI to intelligently merge these documents, combining the best content from both while eliminating redundancy.
                  </p>
                  <button
                    onClick={handleMerge}
                    disabled={merging}
                    className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 mx-auto"
                  >
                    {merging ? (
                      <>
                        <Loader2 className="h-5 w-5 animate-spin" />
                        <span>Merging with AI...</span>
                      </>
                    ) : (
                      <>
                        <Zap className="h-5 w-5" />
                        <span>Merge with AI</span>
                      </>
                    )}
                  </button>
                </div>
              ) : (
                <div>
                  <h4 className="font-semibold mb-3 text-foreground">Merged Result</h4>
                  <div className="bg-muted/30 rounded-lg p-4 max-h-96 overflow-y-auto mb-6">
                    <div 
                      className="prose prose-sm max-w-none text-foreground"
                      dangerouslySetInnerHTML={{ __html: mergedContent }}
                    />
                  </div>
                  
                  <div className="border-t pt-6">
                    <h4 className="font-semibold mb-4 text-foreground">Apply to Confluence</h4>
                    <p className="text-muted-foreground mb-6">
                      Choose which page title to keep. The merged content will replace the selected page, and the other page will be deleted.
                    </p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <button
                        onClick={() => handleApplyMerge(true)}
                        disabled={applying}
                        className="p-4 border border-border rounded-lg text-left hover:bg-muted/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <div className="flex items-center space-x-3">
                          <FileText className="h-5 w-5 text-primary flex-shrink-0" />
                          <div>
                            <div className="font-medium text-foreground">Keep Primary Title</div>
                            <div className="text-sm text-muted-foreground">{mergeData.main_doc.title}</div>
                          </div>
                        </div>
                      </button>
                      
                      <button
                        onClick={() => handleApplyMerge(false)}
                        disabled={applying}
                        className="p-4 border border-border rounded-lg text-left hover:bg-muted/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <div className="flex items-center space-x-3">
                          <FileText className="h-5 w-5 text-orange-500 flex-shrink-0" />
                          <div>
                            <div className="font-medium text-foreground">Keep Similar Title</div>
                            <div className="text-sm text-muted-foreground">{mergeData.similar_doc.title}</div>
                          </div>
                        </div>
                      </button>
                    </div>
                    
                    {applying && (
                      <div className="mt-4 flex items-center justify-center space-x-2 text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span>Applying merge to Confluence...</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Warning */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="h-5 w-5 text-yellow-600 mt-1 flex-shrink-0" />
                <div>
                  <h4 className="font-medium text-yellow-800 mb-1">Important</h4>
                  <p className="text-sm text-yellow-700">
                    Applying the merge will permanently update one page and delete the other in Confluence. 
                    Make sure you have reviewed the merged content and have the necessary permissions.
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default function MergePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="flex items-center space-x-3">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
              <span className="text-lg text-foreground">Loading...</span>
            </div>
          </div>
        </div>
      </div>
    }>
      <MergePageContent />
    </Suspense>
  );
}
