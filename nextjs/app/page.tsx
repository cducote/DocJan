'use client';

import { useAuth, useOrganization } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function HomePage() {
  const { isLoaded: authLoaded, userId } = useAuth();
  const { organization, isLoaded: orgLoaded } = useOrganization();
  const router = useRouter();
  const [isRedirecting, setIsRedirecting] = useState(false);

  useEffect(() => {
    if (!authLoaded || !orgLoaded || isRedirecting) return;

    // If not authenticated, redirect to sign in
    if (!userId) {
      setIsRedirecting(true);
      router.push('/sign-in');
      return;
    }

    // If no organization selected, redirect to org selection
    if (!organization) {
      setIsRedirecting(true);
      router.push('/organization-selection');
      return;
    }

    // Check if organization needs onboarding
    if (organization.publicMetadata?.onboardingComplete !== true) {
      setIsRedirecting(true);
      router.push('/onboarding');
      return;
    }
  }, [authLoaded, orgLoaded, userId, organization, router, isRedirecting]);

  if (!authLoaded || !orgLoaded || isRedirecting) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!userId) {
    return null; // Will redirect to sign-in
  }

  if (!organization) {
    return null; // Will redirect to org selection
  }

  if (organization.publicMetadata?.onboardingComplete !== true) {
    return null; // Will redirect to onboarding
  }

  return (
    <div className="flex h-screen bg-gray-100">
      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 p-6">
          <div className="container mx-auto px-6 py-8">
            <h1 className="text-3xl font-semibold text-gray-800 mb-6">
              Welcome to Concatly, {organization.name}!
            </h1>
            <p className="text-gray-600">
              Organization onboarding is complete. You can now use the full application.
            </p>
          </div>
        </main>
      </div>
    </div>
  );
}
