#!/usr/bin/env python3
"""
Firecrawl API Discovery Script

This script tests the actual Firecrawl API to understand:
- Available endpoints
- Real response structures
- Error handling behavior
- Rate limiting
- Authentication requirements

Used to align our implementation and tests with reality.
"""

import os
import sys
import asyncio
import json
import time
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('FIRECRAWL_API_KEY')
BASE_URL = os.getenv('FIRECRAWL_BASE_URL', 'https://api.firecrawl.dev')

if not API_KEY:
    print("❌ FIRECRAWL_API_KEY not found in environment")
    sys.exit(1)

print(f"🔍 Discovering Firecrawl API capabilities")
print(f"📡 Base URL: {BASE_URL}")
print(f"🔑 API Key: {API_KEY[:10]}...")
print("=" * 60)


async def test_endpoint(client: httpx.AsyncClient, method: str, endpoint: str, 
                       payload: dict = None, description: str = ""):
    """Test a specific API endpoint and return results."""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    print(f"\n🧪 Testing {method} {endpoint}")
    if description:
        print(f"   {description}")
    
    try:
        start_time = time.time()
        
        if method.upper() == "GET":
            response = await client.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            response = await client.post(url, headers=headers, json=payload, timeout=30)
        else:
            print(f"   ❌ Unsupported method: {method}")
            return None
        
        response_time = (time.time() - start_time) * 1000
        
        print(f"   📊 Status: {response.status_code}")
        print(f"   ⏱️  Response time: {response_time:.0f}ms")
        
        # Try to parse JSON response
        try:
            response_data = response.json()
            print(f"   📄 Response structure:")
            print(f"      Keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
            
            # Show first few lines of response for inspection
            response_str = json.dumps(response_data, indent=2)
            lines = response_str.split('\n')[:10]
            for line in lines:
                print(f"      {line}")
            if len(response_str.split('\n')) > 10:
                print(f"      ... (truncated)")
                
            return {
                "status_code": response.status_code,
                "response_time_ms": response_time,
                "data": response_data,
                "success": response.is_success
            }
            
        except json.JSONDecodeError:
            print(f"   📄 Response (text): {response.text[:200]}...")
            return {
                "status_code": response.status_code,
                "response_time_ms": response_time,
                "text": response.text,
                "success": response.is_success
            }
            
    except httpx.TimeoutException:
        print(f"   ⏰ Timeout after 30s")
        return {"error": "timeout"}
    except httpx.ConnectError as e:
        print(f"   🔌 Connection error: {e}")
        return {"error": "connection_error", "details": str(e)}
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return {"error": "unexpected", "details": str(e)}


async def discover_firecrawl_api():
    """Discover Firecrawl API capabilities."""
    
    async with httpx.AsyncClient() as client:
        results = {}
        
        # Test 1: Credits endpoint
        print("\n" + "="*60)
        print("🏦 TESTING CREDITS ENDPOINT")
        print("="*60)
        
        credits_result = await test_endpoint(
            client, "GET", "/v0/credits",
            description="Check if credits endpoint exists and get structure"
        )
        results["credits"] = credits_result
        
        # Test 2: Health/Status endpoint variations
        print("\n" + "="*60)
        print("🏥 TESTING HEALTH/STATUS ENDPOINTS")
        print("="*60)
        
        for endpoint in ["/health", "/status", "/v0/health", "/v0/status", "/"]:
            health_result = await test_endpoint(
                client, "GET", endpoint,
                description=f"Check if {endpoint} exists for health checks"
            )
            results[f"health_{endpoint.replace('/', '_')}"] = health_result
        
        # Test 3: Scrape endpoint (basic functionality)
        print("\n" + "="*60)
        print("🕷️  TESTING SCRAPE ENDPOINT")
        print("="*60)
        
        scrape_payload = {
            "url": "https://httpbin.org/html",
            "formats": ["html", "markdown"]
        }
        
        scrape_result = await test_endpoint(
            client, "POST", "/v0/scrape",
            payload=scrape_payload,
            description="Test basic scraping functionality with simple test page"
        )
        results["scrape"] = scrape_result
        
        # Test 4: Search endpoint (if it exists)
        print("\n" + "="*60)
        print("🔍 TESTING SEARCH ENDPOINT")
        print("="*60)
        
        search_payload = {
            "query": "test",
            "domain": "httpbin.org"
        }
        
        search_result = await test_endpoint(
            client, "POST", "/v0/search",
            payload=search_payload,
            description="Check if search functionality exists"
        )
        results["search"] = search_result
        
        # Test 5: Invalid authentication
        print("\n" + "="*60)
        print("🔐 TESTING AUTHENTICATION ERRORS")
        print("="*60)
        
        # Test with invalid API key
        invalid_headers = {
            "Authorization": "Bearer invalid-key",
            "Content-Type": "application/json"
        }
        
        try:
            invalid_response = await client.get(
                f"{BASE_URL}/v0/credits",
                headers=invalid_headers,
                timeout=30
            )
            
            print(f"   📊 Invalid auth status: {invalid_response.status_code}")
            try:
                invalid_data = invalid_response.json()
                print(f"   📄 Invalid auth response: {json.dumps(invalid_data, indent=2)}")
            except:
                print(f"   📄 Invalid auth response (text): {invalid_response.text}")
                
            results["invalid_auth"] = {
                "status_code": invalid_response.status_code,
                "response": invalid_response.text
            }
            
        except Exception as e:
            print(f"   ❌ Error testing invalid auth: {e}")
            results["invalid_auth"] = {"error": str(e)}
        
        # Test 6: Rate limiting (be careful!)
        print("\n" + "="*60)
        print("⚡ TESTING RATE LIMITING (GENTLE)")
        print("="*60)
        
        print("   Making 3 quick requests to test rate limiting...")
        rate_limit_results = []
        
        for i in range(3):
            print(f"   Request {i+1}/3...")
            rate_result = await test_endpoint(
                client, "POST", "/v0/scrape",
                payload={"url": "https://httpbin.org/html", "formats": ["html"]},
                description=f"Rate limit test request {i+1}"
            )
            rate_limit_results.append(rate_result)
            
            # Small delay between requests
            await asyncio.sleep(1)
        
        results["rate_limiting"] = rate_limit_results
        
        return results


async def main():
    """Main discovery function."""
    print("🚀 Starting Firecrawl API Discovery...")
    
    try:
        results = await discover_firecrawl_api()
        
        print("\n" + "="*60)
        print("📋 DISCOVERY SUMMARY")
        print("="*60)
        
        # Analyze results
        working_endpoints = []
        failed_endpoints = []
        
        for endpoint, result in results.items():
            if result and isinstance(result, dict):
                if result.get("success") or result.get("status_code") in [200, 201]:
                    working_endpoints.append(endpoint)
                    print(f"✅ {endpoint}: Working (Status {result.get('status_code')})")
                elif result.get("status_code") == 401:
                    print(f"🔐 {endpoint}: Authentication required (Status 401)")
                elif result.get("status_code") == 404:
                    print(f"❌ {endpoint}: Not found (Status 404)")
                elif result.get("status_code") == 429:
                    print(f"⚡ {endpoint}: Rate limited (Status 429)")
                else:
                    failed_endpoints.append(endpoint)
                    print(f"❌ {endpoint}: Failed (Status {result.get('status_code', 'Unknown')})")
            else:
                failed_endpoints.append(endpoint)
                print(f"❌ {endpoint}: Failed (No response)")
        
        print(f"\n📊 Working endpoints: {len(working_endpoints)}")
        print(f"❌ Failed endpoints: {len(failed_endpoints)}")
        
        # Save detailed results
        results_file = backend_dir / "scripts" / "firecrawl_discovery_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        print("\n🎯 RECOMMENDATIONS FOR TEST FIXES:")
        print("-" * 40)
        
        if results.get("credits", {}).get("success"):
            print("✅ Credits endpoint works - update test expectations")
        else:
            print("❌ Credits endpoint doesn't work - remove or mock tests")
        
        if any(results.get(f"health_{k}", {}).get("success") for k in ["_health", "_status", "_v0_health", "_v0_status", "_"]):
            print("✅ Health endpoint exists - update test expectations")
        else:
            print("❌ No health endpoint found - implement custom health check")
        
        if results.get("scrape", {}).get("success"):
            print("✅ Scrape endpoint works - update response structure expectations")
        else:
            print("❌ Scrape endpoint failed - check authentication or payload")
        
        if results.get("search", {}).get("success"):
            print("✅ Search endpoint works - implement search functionality")
        else:
            print("❌ Search endpoint doesn't exist - remove search tests")
        
        print("\n🔧 Next steps:")
        print("1. Update FirecrawlClient based on working endpoints")
        print("2. Fix test expectations to match real API responses")
        print("3. Remove tests for non-existent endpoints")
        print("4. Add proper error handling for actual error responses")
        
    except Exception as e:
        print(f"\n💥 Discovery failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
