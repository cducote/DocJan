'use client';

interface SearchPageProps {
  platform: 'confluence' | 'sharepoint';
}

export default function SearchPage({ platform }: SearchPageProps) {
  const platformName = platform === 'confluence' ? 'Confluence' : 'SharePoint';

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">
          Search - {platformName}
        </h1>
        <p className="text-muted-foreground">
          Search for {platformName} documents and discover potential duplicates
        </p>
      </div>

      <div className="bg-card rounded-lg shadow p-6 border border-border">
        <div className="mb-6">
          <label htmlFor="search" className="block text-sm font-medium text-foreground mb-2">
            Search Query
          </label>
          <input
            type="text"
            id="search"
            placeholder={`Search ${platformName} documents...`}
            className="w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-foreground placeholder:text-muted-foreground"
          />
        </div>

        <div className="flex space-x-4 mb-6">
          <button className="bg-primary text-primary-foreground px-6 py-2 rounded-lg hover:bg-primary/90 transition-colors">
            Search
          </button>
          <button className="bg-secondary text-secondary-foreground px-6 py-2 rounded-lg hover:bg-secondary/80 transition-colors">
            Clear
          </button>
        </div>

        <div className="border-t border-border pt-6">
          <h3 className="text-lg font-medium text-foreground mb-4">Search Results</h3>
          <div className="text-center py-12 text-muted-foreground">
            Enter a search query to find documents
          </div>
        </div>
      </div>
    </div>
  );
}
