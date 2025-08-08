import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { username, baseUrl, apiKey } = body;

    if (!username || !baseUrl || !apiKey) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
    }

    // Validate URL format
    try {
      new URL(baseUrl);
    } catch {
      return NextResponse.json({ error: 'Invalid base URL format' }, { status: 400 });
    }

    // Test the connection
    const result = await testConfluenceConnection({ username, baseUrl, apiKey });

    return NextResponse.json(result);

  } catch (error) {
    console.error('Error testing Confluence connection:', error);
    return NextResponse.json(
      { success: false, error: 'Connection test failed' },
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
}): Promise<{ success: boolean; error?: string; userInfo?: any; debug?: any }> {
  try {
    // Clean up base URL
    const cleanBaseUrl = baseUrl.replace(/\/+$/, ''); // Remove trailing slashes
    
    // Test connection by getting current user info (lightweight operation)
    const testUrl = `${cleanBaseUrl}/rest/api/user/current`;
    
    console.log(`Testing Confluence connection to: ${testUrl}`);
    console.log(`Username: ${username}`);
    console.log(`Base URL: ${cleanBaseUrl}`);
    
    const response = await fetch(testUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Basic ${Buffer.from(`${username}:${apiKey}`).toString('base64')}`,
        'Accept': 'application/json',
        'User-Agent': 'Concatly/1.0',
      },
      // Add timeout
      signal: AbortSignal.timeout(15000), // 15 second timeout
    });

    console.log(`Response status: ${response.status}`);
    console.log(`Response headers:`, Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`;
      let responseText = '';
      
      try {
        responseText = await response.text();
        console.log(`Response body:`, responseText);
      } catch (e) {
        console.log('Could not read response body:', e);
      }
      
      if (response.status === 401) {
        errorMessage = 'Invalid username or API token';
      } else if (response.status === 404) {
        errorMessage = 'Invalid base URL - Confluence API not found';
      } else if (response.status === 403) {
        errorMessage = 'Access denied - check permissions';
      } else if (response.status >= 500) {
        errorMessage = `Server error (${response.status}) - Confluence instance may be down`;
      }
      
      return { 
        success: false, 
        error: errorMessage,
        debug: {
          status: response.status,
          statusText: response.statusText,
          responseBody: responseText,
          url: testUrl,
        }
      };
    }

    const userInfo = await response.json();
    console.log(`User info received:`, userInfo);
    
    return { 
      success: true, 
      userInfo: {
        displayName: userInfo.displayName,
        emailAddress: userInfo.emailAddress,
      }
    };
  } catch (error) {
    console.error('Confluence connection test failed:', error);
    
    let errorMessage = 'Connection test failed';
    let debugInfo: any = {};
    
    if (error instanceof Error) {
      console.log(`Error name: ${error.name}`);
      console.log(`Error message: ${error.message}`);
      console.log(`Error stack:`, error.stack);
      
      debugInfo = {
        name: error.name,
        message: error.message,
        stack: error.stack,
      };
      
      if (error.name === 'TimeoutError') {
        errorMessage = 'Connection timeout (15s) - check your base URL';
      } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
        errorMessage = 'Network error - cannot reach Confluence server. Check your base URL format.';
      } else if (error.message.includes('ENOTFOUND')) {
        errorMessage = 'DNS lookup failed - check your base URL domain';
      } else if (error.message.includes('ECONNREFUSED')) {
        errorMessage = 'Connection refused - server may be down or URL incorrect';
      } else if (error.message.includes('certificate')) {
        errorMessage = 'SSL certificate error - check if your Confluence uses HTTPS correctly';
      } else {
        errorMessage = error.message;
      }
    }
    
    return { 
      success: false, 
      error: errorMessage,
      debug: debugInfo,
    };
  }
}
