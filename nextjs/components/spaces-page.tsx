'use client';

interface SpacesPageProps {
  platform: 'confluence' | 'sharepoint';
}

export default function SpacesPage({ platform }: SpacesPageProps) {
  // Mock spaces data
  const availableSpaces = [
    { key: 'SD', name: 'Software Development', description: 'Development team documentation' },
    { key: 'HR', name: 'Human Resources', description: 'HR policies and procedures' },
    { key: 'MARKETING', name: 'Marketing', description: 'Marketing campaigns and materials' },
    { key: 'SALES', name: 'Sales', description: 'Sales processes and training' },
    { key: 'FINANCE', name: 'Finance', description: 'Financial reports and procedures' }
  ];

  const selectedSpaces = ['SD']; // Default selected space

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Spaces - Confluence
        </h1>
        <p className="text-gray-600">
          Manage which Confluence spaces to monitor for duplicate detection
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Available Spaces */}
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">Available Spaces</h2>
          <p className="text-gray-600 mb-4">
            Select spaces to include in duplicate detection
          </p>

          <div className="space-y-3">
            {availableSpaces.map((space) => (
              <div key={space.key} className="flex items-center p-3 border border-gray-200 rounded-lg">
                <input
                  type="checkbox"
                  id={space.key}
                  checked={selectedSpaces.includes(space.key)}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                />
                <div className="ml-3 flex-1">
                  <label htmlFor={space.key} className="font-medium text-gray-900 cursor-pointer">
                    {space.name} ({space.key})
                  </label>
                  <p className="text-sm text-gray-500">{space.description}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 flex space-x-4">
            <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
              Save Selection
            </button>
            <button className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors">
              Refresh Spaces
            </button>
          </div>
        </div>

        {/* Selected Spaces Summary */}
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">Selected Spaces</h2>
          <p className="text-gray-600 mb-4">
            Currently monitoring {selectedSpaces.length} space{selectedSpaces.length !== 1 ? 's' : ''}
          </p>

          <div className="space-y-3 mb-6">
            {selectedSpaces.map((spaceKey) => {
              const space = availableSpaces.find(s => s.key === spaceKey);
              return space ? (
                <div key={spaceKey} className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="font-medium text-blue-900">
                    {space.name} ({space.key})
                  </div>
                  <div className="text-sm text-blue-700">{space.description}</div>
                </div>
              ) : null;
            })}
          </div>

          <div className="border-t pt-4">
            <h3 className="font-medium text-gray-900 mb-3">Space Statistics</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">3,295</div>
                <div className="text-sm text-gray-600">Total Pages</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">3</div>
                <div className="text-sm text-gray-600">Duplicate Pairs</div>
              </div>
            </div>
          </div>

          <div className="mt-6">
            <button className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors">
              Load Documents from Selected Spaces
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
