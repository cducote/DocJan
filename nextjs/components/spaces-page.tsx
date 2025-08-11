'use client';

interface SpacesPageProps {
  platform: 'confluence' | 'sharepoint';
}

export default function SpacesPage({ platform }: SpacesPageProps) {
  const platformName = platform === 'confluence' ? 'Confluence' : 'SharePoint';

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">
          Spaces - {platformName}
        </h1>
        <p className="text-muted-foreground">
          Space management functionality coming soon
        </p>
      </div>

      <div className="bg-card rounded-lg shadow p-8 border border-border text-center">
        <div className="max-w-md mx-auto">
          <div className="text-muted-foreground mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-foreground mb-2">Spaces Management</h3>
          <p className="text-muted-foreground">
            This section will allow you to select and manage which {platformName} spaces to monitor for duplicate detection.
          </p>
        </div>
      </div>
    </div>
  );
}
