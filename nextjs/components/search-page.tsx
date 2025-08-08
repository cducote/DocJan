'use client';

interface SearchPageProps {
  platform: 'confluence' | 'sharepoint';
}

export default function SearchPage({ platform }: SearchPageProps) {
  const platformName = platform === 'confluence' ? 'Confluence' : 'SharePoint';

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Search - {platformName}
        </h1>
        <p className="text-gray-600">
          Search for {platformName} documents and discover potential duplicates
        </p>
      </div>

      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <div className="mb-6">
          <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
            Search Query
          </label>
          <input
            type="text"
            id="search"
            placeholder={`Search ${platformName} documents...`}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div className="flex space-x-4 mb-6">
          <button className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
            Search
          </button>
          <button className="bg-gray-200 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-300 transition-colors">
            Clear
          </button>
        </div>

        <div className="border-t pt-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Search Results</h3>
          <div className="text-center py-12 text-gray-500">
            Enter a search query to find documents
          </div>
        </div>
      </div>
    </div>
  );
}
