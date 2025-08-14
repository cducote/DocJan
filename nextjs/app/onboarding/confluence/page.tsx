'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useUser, useOrganization } from '@clerk/nextjs';

export default function ConfluenceSetupPage() {
  const [formData, setFormData] = useState({
    username: '',
    baseUrl: '',
    apiKey: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<{
    tested: boolean;
    success: boolean;
    error?: string;
    userInfo?: any;
    debug?: any;
  }>({ tested: false, success: false });
  const [error, setError] = useState('');
  const router = useRouter();
  const { user } = useUser();
  const { organization } = useOrganization();

  // Pre-fill username with user's email
  useState(() => {
    if (user?.emailAddresses[0]?.emailAddress) {
      setFormData(prev => ({
        ...prev,
        username: user.emailAddresses[0].emailAddress,
      }));
    }
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    
    // Reset connection status when form data changes
    if (connectionStatus.tested) {
      setConnectionStatus({ tested: false, success: false });
    }
    setError('');
  };

  const validateForm = () => {
    if (!formData.username.trim()) {
      setError('Username is required');
      return false;
    }
    if (!formData.baseUrl.trim()) {
      setError('Base URL is required');
      return false;
    }
    if (!formData.apiKey.trim()) {
      setError('API Token is required');
      return false;
    }
    
    // Validate URL format
    try {
      new URL(formData.baseUrl);
    } catch {
      setError('Please enter a valid URL');
      return false;
    }

    return true;
  };

  const testConnection = async () => {
    setError('');
    
    if (!validateForm()) {
      return;
    }

    setIsTesting(true);
    setConnectionStatus({ tested: false, success: false });

    try {
      const response = await fetch('/api/onboarding/confluence/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const result = await response.json();

      if (result.success) {
        setConnectionStatus({
          tested: true,
          success: true,
          userInfo: result.userInfo,
        });
      } else {
        setConnectionStatus({
          tested: true,
          success: false,
          error: result.error,
          debug: result.debug,
        });
        setError(result.error || 'Connection test failed');
      }
    } catch (err) {
      const errorMessage = 'Network error - please check your connection';
      setConnectionStatus({
        tested: true,
        success: false,
        error: errorMessage,
      });
      setError(errorMessage);
    } finally {
      setIsTesting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!connectionStatus.tested || !connectionStatus.success) {
      setError('Please test your connection first');
      return;
    }

    if (!organization?.id) {
      setError('No organization context found');
      return;
    }

    setIsLoading(true);

    try {
      console.log('🚀 Starting onboarding API call...');
      const response = await fetch('/api/onboarding/confluence', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          orgId: organization.id,
          ...formData,
        }),
      });

      console.log('📡 API response status:', response.status);
      const result = await response.json();
      console.log('📦 API response data:', result);

      if (!response.ok) {
        console.error('❌ API error:', result);
        throw new Error(result.error || 'Failed to save configuration');
      }

      console.log('✅ Onboarding successful, redirecting...');
      // Redirect to dashboard on success
      router.push('/');
    } catch (err) {
      console.error('💥 Frontend error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
          <h2 className="text-3xl font-bold text-gray-900">Configure Confluence</h2>
          <p className="mt-2 text-sm text-gray-600">
            Enter your Confluence credentials to connect your knowledge base
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="rounded-md bg-red-50 p-4">
                <div className="flex">
                  <svg className="h-5 w-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              </div>
            )}

            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                Confluence Username/Email
              </label>
              <div className="mt-1">
                <input
                  id="username"
                  name="username"
                  type="email"
                  autoComplete="email"
                  required
                  value={formData.username}
                  onChange={handleInputChange}
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="your-email@company.com"
                />
              </div>
              <p className="mt-1 text-xs text-gray-500">
                The email address you use to log into Confluence
              </p>
            </div>

            <div>
              <label htmlFor="baseUrl" className="block text-sm font-medium text-gray-700">
                Confluence Base URL
              </label>
              <div className="mt-1">
                <input
                  id="baseUrl"
                  name="baseUrl"
                  type="url"
                  required
                  value={formData.baseUrl}
                  onChange={handleInputChange}
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="https://your-company.atlassian.net/wiki"
                />
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Your Confluence instance URL (e.g., https://company.atlassian.net/wiki)
              </p>
            </div>

            <div>
              <label htmlFor="apiKey" className="block text-sm font-medium text-gray-700">
                Confluence API Token
              </label>
              <div className="mt-1">
                <input
                  id="apiKey"
                  name="apiKey"
                  type="password"
                  required
                  value={formData.apiKey}
                  onChange={handleInputChange}
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Your Confluence API token"
                />
              </div>
              <div className="mt-1 text-xs text-gray-500">
                <p>Create an API token at:{' '}
                  <a 
                    href="https://id.atlassian.com/manage-profile/security/api-tokens" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-500"
                  >
                    Atlassian Account Settings
                  </a>
                </p>
              </div>
            </div>

            {/* Test Connection Button */}
            <div>
              <button
                type="button"
                onClick={testConnection}
                disabled={isTesting || !formData.username || !formData.baseUrl || !formData.apiKey}
                className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isTesting ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Testing Connection...
                  </>
                ) : (
                  'Test Connection'
                )}
              </button>
            </div>

            {/* Connection Status */}
            {connectionStatus.tested && (
              <div className={`rounded-md p-4 ${
                connectionStatus.success 
                  ? 'bg-green-50 border border-green-200' 
                  : 'bg-red-50 border border-red-200'
              }`}>
                <div className="flex">
                  {connectionStatus.success ? (
                    <svg className="h-5 w-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  )}
                  <div className="text-sm">
                    {connectionStatus.success ? (
                      <div>
                        <p className="text-green-800 font-medium">Connection Successful!</p>
                        {connectionStatus.userInfo && (
                          <p className="text-green-700 mt-1">
                            Connected as: {connectionStatus.userInfo.displayName} ({connectionStatus.userInfo.emailAddress})
                          </p>
                        )}
                      </div>
                    ) : (
                      <div>
                        <p className="text-red-800 font-medium">Connection Failed</p>
                        <p className="text-red-700 mt-1">{connectionStatus.error}</p>
                        {connectionStatus.debug && (
                          <details className="mt-2">
                            <summary className="text-red-600 text-xs cursor-pointer hover:text-red-500">
                              Show debug info
                            </summary>
                            <pre className="mt-1 text-xs text-red-600 bg-red-100 p-2 rounded overflow-auto max-h-32">
                              {JSON.stringify(connectionStatus.debug, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <div className="flex">
                <svg className="h-5 w-5 text-blue-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                <div className="text-sm">
                  <p className="text-blue-800 font-medium">Security Note</p>
                  <p className="text-blue-700 mt-1">
                    Your API credentials are encrypted and securely stored. We use them only to access your Confluence content for duplicate detection.
                  </p>
                </div>
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading || !connectionStatus.success}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Setting up...
                  </>
                ) : connectionStatus.success ? (
                  'Complete Setup'
                ) : (
                  'Test Connection First'
                )}
              </button>
              {!connectionStatus.success && (
                <p className="mt-2 text-xs text-gray-500 text-center">
                  Please test your connection before completing setup
                </p>
              )}
            </div>

            <div className="text-center">
              <button
                type="button"
                onClick={() => router.back()}
                className="text-sm text-gray-600 hover:text-gray-500"
              >
                ← Back to knowledge base selection
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
