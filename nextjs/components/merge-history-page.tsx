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
        return <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">Completed</span>;
      case 'failed':
        return <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium">Failed</span>;
      case 'pending':
        return <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">Pending</span>;
      default:
        return <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-sm font-medium">Unknown</span>;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Merge History - {platformName}
        </h1>
        <p className="text-gray-600">
          View the history of document merges and their results
        </p>
      </div>

      <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-900">
              {mergeHistory.filter(m => m.status === 'completed').length}
            </div>
            <div className="text-sm text-blue-700">Successful Merges</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-900">
              {mergeHistory.filter(m => m.status === 'failed').length}
            </div>
            <div className="text-sm text-red-700">Failed Merges</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {mergeHistory.length}
            </div>
            <div className="text-sm text-gray-700">Total Attempts</div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Merge History</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Documents Merged
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Result
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Similarity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {mergeHistory.map((merge) => (
                <tr key={merge.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(merge.date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <div className="max-w-xs">
                      <div className="text-blue-600 hover:text-blue-800 cursor-pointer">
                        {merge.sourceDoc}
                      </div>
                      <div className="text-gray-500 text-xs">merged with</div>
                      <div className="text-blue-600 hover:text-blue-800 cursor-pointer">
                        {merge.targetDoc}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {merge.status === 'completed' ? (
                      <div className="text-green-600 font-medium">{merge.mergedTitle}</div>
                    ) : merge.status === 'failed' ? (
                      <div className="text-red-600">{merge.error}</div>
                    ) : (
                      <div className="text-gray-500">-</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {Math.round(merge.similarity * 100)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(merge.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      {merge.status === 'completed' && (
                        <button className="text-blue-600 hover:text-blue-900">
                          View
                        </button>
                      )}
                      {merge.status === 'failed' && (
                        <button className="text-green-600 hover:text-green-900">
                          Retry
                        </button>
                      )}
                      <button className="text-gray-600 hover:text-gray-900">
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
          <div className="text-center py-12 text-gray-500">
            No merge history available
          </div>
        )}
      </div>
    </div>
  );
}
