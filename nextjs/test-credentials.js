// Quick test script to debug credentials API
// Run with: node test-credentials.mjs

async function testCredentialsAPI() {
  const fetch = (await import('node-fetch')).default;
  console.log('🧪 Testing Credentials API...\n');
  
  try {
    // Test the credentials endpoint
    const response = await fetch('http://localhost:3000/api/organization/credentials', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // Note: This won't work without proper Clerk session cookies
        // But it will help us see what error we get
      }
    });

    console.log('📊 Response Status:', response.status);
    console.log('📊 Response Headers:', Object.fromEntries(response.headers.entries()));
    
    const responseText = await response.text();
    console.log('📊 Response Body:', responseText);
    
    if (response.ok) {
      console.log('✅ API endpoint is working!');
      try {
        const data = JSON.parse(responseText);
        console.log('📋 Parsed Data:', data);
      } catch (e) {
        console.log('⚠️  Response is not valid JSON');
      }
    } else {
      console.log('❌ API endpoint returned error');
      if (response.status === 401) {
        console.log('🔐 Expected: Need authentication (Clerk session)');
      } else if (response.status === 404) {
        console.log('🔍 Expected: No credentials found');
      } else {
        console.log('💥 Unexpected error');
      }
    }
    
  } catch (error) {
    console.error('💥 Network or other error:', error.message);
    
    if (error.code === 'ECONNREFUSED') {
      console.log('🚨 Next.js server is not running! Start it with: npm run dev');
    }
  }
}

async function testOrganizationService() {
  console.log('\n🧪 Testing Organization Service directly...\n');
  
  try {
    // Test if we can import the service
    const { OrganizationService } = await import('./lib/database/organization-service.js');
    console.log('✅ OrganizationService imported successfully');
    
    // Test mock orgId
    const mockOrgId = 'test-org-123';
    
    console.log(`🔍 Testing with mock org ID: ${mockOrgId}`);
    
    // This will fail because we don't have Clerk context, but we can see the error
    const settings = await OrganizationService.getOrgSettings(mockOrgId);
    console.log('📋 Settings:', settings);
    
  } catch (error) {
    console.error('💥 Service test error:', error.message);
    console.log('🔐 Expected: Clerk authentication error');
  }
}

// Run tests
async function runTests() {
  await testCredentialsAPI();
  // await testOrganizationService(); // Comment out since it requires TS compilation
  
  console.log('\n✨ Test complete!');
  console.log('\n💡 Next steps:');
  console.log('1. Make sure Next.js dev server is running: npm run dev');
  console.log('2. Check browser network tab when clicking "Start Data Ingestion"');
  console.log('3. Look for specific error messages in browser console');
}

runTests();
