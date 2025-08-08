import { NextRequest, NextResponse } from 'next/server';
import { OrganizationService } from '@/lib/database/organization-service';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { orgId, username, baseUrl, apiKey } = body;

    console.log('Received onboarding request:', { orgId, username, baseUrl, apiKeyLength: apiKey?.length });

    // Validate required fields
    if (!orgId || !username || !baseUrl || !apiKey) {
      console.log('Missing required fields:', { orgId: !!orgId, username: !!username, baseUrl: !!baseUrl, apiKey: !!apiKey });
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

    // Save configuration (skip connection test since we already validated it)
    console.log('Saving configuration...');
    const result = await OrganizationService.completeConfluenceOnboarding(orgId, {
      username,
      baseUrl,
      apiKey,
    });

    console.log('Save result:', result);

    if (!result.success) {
      return NextResponse.json(
        { error: 'Failed to save configuration' }, 
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      message: 'Confluence configuration saved successfully',
      secretId: result.secretId,
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
