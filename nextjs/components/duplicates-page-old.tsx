'use client';

import { useState, useEffect } from 'react';
import { useOrganization } from '@clerk/nextjs';
import { FileText, ExternalLink, TrendingUp, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { api } from '../lib/api';

interface ContentReportPageProps {
  platform: 'confluence' | 'sharepoint';
}

interface DuplicatePair {
  id: number;
  page1: {
    title: string;
    url: string;
    space_name?: string;
    space_id?: string;
  };
  page2: {
    title: string;
    url: string;
    space_name?: string;
    space_id?: string;
  };
  similarity: number;
  status: string;
}

interface DuplicatesData {
  duplicate_pairs: DuplicatePair[];
  total_pairs: number;
  total_documents: number;
  documents_with_duplicates: number;
}

export default function ContentReportPage({ platform }: ContentReportPageProps) {
  const { organization } = useOrganization();
  const [duplicatesData, setDuplicatesData] = useState<DuplicatesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const platformName = platform === 'confluence' ? 'Confluence' : 'SharePoint';

  useEffect(() => {
    if (organization?.id) {
      loadDuplicatesData();
    }
  }, [organization?.id]);

  const loadDuplicatesData = async () => {
    if (!organization?.id) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const data = await api.getDuplicates();
      setDuplicatesData(data);
    } catch (err) {
      console.error('Failed to load duplicates data:', err);
      setError('Failed to load content report. Please ensure data ingestion is complete.');
    } finally {
      setLoading(false);
    }
  };

  const getSimilarityLevel = (similarity: number) => {
    if (similarity >= 0.9) return { level: 'Very High', color: 'text-destructive' };
    if (similarity >= 0.8) return { level: 'High', color: 'text-secondary-foreground' };
    if (similarity >= 0.7) return { level: 'Medium', color: 'text-accent-foreground' };
    return { level: 'Low', color: 'text-primary' };
  };

  const getSimilarityIcon = (similarity: number) => {
    if (similarity >= 0.9) return <AlertTriangle className="h-4 w-4" />;
    if (similarity >= 0.8) return <TrendingUp className="h-4 w-4" />;
    return <Clock className="h-4 w-4" />;
  };

  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-6 w-6 border-2 border-primary border-t-transparent"></div>
            <span className="text-lg text-foreground">Loading content report...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="text-center py-12">
          <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-secondary-foreground" />
          <h2 className="text-xl font-semibold mb-2 text-foreground">Unable to Load Report</h2>
          <p className="text-muted-foreground mb-4">{error}</p>
          <button
            onClick={loadDuplicatesData}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 text-foreground">
          Content Report - {platformName}
        </h1>
        <p className="text-muted-foreground">
          Analyze similar content patterns and potential duplicates across your {platformName} workspace
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-card rounded-lg border border-border p-6">
          <div className="flex items-center space-x-3">
            <FileText className="h-8 w-8 text-primary" />
            <div>
              <div className="text-2xl font-bold text-foreground">{duplicatesData?.total_documents || 0}</div>
              <div className="text-sm text-muted-foreground">Total Documents</div>
            </div>
          </div>
        </div>

        <div className="bg-card rounded-lg border border-border p-6">
          <div className="flex items-center space-x-3">
            <TrendingUp className="h-8 w-8 text-secondary-foreground" />
            <div>
              <div className="text-2xl font-bold text-foreground">{duplicatesData?.total_pairs || 0}</div>
              <div className="text-sm text-muted-foreground">Similar Pairs</div>
            </div>
          </div>
        </div>

        <div className="bg-card rounded-lg border border-border p-6">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="h-8 w-8 text-destructive" />
            <div>
              <div className="text-2xl font-bold text-foreground">{duplicatesData?.documents_with_duplicates || 0}</div>
              <div className="text-sm text-muted-foreground">Affected Documents</div>
            </div>
          </div>
        </div>

        <div className="bg-card rounded-lg border border-border p-6">
          <div className="flex items-center space-x-3">
            <CheckCircle className="h-8 w-8 text-accent-foreground" />
            <div>
              <div className="text-2xl font-bold text-foreground">
                {duplicatesData?.total_documents && duplicatesData?.documents_with_duplicates 
                  ? Math.round(((duplicatesData.total_documents - duplicatesData.documents_with_duplicates) / duplicatesData.total_documents) * 100)
                  : 0}%
              </div>
              <div className="text-sm text-muted-foreground">Unique Content</div>
            </div>
          </div>
        </div>
      </div>

      {/* Content Pairs */}
      {duplicatesData?.duplicate_pairs && duplicatesData.duplicate_pairs.length > 0 ? (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold mb-4">Similar Content Pairs</h2>
          
          {duplicatesData.duplicate_pairs.map((pair) => {
            const simInfo = getSimilarityLevel(pair.similarity);
            const simIcon = getSimilarityIcon(pair.similarity);
            
            return (
              <div
                key={pair.id}
                className="bg-card rounded-lg border border-border p-6 hover:shadow-lg transition-shadow"
              >
                {/* Similarity Score Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <div className={simInfo.color}>
                      {simIcon}
                    </div>
                    <span className="font-medium text-foreground">Similarity Score</span>
                    <span className={`font-bold ${simInfo.color}`}>
                      {Math.round(pair.similarity * 100)}%
                    </span>
                    <span className={`text-sm px-2 py-1 rounded-full bg-muted ${simInfo.color}`}>
                      {simInfo.level}
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Pair #{pair.id}
                  </div>
                </div>

                {/* Document Pair */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Document 1 */}
                  <div className="border border-border rounded-lg p-4">
                    <div className="flex items-start space-x-3">
                      <FileText className="h-5 w-5 text-muted-foreground mt-1 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-foreground mb-1 truncate">
                          {pair.page1.title}
                        </h3>
                        {pair.page1.space && (
                          <div className="text-sm text-muted-foreground mb-2">
                            Space: {pair.page1.space}
                          </div>
                        )}
                        <a
                          href={pair.page1.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1 text-sm text-primary hover:underline"
                        >
                          <span>View Document</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    </div>
                  </div>

                  {/* Document 2 */}
                  <div className="border border-border rounded-lg p-4">
                    <div className="flex items-start space-x-3">
                      <FileText className="h-5 w-5 text-muted-foreground mt-1 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-foreground mb-1 truncate">
                          {pair.page2.title}
                        </h3>
                        {pair.page2.space && (
                          <div className="text-sm text-muted-foreground mb-2">
                            Space: {pair.page2.space}
                          </div>
                        )}
                        <a
                          href={pair.page2.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1 text-sm text-primary hover:underline"
                        >
                          <span>View Document</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center justify-end space-x-3 mt-4 pt-4 border-t border-border">
                  <button className="px-4 py-2 text-sm border border-border rounded-lg hover:bg-muted transition-colors">
                    Ignore
                  </button>
                  <button className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors">
                    Review Merge
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-12 bg-card rounded-lg border border-border">
          <CheckCircle className="h-12 w-12 mx-auto mb-4 text-primary" />
          <h2 className="text-xl font-semibold mb-2 text-foreground">No Similar Content Found</h2>
          <p className="text-muted-foreground">
            Your {platformName} workspace appears to have unique content with no significant duplicates detected.
          </p>
        </div>
      )}
    </div>
  );
}
