'use client';

import { useAuth, useOrganization, useClerk } from '@clerk/nextjs';
import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Sidebar from '../components/sidebar';
import DashboardContent from '../components/dashboard-content';
import SearchPage from '../components/search-page';
import ContentReportPage from '../components/duplicates-page';
import SpacesPage from '../components/spaces-page';
import MergeHistoryPage from '../components/merge-history-page';
import SettingsPage from '../components/settings-page';
import { ThemeToggle } from '../components/theme-toggle';
import { Header } from '../components/header';

export default function Home() {
  const { isSignedIn, isLoaded: authLoaded } = useAuth();
  const { organization, isLoaded: orgLoaded } = useOrganization();
  const { signOut } = useClerk();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [currentPage, setCurrentPage] = useState('dashboard');
  const [platform, setPlatform] = useState<'confluence' | 'sharepoint'>('confluence');
  const [shouldRefresh, setShouldRefresh] = useState(false);

  // Handle URL parameters for page navigation and refresh
  useEffect(() => {
    const pageParam = searchParams.get('page');
    const refreshParam = searchParams.get('refresh');
    
    if (pageParam) {
      setCurrentPage(pageParam);
      if (refreshParam === 'true') {
        setShouldRefresh(true);
      }
      // Clear URL parameters after setting state
      const url = new URL(window.location.href);
      url.searchParams.delete('page');
      url.searchParams.delete('refresh');
      window.history.replaceState({}, '', url.toString());
    }
  }, [searchParams]);

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
        return <ContentReportPage platform={platform} shouldRefresh={shouldRefresh} onRefreshComplete={() => setShouldRefresh(false)} />;
      case 'content-report':
        return <ContentReportPage platform={platform} shouldRefresh={shouldRefresh} onRefreshComplete={() => setShouldRefresh(false)} />;
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
        <Header />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          {renderPageContent()}
        </main>
      </div>
    </div>
  );
}
