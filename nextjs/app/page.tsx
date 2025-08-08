'use client';

import { useAuth, useOrganization, useClerk } from '@clerk/nextjs';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '../components/sidebar';
import DashboardContent from '../components/dashboard-content';
import SearchPage from '../components/search-page';
import ContentReportPage from '../components/duplicates-page';
import SpacesPage from '../components/spaces-page';
import MergeHistoryPage from '../components/merge-history-page';
import SettingsPage from '../components/settings-page';
import { ThemeToggle } from '../components/theme-toggle';

export default function Home() {
  const { isSignedIn, isLoaded: authLoaded } = useAuth();
  const { organization, isLoaded: orgLoaded } = useOrganization();
  const { signOut } = useClerk();
  const router = useRouter();

  const [currentPage, setCurrentPage] = useState('dashboard');
  const [platform, setPlatform] = useState<'confluence' | 'sharepoint'>('confluence');

  useEffect(() => {
    if (authLoaded && !isSignedIn) {
      router.push('/sign-in');
      return;
    }

    if (authLoaded && isSignedIn && orgLoaded && !organization) {
      router.push('/organization-selection');
      return;
    }

    if (authLoaded && isSignedIn && orgLoaded && organization) {
      const onboardingComplete = organization.publicMetadata?.onboardingComplete;
      if (!onboardingComplete) {
        router.push('/onboarding');
        return;
      }
    }
  }, [authLoaded, isSignedIn, orgLoaded, organization, router]);

  if (!authLoaded || !orgLoaded) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isSignedIn || !organization) {
    return null; // Will redirect via useEffect
  }

  const handleSignOut = async () => {
    await signOut();
    router.push('/sign-in');
  };

  const renderPageContent = () => {
    switch (currentPage) {
      case 'dashboard':
        return <DashboardContent platform={platform} onPageChange={setCurrentPage} />;
      case 'search':
        return <SearchPage platform={platform} />;
      case 'duplicates':
        return <ContentReportPage platform={platform} />;
      case 'spaces':
        return platform === 'confluence' ? <SpacesPage platform={platform} /> : <DashboardContent platform={platform} onPageChange={setCurrentPage} />;
      case 'merge_history':
        return <MergeHistoryPage platform={platform} />;
      case 'settings':
        return <SettingsPage platform={platform} />;
      default:
        return <DashboardContent platform={platform} onPageChange={setCurrentPage} />;
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <Sidebar
        currentPage={currentPage}
        platform={platform}
        onPageChange={setCurrentPage}
        onPlatformChange={setPlatform}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-card border-b border-border px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-foreground">Concatly</h1>
              <p className="text-sm text-muted-foreground">
                Organization: {organization.name}
              </p>
            </div>
            
            <div className="flex items-center gap-4">
              <ThemeToggle />
              <button
                onClick={handleSignOut}
                className="bg-destructive text-destructive-foreground px-4 py-2 rounded-lg hover:bg-destructive/90 transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          {renderPageContent()}
        </main>
      </div>
    </div>
  );
}
