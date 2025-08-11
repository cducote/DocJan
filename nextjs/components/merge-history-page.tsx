'use client';

interface MergeHistoryPageProps {
  platform: 'confluence' | 'sharepoint';
}

export default function MergeHistoryPage({ platform }: MergeHistoryPageProps) {
  const platformName = platform === 'confluence' ? 'Confluence' : 'SharePoint';

  // Mock merge history data
  const mergeHistory = [
    {
      id: 1,
      date: '2024-01-15',
      sourceDoc: 'API Documentation v1',
      targetDoc: 'API Documentation v2',
      status: 'completed',
      mergedTitle: 'API Documentation (Merged)',
      similarity: 0.89
    },
    {
      id: 2,
      date: '2024-01-14',
      sourceDoc: 'User Guide',
      targetDoc: 'User Manual',
      status: 'completed',
      mergedTitle: 'User Guide and Manual',
      similarity: 0.82
    },
    {
      id: 3,
      date: '2024-01-13',
      sourceDoc: 'Project Requirements',
      targetDoc: 'Requirements Document',
      status: 'failed',
      error: 'Merge conflict detected',
      similarity: 0.76
    }
  ];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="px-2 py-1 bg-primary/10 text-primary rounded-full text-sm font-medium">Completed</span>;
      case 'failed':
        return <span className="px-2 py-1 bg-destructive/10 text-destructive rounded-full text-sm font-medium">Failed</span>;
      case 'pending':
        return <span className="px-2 py-1 bg-secondary/10 text-secondary-foreground rounded-full text-sm font-medium">Pending</span>;
      default:
        return <span className="px-2 py-1 bg-muted text-muted-foreground rounded-full text-sm font-medium">Unknown</span>;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">
          Merge History - {platformName}
        </h1>
        <p className="text-muted-foreground">
          View the history of document merges and their results
        </p>
      </div>

      <div className="mb-6 bg-muted border border-border rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-primary">
              {mergeHistory.filter(m => m.status === 'completed').length}
            </div>
            <div className="text-sm text-muted-foreground">Successful Merges</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-destructive">
              {mergeHistory.filter(m => m.status === 'failed').length}
            </div>
            <div className="text-sm text-muted-foreground">Failed Merges</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">
              {mergeHistory.length}
            </div>
            <div className="text-sm text-muted-foreground">Total Attempts</div>
          </div>
        </div>
      </div>

      <div className="bg-card rounded-lg shadow border border-border">
        <div className="px-6 py-4 border-b border-border">
          <h2 className="text-lg font-medium text-foreground">Merge History</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Documents Merged
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Result
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Similarity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-card divide-y divide-border">
              {mergeHistory.map((merge) => (
                <tr key={merge.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                    {new Date(merge.date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-sm text-foreground">
                    <div className="max-w-xs">
                      <div className="text-primary hover:text-primary/80 cursor-pointer">
                        {merge.sourceDoc}
                      </div>
                      <div className="text-muted-foreground text-xs">merged with</div>
                      <div className="text-primary hover:text-primary/80 cursor-pointer">
                        {merge.targetDoc}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-foreground">
                    {merge.status === 'completed' ? (
                      <div className="text-primary font-medium">{merge.mergedTitle}</div>
                    ) : merge.status === 'failed' ? (
                      <div className="text-destructive">{merge.error}</div>
                    ) : (
                      <div className="text-muted-foreground">-</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                    {Math.round(merge.similarity * 100)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(merge.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      {merge.status === 'completed' && (
                        <button className="text-primary hover:text-primary/80">
                          View
                        </button>
                      )}
                      {merge.status === 'failed' && (
                        <button className="text-primary hover:text-primary/80">
                          Retry
                        </button>
                      )}
                      <button className="text-muted-foreground hover:text-foreground">
                        Details
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {mergeHistory.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            No merge history available
          </div>
        )}
      </div>
    </div>
  );
}
