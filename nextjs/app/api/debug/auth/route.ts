import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';

export async function GET(request: NextRequest) {
  try {
    const authResult = await auth();
    
    return NextResponse.json({
      authenticated: !!authResult.userId,
      userId: authResult.userId,
      orgId: authResult.orgId,
      orgRole: authResult.orgRole,
      orgSlug: authResult.orgSlug,
      sessionId: authResult.sessionId,
    });
  } catch (error) {
    return NextResponse.json({
      error: error instanceof Error ? error.message : 'Unknown error',
      authenticated: false
    });
  }
}
