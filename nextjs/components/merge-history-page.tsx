'use client';

import React, { useState, useEffect } from 'react';
import { useOrganization } from '@clerk/nextjs';
import { ExternalLink, Undo2, RefreshCw, CheckCircle2, XCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { api, MergeHistoryItem } from '../lib/api';

interface SequentialUndoData {
  blockedOperationId: string;
  nextRequiredUndo: MergeHistoryItem;
  blockingOperations: MergeHistoryItem[];
  reason: string;
}

interface MergeHistoryPageProps {
  platform: 'confluence' | 'sharepoint';
}

export default function MergeHistoryPage({ platform }: MergeHistoryPageProps) {
  const { organization } = useOrganization();
  const [mergeHistory, setMergeHistory] = useState<MergeHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedUndo, setSelectedUndo] = useState<string | null>(null);
  const [undoLoading, setUndoLoading] = useState<Record<string, boolean>>({});
  const [showSequentialUndoModal, setShowSequentialUndoModal] = useState(false);
  const [sequentialUndoData, setSequentialUndoData] = useState<SequentialUndoData | null>(null);
  const [undoingId, setUndoingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const platformName = platform === 'confluence' ? 'Confluence' : 'SharePoint';

  useEffect(() => {
    if (organization?.id) {
      loadMergeHistory();
    }
  }, [organization?.id]);

  const loadMergeHistory = async () => {
    if (!organization?.id) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const history = await api.getMergeHistory(organization.id);
      setMergeHistory(history);
    } catch (err) {
      setError('Failed to load merge history');
      console.error('Error loading merge history:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadMergeHistory();
    setRefreshing(false);
  };

    const handleUndoMerge = async (mergeId: string) => {
    if (!organization?.id) {
      console.error('No organization ID available');
      return;
    }

    setUndoLoading(prev => ({ ...prev, [mergeId]: true }));

    try {
      // Get user credentials
      const credentialsResponse = await fetch('/api/organization/credentials');
      if (!credentialsResponse.ok) {
        throw new Error('Failed to fetch user credentials');
      }
      const credentials = await credentialsResponse.json();

      console.log('Attempting undo for merge:', mergeId);
      console.log('Organization ID:', organization.id);

      // Call the API to undo the merge
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/merge/undo`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          merge_id: mergeId,
          organization_id: organization.id,
          credentials: credentials
        })
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        console.log('Undo successful:', result.message);
        // Refresh the merge history
        await loadMergeHistory();
        // Clear selected undo
        setSelectedUndo(null);
      } else {
        console.error('Undo failed:', result);
        
        // Check if this is a sequential undo validation error
        if (result.requires_sequential_undo && result.next_required_undo) {
          // Show modal for sequential undo requirement
          setSequentialUndoData({
            blockedOperationId: mergeId,
            nextRequiredUndo: result.next_required_undo,
            blockingOperations: result.blocking_operations || [],
            reason: result.reason
          });
          setShowSequentialUndoModal(true);
        } else {
          // Show regular error
          console.error('Undo operation failed:', result.reason || 'Unknown error');
        }
      }
    } catch (error) {
      console.error('Error undoing merge:', error);
    } finally {
      setUndoLoading(prev => ({ ...prev, [mergeId]: false }));
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center px-2 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            Completed
          </span>
        );
      case 'undone':
        return (
          <span className="inline-flex items-center px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-sm font-medium">
            <Undo2 className="w-3 h-3 mr-1" />
            Undone
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center px-2 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium">
            <XCircle className="w-3 h-3 mr-1" />
            Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-sm font-medium">
            <AlertTriangle className="w-3 h-3 mr-1" />
            Unknown
          </span>
        );
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-3">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <span className="text-lg text-foreground">Loading merge history...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground mb-2">
              Merge History - {platformName}
            </h1>
            <p className="text-muted-foreground">
              View and manage your document merge operations
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center space-x-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <XCircle className="h-5 w-5 text-red-600" />
            <span className="text-red-800">{error}</span>
          </div>
        </div>
      )}

      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="h-5 w-5 text-green-600" />
            <span className="text-green-800">{success}</span>
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="mb-6 bg-muted border border-border rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {mergeHistory.filter(m => m.status === 'completed').length}
            </div>
            <div className="text-sm text-muted-foreground">Successful Merges</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {mergeHistory.filter(m => m.status === 'undone').length}
            </div>
            <div className="text-sm text-muted-foreground">Undone Merges</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">
              {mergeHistory.length}
            </div>
            <div className="text-sm text-muted-foreground">Total Operations</div>
          </div>
        </div>
      </div>

      {/* Merge History */}
      {mergeHistory.length > 0 ? (
        <div className="space-y-4">
          {mergeHistory.map((merge, index) => (
            <div key={merge.id} className="bg-card rounded-lg border border-border p-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-foreground mb-1">
                    Merge Operation #{index + 1}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Performed: {formatTimestamp(merge.timestamp)}
                  </p>
                </div>
                <div className="flex items-center space-x-3">
                  {getStatusBadge(merge.status)}
                </div>
              </div>

              {/* Document Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h4 className="font-medium text-green-800 mb-2">Kept Document</h4>
                  <div className="space-y-1">
                    <div className="flex items-start justify-between">
                      <span className="font-medium text-green-900">{merge.kept_title}</span>
                      {merge.kept_url && (
                        <a
                          href={merge.kept_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-green-600 hover:text-green-800"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      )}
                    </div>
                    <p className="text-sm text-green-700">ID: {merge.kept_page_id}</p>
                  </div>
                </div>

                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <h4 className="font-medium text-red-800 mb-2">Deleted Document</h4>
                  <div className="space-y-1">
                    <div className="flex items-start justify-between">
                      <span className="font-medium text-red-900">{merge.deleted_title}</span>
                      {merge.deleted_url && (
                        <a
                          href={merge.deleted_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-red-600 hover:text-red-800"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      )}
                    </div>
                    <p className="text-sm text-red-700">ID: {merge.deleted_page_id}</p>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-4 border-t border-border">
                <div className="flex items-center space-x-3">
                  {merge.status === 'completed' && (
                    <>
                      {selectedUndo === merge.id ? (
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-muted-foreground">
                            This will restore both documents. Continue?
                          </span>
                          <button
                            onClick={() => handleUndoMerge(merge.id)}
                            disabled={undoingId === merge.id}
                            className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700 disabled:opacity-50"
                          >
                            {undoingId === merge.id ? (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                              'Confirm Undo'
                            )}
                          </button>
                          <button
                            onClick={() => setSelectedUndo(null)}
                            className="px-3 py-1 bg-gray-300 text-gray-700 rounded text-sm hover:bg-gray-400"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setSelectedUndo(merge.id)}
                          className="flex items-center space-x-1 px-3 py-1 bg-orange-100 text-orange-800 rounded text-sm hover:bg-orange-200 transition-colors"
                        >
                          <Undo2 className="h-3 w-3" />
                          <span>Undo Merge</span>
                        </button>
                      )}
                    </>
                  )}
                  {merge.kept_url && (
                    <a
                      href={merge.kept_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center space-x-1 px-3 py-1 bg-blue-100 text-blue-800 rounded text-sm hover:bg-blue-200 transition-colors"
                    >
                      <ExternalLink className="h-3 w-3" />
                      <span>View Kept Page</span>
                    </a>
                  )}
                </div>

                <div className="text-xs text-muted-foreground">
                  Operation ID: {merge.id}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-card rounded-lg border border-border">
          <div className="text-center py-12 text-muted-foreground">
            <Undo2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
            <h3 className="text-lg font-medium text-foreground mb-2">No merge history available</h3>
            <p>No document merge operations have been performed yet.</p>
          </div>
        </div>
      )}

      {/* Info Panel */}
      {mergeHistory.length > 0 && (
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-blue-600 mt-1 flex-shrink-0" />
            <div>
              <h4 className="font-medium text-blue-800 mb-1">About Undo Operations</h4>
              <p className="text-sm text-blue-700">
                Undo operations restore both documents and automatically scan for duplicates. 
                The kept page is restored to its pre-merge version, and the deleted page is 
                recovered from the platform's trash.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
