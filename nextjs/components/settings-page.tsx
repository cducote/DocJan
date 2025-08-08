'use client';

import { useState } from 'react';

interface SettingsPageProps {
  platform: 'confluence' | 'sharepoint';
}

export default function SettingsPage({ platform }: SettingsPageProps) {
  const [similarityThreshold, setSimilarityThreshold] = useState(0.65);
  const [isScanning, setIsScanning] = useState(false);
  const [scanResults, setScanResults] = useState<string | null>(null);

  const platformName = platform === 'confluence' ? 'Confluence' : 'SharePoint';

  const handleRunScan = async () => {
    setIsScanning(true);
    setScanResults(null);
    
    // Simulate scanning process
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    const foundPairs = Math.floor(Math.random() * 5) + 1;
    setScanResults(`✅ Scan completed successfully! Found ${foundPairs} potential duplicate pairs. Go to the Duplicates page to review them.`);
    setIsScanning(false);
  };

  const handleClearDatabase = async () => {
    if (confirm('⚠️ This will clear all document embeddings from ChromaDB. You\'ll need to reload your documents after this. Are you sure?')) {
      // Simulate clearing database
      await new Promise(resolve => setTimeout(resolve, 2000));
      alert('✅ ChromaDB cleared successfully! Now reload your documents from the Space Management section.');
    }
  };

  const handleCleanOrphans = async () => {
    if (confirm('⚠️ This will remove ChromaDB records that reference deleted pages. Continue?')) {
      // Simulate cleaning orphans
      await new Promise(resolve => setTimeout(resolve, 2000));
      const cleanedCount = Math.floor(Math.random() * 10);
      if (cleanedCount > 0) {
        alert(`✅ Cleanup completed! 🧹 Cleaned up ${cleanedCount} orphaned records`);
      } else {
        alert('✅ Cleanup completed! ✨ No orphaned records found - database is clean!');
      }
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Settings - {platformName}
        </h1>
        <p className="text-gray-600">
          Configure Concatly settings and perform maintenance operations
        </p>
      </div>

      {/* Duplicate Detection Settings */}
      <div className="bg-white rounded-lg shadow p-6 border border-gray-200 mb-8">
        <h2 className="text-xl font-semibold mb-4 text-gray-900">🔍 Duplicate Detection</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Similarity Threshold
            </label>
            <input
              type="range"
              min="0.50"
              max="0.95"
              step="0.05"
              value={similarityThreshold}
              onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>50%</span>
              <span className="font-medium">{Math.round(similarityThreshold * 100)}%</span>
              <span>95%</span>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              Documents with similarity above this threshold will be considered potential duplicates
            </p>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Current Threshold: {Math.round(similarityThreshold * 100)}%</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• <strong>50-60%:</strong> Very loose matching (many false positives)</li>
              <li>• <strong>65-75%:</strong> Balanced matching (recommended)</li>
              <li>• <strong>80-95%:</strong> Strict matching (may miss some duplicates)</li>
            </ul>
          </div>
        </div>

        <div className="mt-6">
          <button
            onClick={handleRunScan}
            disabled={isScanning}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isScanning ? '🔄 Scanning...' : '🔍 Run Duplicate Scan'}
          </button>
          
          {scanResults && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-800">{scanResults}</p>
            </div>
          )}
        </div>
      </div>

      {/* Space Management (Confluence only) */}
      {platform === 'confluence' && (
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200 mb-8">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">🏢 Space Management</h2>
          
          <div className="mb-4">
            <p className="text-gray-700">
              <strong>Currently monitoring 1 space:</strong> SD (Software Development)
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium text-gray-900 mb-3">Load Documents from Confluence</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Documents per space
                  </label>
                  <input
                    type="number"
                    min="10"
                    max="200"
                    defaultValue={50}
                    step="10"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Maximum number of documents to load from each space
                  </p>
                </div>
                
                <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors">
                  📥 Load Documents
                </button>
              </div>
            </div>

            <div>
              <h3 className="font-medium text-gray-900 mb-3">Space Statistics</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">3,295</div>
                  <div className="text-sm text-gray-600">Total Documents</div>
                </div>
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">3</div>
                  <div className="text-sm text-blue-600">Duplicate Pairs</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Basic Tools */}
      <div className="bg-white rounded-lg shadow p-6 border border-gray-200 mb-8">
        <h2 className="text-xl font-semibold mb-4 text-gray-900">🔧 Basic Tools</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h3 className="font-medium text-gray-900 mb-3">Database Status</h3>
            <div className="space-y-3">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">3,295</div>
                <div className="text-sm text-gray-600">Total Documents</div>
              </div>
              
              <button className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors">
                🔄 Refresh Space List
              </button>
            </div>
          </div>

          <div>
            <h3 className="font-medium text-gray-900 mb-3">🗃️ Database Maintenance</h3>
            <p className="text-gray-600 mb-4">Use these tools to fix common database issues:</p>
            
            <div className="space-y-3">
              <button
                onClick={handleClearDatabase}
                className="w-full bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 transition-colors"
              >
                🧹 Clear ChromaDB
              </button>
              
              <button
                onClick={handleCleanOrphans}
                className="w-full bg-yellow-600 text-white py-2 px-4 rounded-lg hover:bg-yellow-700 transition-colors"
              >
                🗑️ Clean Orphaned Records
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Database Cleanup Information */}
      <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
        <h3 className="font-medium text-gray-900 mb-3">Database Cleanup Options</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-gray-600">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Clear ChromaDB:</h4>
            <p className="mb-2">Complete reset - removes ALL documents</p>
            <h4 className="font-medium text-gray-900 mb-2">When to use:</h4>
            <ul className="list-disc list-inside space-y-1">
              <li>Starting fresh with new embeddings</li>
              <li>Major issues with duplicate detection</li>
              <li>After changing embedding models</li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Clean Orphaned Records:</h4>
            <p className="mb-2">Smart cleanup - only removes records for deleted pages</p>
            <h4 className="font-medium text-gray-900 mb-2">When to use:</h4>
            <ul className="list-disc list-inside space-y-1">
              <li>Seeing old/deleted pages in duplicate detection</li>
              <li>Document count higher than expected</li>
              <li>After deleting pages in Confluence</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
