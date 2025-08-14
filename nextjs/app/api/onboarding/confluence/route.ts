import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';
import { UserService } from '@/lib/database/user-service';
import { OrganizationService } from '@/lib/database/organization-service';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { username, baseUrl, apiKey, orgId } = body;

    console.log('Received onboarding request:', { username, baseUrl, apiKeyLength: apiKey?.length, orgId });

    // Get current user
    const { userId, orgId: authOrgId } = await auth();
    if (!userId) {
      return NextResponse.json(
        { error: 'Authentication required' }, 
        { status: 401 }
      );
    }

    // Use orgId from auth context if not provided in body
    const organizationId = orgId || authOrgId;
    if (!organizationId) {
      return NextResponse.json(
        { error: 'No organization context found' }, 
        { status: 400 }
      );
    }

    // Validate required fields
    if (!username || !baseUrl || !apiKey) {
      console.log('Missing required fields:', { username: !!username, baseUrl: !!baseUrl, apiKey: !!apiKey });
      return NextResponse.json(
        { error: 'Missing required fields' }, 
        { status: 400 }
      );
    }

    // Validate URL format
    try {
      new URL(baseUrl);
    } catch {
      console.log('Invalid URL format:', baseUrl);
      return NextResponse.json(
        { error: 'Invalid base URL format' }, 
        { status: 400 }
      );
    }

    // Save configuration to user's private metadata
    console.log('Saving user credentials...');
    const userSuccess = await UserService.storeConfluenceCredentials(userId, {
      username,
      baseUrl,
      apiKey,
    });

    console.log('User save result:', userSuccess);

    if (!userSuccess) {
      return NextResponse.json(
        { error: 'Failed to save user credentials' }, 
        { status: 500 }
      );
    }

    // Complete organization onboarding
    console.log('Completing organization onboarding...');
    const orgResult = await OrganizationService.completeConfluenceOnboarding(organizationId, {
      username,
      baseUrl,
      apiKey,
    });

    console.log('Organization onboarding result:', orgResult);

    if (!orgResult.success) {
      console.error('Organization onboarding failed:', orgResult);
      return NextResponse.json(
        { error: 'Failed to complete organization onboarding' }, 
        { status: 500 }
      );
    }

    console.log('✅ Onboarding completed successfully, sending response...');
    return NextResponse.json({
      success: true,
      message: 'Confluence onboarding completed successfully',
    });

  } catch (error) {
    console.error('Error in confluence onboarding API:', error);
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    );
  }
}

/**
 * Test Confluence connection with provided credentials
 */
async function testConfluenceConnection({
  username,
  baseUrl,
  apiKey,
}: {
  username: string;
  baseUrl: string;
  apiKey: string;
}): Promise<{ success: boolean; error?: string }> {
  try {
    // Clean up base URL
    const cleanBaseUrl = baseUrl.replace(/\/+$/, ''); // Remove trailing slashes
    
    // Test connection by getting user info
    const testUrl = `${cleanBaseUrl}/rest/api/user?username=${encodeURIComponent(username)}`;
    
    const response = await fetch(testUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Basic ${Buffer.from(`${username}:${apiKey}`).toString('base64')}`,
        'Accept': 'application/json',
      },
      // Add timeout
      signal: AbortSignal.timeout(10000), // 10 second timeout
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`;
      
      if (response.status === 401) {
        errorMessage = 'Invalid username or API token';
      } else if (response.status === 404) {
        errorMessage = 'Invalid base URL or user not found';
      } else if (response.status === 403) {
        errorMessage = 'Access denied - check permissions';
      }
      
      return { success: false, error: errorMessage };
    }

    return { success: true };
  } catch (error) {
    console.error('Confluence connection test failed:', error);
    
    if (error instanceof Error) {
      if (error.name === 'TimeoutError') {
        return { success: false, error: 'Connection timeout - check your base URL' };
      }
      return { success: false, error: error.message };
    }
    
    return { success: false, error: 'Connection test failed' };
  }
}
