'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useUser } from '@clerk/nextjs';

export default function OnboardingPage() {
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<'confluence' | 'sharepoint' | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const { user } = useUser();

  const handleKnowledgeBaseSelection = (kb: 'confluence' | 'sharepoint') => {
    setSelectedKnowledgeBase(kb);
  };

  const handleContinue = () => {
    if (selectedKnowledgeBase === 'confluence') {
      router.push('/onboarding/confluence');
    } else if (selectedKnowledgeBase === 'sharepoint') {
      router.push('/onboarding/sharepoint');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900">Welcome to Concatly</h2>
          <p className="mt-2 text-sm text-gray-600">
            Hi {user?.firstName || user?.emailAddresses[0]?.emailAddress}! Let's set up your knowledge base.
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Choose your knowledge base
              </h3>
              <p className="text-sm text-gray-600 mb-6">
                Select where your documents are stored. We'll help you connect and start finding duplicates.
              </p>
            </div>

            <div className="space-y-4">
              {/* Confluence Option */}
              <div
                className={`relative rounded-lg border p-4 cursor-pointer transition-all ${
                  selectedKnowledgeBase === 'confluence'
                    ? 'border-blue-500 ring-2 ring-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onClick={() => handleKnowledgeBaseSelection('confluence')}
              >
                <div className="flex items-center">
                  <div className="flex items-center h-5">
                    <input
                      type="radio"
                      name="knowledgeBase"
                      value="confluence"
                      checked={selectedKnowledgeBase === 'confluence'}
                      onChange={() => handleKnowledgeBaseSelection('confluence')}
                      className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                    />
                  </div>
                  <div className="ml-3 flex-1">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center mr-3">
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                        </svg>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">Confluence</h4>
                        <p className="text-sm text-gray-500">Atlassian Confluence wiki and documentation</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* SharePoint Option */}
              <div
                className={`relative rounded-lg border p-4 cursor-pointer transition-all ${
                  selectedKnowledgeBase === 'sharepoint'
                    ? 'border-blue-500 ring-2 ring-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onClick={() => handleKnowledgeBaseSelection('sharepoint')}
              >
                <div className="flex items-center">
                  <div className="flex items-center h-5">
                    <input
                      type="radio"
                      name="knowledgeBase"
                      value="sharepoint"
                      checked={selectedKnowledgeBase === 'sharepoint'}
                      onChange={() => handleKnowledgeBaseSelection('sharepoint')}
                      className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                    />
                  </div>
                  <div className="ml-3 flex-1">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-green-600 rounded flex items-center justify-center mr-3">
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                        </svg>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">SharePoint</h4>
                        <p className="text-sm text-gray-500">Microsoft SharePoint document library</p>
                        <p className="text-xs text-orange-600 mt-1">Coming soon</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-4">
              <button
                type="button"
                onClick={handleContinue}
                disabled={!selectedKnowledgeBase || selectedKnowledgeBase === 'sharepoint' || isLoading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Processing...' : 'Continue Setup'}
              </button>
            </div>

            <div className="text-center">
              <p className="text-xs text-gray-500">
                Don't worry, you can change this later in settings
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
