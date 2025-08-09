
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';

const isProtectedRoute = createRouteMatcher([
  '/dashboard(.*)',
  '/onboarding(.*)',
  '/api/organization(.*)',
  '/api/onboarding(.*)',
]);

export default clerkMiddleware(async (auth, req) => {
  // Protect routes that require authentication
  if (isProtectedRoute(req)) {
    auth().protect();
  }

  // Auto-org context redirect for root/dashboard
  const { userId, orgId } = await auth();
  if (userId && !orgId && req.nextUrl.pathname === '/') {
    // Fetch user's orgs from Clerk
    const base = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ? 'https://api.clerk.dev' : 'https://api.clerk.com';
    const apiKey = process.env.CLERK_SECRET_KEY;
    if (!apiKey) return;
    const orgsRes = await fetch(`${base}/v1/users/${userId}/organization_memberships`, {
      headers: { 'Authorization': `Bearer ${apiKey}` }
    });
    if (orgsRes.ok) {
      const orgs = await orgsRes.json();
      if (orgs.length === 1) {
        const org = orgs[0].organization;
        // Redirect to org context (slug or id)
        return NextResponse.redirect(new URL(`/org-${org.id}`, req.url));
      }
    }
  }
});

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
};
