import { NextRequest, NextResponse } from 'next/server';

import { auth } from '@clerk/nextjs/server';
import { UserService } from '@/lib/database/user-service';

export async function GET(request: NextRequest) {
  try {
    console.log('🔍 Credentials API called');
    
    const authResult = await auth();
    console.log('🔐 Auth result:', { 
      userId: authResult?.userId, 
      orgId: authResult?.orgId,
    });
    
    const { userId } = authResult;
    if (!userId) {
      console.log('❌ No user context found');
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      );
    }

    console.log('👤 User ID:', userId);
    // Get stored credentials using the user service
    console.log('📥 Calling UserService.getConfluenceCredentials...');
    const credentials = await UserService.getConfluenceCredentials(userId);
    console.log('📤 Credentials result:', credentials ? 'Found' : 'Not found');

    if (!credentials) {
      console.log('❌ No credentials found for user:', userId);
      return NextResponse.json(
        { error: 'No Confluence credentials found' },
        { status: 404 }
      );
    }

    console.log('✅ Returning credentials for user:', userId);
    return NextResponse.json({
      username: credentials.username,
      baseUrl: credentials.baseUrl,
      apiKey: credentials.apiKey,
    });

  } catch (error) {
    console.error('💥 Error retrieving user credentials:', error);
    
    if (error instanceof Error) {
      console.error('💥 Error stack:', error.stack);
      console.error('💥 Error name:', error.name);
      console.error('💥 Error message:', error.message);
      return NextResponse.json(
        { error: 'Internal server error', details: error.message }, 
        { status: 500 }
      );
    }
    
    return NextResponse.json(
      { error: 'Internal server error', details: 'Unknown error' }, 
      { status: 500 }
    );
  }
}
