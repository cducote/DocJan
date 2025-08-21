'use client';

import { useState, useEffect } from 'react';
import { useOrganization } from '@clerk/nextjs';
import { Search, BarChart3, Copy, Settings, FileText, Database, AlertCircle, CheckCircle, Play } from 'lucide-react';
import { api, ConnectionStatus } from '../lib/api';

interface DashboardContentProps {
  platform: 'confluence' | 'sharepoint';
  onPageChange: (page: string) => void;
}

interface DuplicateStats {
  loading: boolean;
  duplicatePairs: number;
  totalDocuments: number;
  documentsWithDuplicates: number;
  potentialMerges: number;
  error?: string;
}

export default function DashboardContent({ platform, onPageChange }: DashboardContentProps) {
  const { organization } = useOrganization();
  const [quickSearchQuery, setQuickSearchQuery] = useState('');
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [startingSync, setStartingSync] = useState(false);
  const [duplicateStats, setDuplicateStats] = useState<DuplicateStats>({
    loading: true,
    duplicatePairs: 0,
    totalDocuments: 0,
    documentsWithDuplicates: 0,
    potentialMerges: 0
  });
  const platformName = platform === 'confluence' ? 'Confluence' : 'SharePoint';

  // Check connection status when organization changes
  useEffect(() => {
    if (organization?.id) {
      checkConnectionStatus();
    }
  }, [organization?.id]);

  const checkConnectionStatus = async () => {
    if (!organization?.id) return;
    
    setLoadingStatus(true);
    try {
      const status = await api.getConnectionStatus(organization.id);
      setConnectionStatus(status);
    } catch (error) {
      // If the API call fails, assume no setup has been done
      setConnectionStatus(null);
    } finally {
      setLoadingStatus(false);
    }
  };

  const startInitialSync = async () => {
    if (!organization?.id) return;
    
    setStartingSync(true);
    try {
      
      // Get Confluence credentials from the API (stored in organization settings)
      const credentialsResponse = await fetch('/api/organization/credentials');
      
      if (!credentialsResponse.ok) {
        const errorText = await credentialsResponse.text();
        
        if (credentialsResponse.status === 404) {
          alert('Please complete the onboarding setup first to configure your Confluence connection.');
        } else {
          alert('Failed to retrieve Confluence credentials. Please try again.');
        }
        return;
      }
      
      const credentials = await credentialsResponse.json();

      const syncResult = await api.startSync({
        organization_id: organization.id,
        confluence_url: credentials.baseUrl,
        username: credentials.username,
        api_token: credentials.apiKey,
      });

      // Refresh connection status
      await checkConnectionStatus();
      
    } catch (error) {
      alert('Failed to start data ingestion. Please check your connection settings.');
    } finally {
      setStartingSync(false);
    }
  };

  useEffect(() => {
    // Only load duplicate data if we have a complete setup AND documents
    if (connectionStatus?.vector_store_connected && connectionStatus?.document_count > 0) {
      loadDuplicateData();
    }
  }, [platform, connectionStatus]);

  // Refresh data when page becomes visible (e.g., returning from merge operations)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && connectionStatus?.vector_store_connected && connectionStatus?.document_count > 0) {
        // Only refresh if we have been away for more than 30 seconds
        const lastRefresh = sessionStorage.getItem('lastDashboardRefresh');
        const now = Date.now();
        if (!lastRefresh || now - parseInt(lastRefresh) > 30000) {
          loadDuplicateData();
          sessionStorage.setItem('lastDashboardRefresh', now.toString());
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [connectionStatus]);

  const loadDuplicateData = async () => {
    if (!organization?.id) return;
    
    setDuplicateStats(prev => ({ ...prev, loading: true, error: undefined }));

    try {
      // Use lightweight summary API instead of heavy duplicates call
      const summaryData = await api.getDuplicateSummary(organization.id);
      
      setDuplicateStats({
        loading: false,
        duplicatePairs: summaryData.duplicate_pairs,
        totalDocuments: summaryData.total_documents,
        documentsWithDuplicates: summaryData.documents_with_duplicates,
        potentialMerges: summaryData.potential_merges
      });

    } catch (error) {
      
      setDuplicateStats(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to load duplicate detection data'
      }));
    }
  };

  const handleQuickSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (quickSearchQuery.trim()) {
      // In a real app, you'd store the search query in global state
      onPageChange('search');
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">
          Dashboard - {platformName}
        </h1>
        <p className="">
          Welcome to Concatly - your {platformName} duplicate document manager!
        </p>
      </div>

      {/* Setup Status Section */}
      {loadingStatus ? (
        <div className="mb-8 p-4 bg-muted border border-border rounded-lg">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary border-t-transparent"></div>
            <span className="text-muted-foreground">Checking setup status...</span>
          </div>
        </div>
      ) : !connectionStatus?.vector_store_connected || connectionStatus?.document_count === 0 ? (
        <div className="mb-8 p-6 bg-orange-50 border border-orange-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <AlertCircle className="h-6 w-6 text-orange-600 flex-shrink-0 mt-1" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-orange-900 mb-2">
                Initial Setup Required
              </h3>
              <p className="text-orange-700 mb-4">
                To get started with duplicate detection, we need to perform an initial data ingestion from your {platformName} workspace. 
                This process will read your documents and create a searchable index for duplicate detection.
              </p>
              <div className="flex items-center space-x-4">
                <button
                  onClick={startInitialSync}
                  disabled={startingSync}
                  className="bg-orange-600 hover:bg-orange-700 disabled:bg-orange-300 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
                >
                  {startingSync ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent"></div>
                      <span>Starting...</span>
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      <span>Start Data Ingestion</span>
                    </>
                  )}
                </button>
                {connectionStatus && (
                  <div className="text-sm text-orange-600">
                    Connection: {connectionStatus.confluence_connected ? '✓' : '✗'} {platformName} | 
                    Vector Store: {connectionStatus.vector_store_connected ? '✓' : '✗'} | 
                    Documents: {connectionStatus.document_count} | 
                    Status: {connectionStatus.status}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="mb-8 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center space-x-3">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <div>
              <span className="text-green-900 font-medium">System Ready</span>
              <p className="text-sm text-green-700">
                {connectionStatus.document_count ? `${connectionStatus.document_count} documents indexed` : 'Vector store ready'}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Search Section */}
        <div className="rounded-lg shadow p-6 border border-border bg-card">
          <h2 className="text-xl font-semibold mb-4 text-foreground">
            Search {platformName}
          </h2>
          <p className="mb-4 text-muted-foreground">
            {platform === 'confluence' 
              ? 'Search for Confluence pages and discover potential duplicates using semantic search.'
              : 'Search for SharePoint documents and discover potential duplicates.'
            }
          </p>
          
          <form onSubmit={handleQuickSearch} className="space-y-4">
            <div>
              <input
                type="text"
                value={quickSearchQuery}
                onChange={(e) => setQuickSearchQuery(e.target.value)}
                placeholder={(connectionStatus?.vector_store_connected && connectionStatus?.document_count > 0) ? "Enter search terms..." : "Complete setup to enable search"}
                disabled={!(connectionStatus?.vector_store_connected && connectionStatus?.document_count > 0)}
                className="w-full px-4 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
              />
            </div>
            <button
              type="submit"
              disabled={!(connectionStatus?.vector_store_connected && connectionStatus?.document_count > 0)}
              className="w-full bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-primary-foreground py-2 px-4 rounded-lg transition-colors"
            >
              {(connectionStatus?.vector_store_connected && connectionStatus?.document_count > 0) ? 'Search' : 'Setup Required'}
            </button>
          </form>
        </div>

        {/* Duplicates Section */}
        <div className="rounded-lg shadow p-6 border border-border bg-card">
          <h2 className="text-xl font-semibold mb-4 text-foreground">
            Content Analysis
          </h2>
          <p className="mb-4 text-muted-foreground">
            {platform === 'confluence'
              ? 'Review and manage Confluence page pairs that have been automatically detected as potential duplicates.'
              : 'View and manage your SharePoint document duplicates.'
            }
          </p>

          {!(connectionStatus?.vector_store_connected && connectionStatus?.document_count > 0) ? (
            <div className="text-center py-8 text-muted-foreground">
              <Database className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Complete the initial data ingestion to see duplicate detection results.</p>
            </div>
          ) : duplicateStats.loading ? (
            <div className="text-center py-8 text-muted-foreground">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent mx-auto mb-4"></div>
              <p>Loading duplicate detection data...</p>
            </div>
          ) : duplicateStats.error ? (
            <div className="text-destructive">
              <p>Error: {duplicateStats.error}</p>
              <div className="mt-4 p-4 bg-destructive/10 rounded-lg">
                <p className="font-medium">Duplicate Pairs Found: Error</p>
              </div>
            </div>
          ) : (
            <div>
              <div className="border border-border rounded-lg p-4 mb-4">
                <p className="text-2xl font-bold text-foreground mb-1">
                  {duplicateStats.duplicatePairs}
                </p>
                <p className="text-muted-foreground text-sm">Duplicate Pairs Found</p>
              </div>
              
              <div className="mb-4 text-foreground">
                {duplicateStats.duplicatePairs === 1 
                  ? `Found ${duplicateStats.duplicatePairs} duplicate pair.`
                  : `Found ${duplicateStats.duplicatePairs} duplicate pairs.`
                }
              </div>

              <button
                onClick={() => onPageChange('content-report')}
                className="w-full bg-primary text-primary-foreground py-2 px-4 rounded-lg hover:bg-primary/90 transition-colors"
              >
                View Content Report
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Statistics Section */}
      <div className="rounded-lg shadow p-6 border border-border bg-card">
        <h2 className="text-xl font-semibold mb-6 text-foreground">Statistics</h2>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground mb-1">
              {duplicateStats.loading ? '...' : duplicateStats.totalDocuments.toLocaleString()}
            </div>
            <div className="text-sm text-muted-foreground">Total Documents</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-primary mb-1">
              {duplicateStats.loading ? '...' : duplicateStats.duplicatePairs}
            </div>
            <div className="text-sm text-muted-foreground">Duplicate Pairs</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-secondary-foreground mb-1">
              {duplicateStats.loading ? '...' : duplicateStats.documentsWithDuplicates}
            </div>
            <div className="text-sm text-muted-foreground">Documents with Duplicates</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-accent-foreground mb-1">
              {duplicateStats.loading ? '...' : duplicateStats.potentialMerges}
            </div>
            <div className="text-sm text-muted-foreground">Potential Merges</div>
          </div>
        </div>
      </div>
    </div>
  );
}
