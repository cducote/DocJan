'use client';

import React, { useState, useEffect } from 'react';
import Sidebar from '@/components/sidebar';
import { useOrganization } from '@clerk/nextjs';
import { FileText, ExternalLink, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';
import { api } from '../lib/api';
import { useRouter } from 'next/navigation';

interface ContentReportPageProps {
  platform: 'confluence' | 'sharepoint';
  shouldRefresh?: boolean;
  onRefreshComplete?: () => void;
}

interface DuplicatePair {
  id: number;
  page1: {
    title: string;
    url: string;
    space?: string;
  };
  page2: {
    title: string;
    url: string;
    space?: string;
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

export default function ContentReportPage({ platform, shouldRefresh, onRefreshComplete }: ContentReportPageProps) {
  const { organization } = useOrganization();
  const router = useRouter();
  const [duplicatesData, setDuplicatesData] = useState<DuplicatesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const platformName = platform === 'confluence' ? 'Confluence' : 'SharePoint';

  useEffect(() => {
    if (organization?.id) {
      loadDuplicatesData();
    }
  }, [organization?.id]);

  // Check for refresh prop (when returning from merge)
  useEffect(() => {
    if (shouldRefresh && organization?.id) {
      // Force refresh the data
      loadDuplicatesData(true);
      // Notify parent that refresh is complete
      onRefreshComplete?.();
    }
  }, [shouldRefresh, organization?.id]);

  const loadDuplicatesData = async (forceRefresh = false) => {
    if (!organization?.id) return;
    
    if (forceRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);
    
    try {
      // If forceRefresh is true, trigger backend refresh first
      if (forceRefresh) {
        try {
          await api.refreshDuplicates(organization.id);
          console.log('Successfully refreshed duplicate data on backend');
        } catch (refreshError) {
          console.warn('Failed to refresh backend data, continuing with cached data:', refreshError);
        }
      }
      
      // Fetch the duplicate pairs
      const duplicatesArray = await api.getDuplicates(organization.id);
      
      // Create the data structure with just the duplicate pairs
      const combinedData: DuplicatesData = {
        duplicate_pairs: duplicatesArray,
        total_pairs: duplicatesArray.length,
        total_documents: 0, // Not needed for the display
        documents_with_duplicates: 0 // Not needed for the display
      };
      
      setDuplicatesData(combinedData);
    } catch (err) {
      setError('Failed to load content report. Please ensure data ingestion is complete.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    loadDuplicatesData(true);
  };

  const getReadableSpaceName = (spaceName: string): string => {
    // Since we now store the actual space name from Confluence, just return it as-is
    if (!spaceName || spaceName === 'Unknown') {
      return 'Unknown Space';
    }
    
    return spaceName;
  };

  const handleMerge = (pairId: number) => {
    // Navigate to merge page with the pair ID
    router.push(`/merge?pairId=${pairId}`);
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
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {refreshing ? 'Refreshing...' : 'Retry'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold mb-2 text-foreground">
            Content Report - {platformName}
          </h1>
          <p className="text-muted-foreground">
            Review duplicate content pairs detected across your {platformName} workspace
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {refreshing ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Refreshing...
            </>
          ) : (
            <>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </>
          )}
        </button>
      </div>

      {/* Content Pairs */}
      {duplicatesData?.duplicate_pairs && duplicatesData.duplicate_pairs.length > 0 ? (
        <div className="space-y-6">
          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2 text-foreground">
              Found {duplicatesData.duplicate_pairs.length} Duplicate Pair{duplicatesData.duplicate_pairs.length !== 1 ? 's' : ''}
            </h2>
            <p className="text-muted-foreground">
              Review and manage content that appears to be duplicated across your workspace
            </p>
          </div>
          
          {duplicatesData.duplicate_pairs.map((pair) => (
            <div
              key={pair.id}
              className="bg-card rounded-lg border border-border p-6 hover:shadow-lg transition-shadow"
            >
              {/* Similarity Score Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <span className="text-lg font-semibold text-foreground">
                    Similarity: {Math.round(pair.similarity * 100)}%
                  </span>
                  <span className={`text-sm px-3 py-1 rounded-full font-medium ${
                    pair.similarity >= 0.9 ? 'bg-red-100 text-red-800' :
                    pair.similarity >= 0.8 ? 'bg-orange-100 text-orange-800' :
                    pair.similarity >= 0.7 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {pair.similarity >= 0.9 ? 'Very High' :
                     pair.similarity >= 0.8 ? 'High' :
                     pair.similarity >= 0.7 ? 'Medium' : 'Low'}
                  </span>
                </div>
                <div className="text-sm text-muted-foreground">
                  Pair #{pair.id}
                </div>
              </div>

              {/* Document Pair */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Document 1 */}
                <div className="border border-border rounded-lg p-4 bg-muted/30">
                  <div className="flex items-start space-x-3">
                    <FileText className="h-5 w-5 text-muted-foreground mt-1 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-foreground mb-2 leading-tight">
                        {pair.page1.title}
                      </h3>
                      {pair.page1.space && pair.page1.space.trim() !== '' && (
                        <div className="text-sm text-muted-foreground mb-3 flex items-center">
                          <span className="bg-muted px-2 py-1 rounded text-xs">
                            Space: {getReadableSpaceName(pair.page1.space)}
                          </span>
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
                <div className="border border-border rounded-lg p-4 bg-muted/30">
                  <div className="flex items-start space-x-3">
                    <FileText className="h-5 w-5 text-muted-foreground mt-1 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-foreground mb-2 leading-tight">
                        {pair.page2.title}
                      </h3>
                      {pair.page2.space && (
                        <div className="text-sm text-muted-foreground mb-3 flex items-center">
                          <span className="bg-muted px-2 py-1 rounded text-xs">
                            Space: {getReadableSpaceName(pair.page2.space)}
                          </span>
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

              {/* Merge Button */}
              <div className="flex justify-center">
                <button 
                  onClick={() => handleMerge(pair.id)}
                  className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium"
                >
                  Merge Documents
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-card rounded-lg border border-border">
          <CheckCircle className="h-12 w-12 mx-auto mb-4 text-primary" />
          <h2 className="text-xl font-semibold mb-2 text-foreground">No Duplicates Found</h2>
          <p className="text-muted-foreground">
            Your {platformName} workspace appears to have unique content with no significant duplicates detected.
          </p>
        </div>
      )}
    </div>
  );
}
