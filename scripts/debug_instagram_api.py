#!/usr/bin/env python3
"""
Debug script to test Instagram Graph API endpoints and identify correct configuration
"""

import os
import sys
import json
import requests
from datetime import datetime


def test_instagram_endpoint(token, account_id, endpoint_base, version="v18.0"):
    """Test Instagram insights fetch with given endpoint"""
    print(f"\n{'='*70}")
    print(f"Testing: {endpoint_base}")
    print('='*70)

    url = f'{endpoint_base}/{version}/{account_id}/insights'
    print(f"URL: {url}")

    # Test 1: Basic connection with common metrics
    print("\n[Test 1] Fetching common metrics...")
    params = {
        'metric': 'impressions,reach,profile_views',
        'period': 'day',
        'access_token': token
    }
    print(f"Params: metric=impressions,reach,profile_views; period=day")

    try:
        response = requests.get(url, params=params, timeout=5)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                print(f"✅ SUCCESS - Received {len(data['data'])} metrics")
                print(f"Metrics: {[m.get('name') for m in data['data']]}")
                return True, data
            elif 'error' not in data:
                print(f"⚠️  No data returned but no error")
                return None, data
        elif response.status_code == 400:
            data = response.json()
            if 'error' in data:
                error = data['error']
                print(f"❌ ERROR {response.status_code}")
                print(f"   Message: {error.get('message', 'Unknown')}")
                print(f"   Type: {error.get('type', 'Unknown')}")
                print(f"   Code: {error.get('code', 'Unknown')}")
                return False, data
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False, response.text

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False, str(e)

    return None, None


def test_account_id_verification(token, account_id, endpoint_base, version="v18.0"):
    """Test if account_id is valid"""
    print(f"\n[Test 2] Verifying account ID...")

    url = f'{endpoint_base}/{version}/{account_id}?fields=id,name,biography,profile_picture_url'
    print(f"URL: {url}")
    print(f"Params: access_token=***")

    try:
        response = requests.get(url, params={'access_token': token}, timeout=5)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Account verified")
            print(f"   ID: {data.get('id')}")
            print(f"   Name: {data.get('name')}")
            print(f"   Biography: {data.get('biography', 'N/A')[:50]}")
            return True, data
        elif response.status_code == 400:
            data = response.json()
            if 'error' in data:
                error = data['error']
                print(f"❌ ERROR {response.status_code}")
                print(f"   Message: {error.get('message')}")
                print(f"   Type: {error.get('type')}")
                return False, data
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False, response.text

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False, str(e)

    return None, None


def test_available_metrics(token, account_id, endpoint_base, version="v18.0"):
    """Test what metrics are available without specifying metric parameter"""
    print(f"\n[Test 3] Fetching all available metrics (no filter)...")

    url = f'{endpoint_base}/{version}/{account_id}/insights'
    print(f"URL: {url}")
    print(f"Params: period=day (no metric filter)")

    try:
        params = {
            'period': 'day',
            'access_token': token
        }
        response = requests.get(url, params=params, timeout=5)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                metrics = data['data']
                print(f"✅ Received {len(metrics)} metrics")
                for m in metrics:
                    print(f"   - {m.get('name')}: {m.get('period')}")
                    if 'values' in m and m['values']:
                        print(f"     (Sample value: {m['values'][0].get('value')})")
                return True, data
            else:
                print(f"⚠️  No data returned")
                return None, data
        elif response.status_code == 400:
            data = response.json()
            if 'error' in data:
                error = data['error']
                print(f"❌ ERROR {response.status_code}")
                print(f"   Message: {error.get('message')}")
                return False, data
        else:
            print(f"❌ HTTP {response.status_code}")
            return False, response.text

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False, str(e)

    return None, None


def test_token_debug(token, endpoint_base, version="v18.0"):
    """Debug token validity"""
    print(f"\n[Test 4] Token debug information...")

    url = f'{endpoint_base}/{version}/debug_token'
    print(f"URL: {url}")
    print(f"Params: input_token=***; access_token=***")

    try:
        params = {
            'input_token': token,
            'access_token': token
        }
        response = requests.get(url, params=params, timeout=5)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                token_data = data['data']
                print(f"✅ Token info retrieved")
                print(f"   Valid: {token_data.get('is_valid')}")
                print(f"   App ID: {token_data.get('app_id')}")
                print(f"   User ID: {token_data.get('user_id')}")
                print(f"   Scopes: {', '.join(token_data.get('scopes', []))}")
                print(f"   Expires: {token_data.get('expires_at')}")
                return True, data
            else:
                print(f"⚠️  No data in response")
                return None, data
        elif response.status_code == 400:
            data = response.json()
            if 'error' in data:
                error = data['error']
                print(f"❌ ERROR {response.status_code}")
                print(f"   Message: {error.get('message')}")
                return False, data
        else:
            print(f"❌ HTTP {response.status_code}")
            return False, response.text

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False, str(e)

    return None, None


def main():
    token = os.getenv('INSTAGRAM_GRAPH_TOKEN')
    account_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')

    if not token or not account_id:
        print("❌ Missing environment variables:")
        if not token:
            print("   - INSTAGRAM_GRAPH_TOKEN")
        if not account_id:
            print("   - INSTAGRAM_BUSINESS_ACCOUNT_ID")
        sys.exit(1)

    print("🔍 Instagram API Endpoint Debug")
    print(f"Account ID: {account_id}")
    print(f"Token: {token[:20]}... (length: {len(token)})")

    # Test endpoints
    endpoints = [
        ('graph.instagram.com', 'https://graph.instagram.com'),
        ('graph.facebook.com', 'https://graph.facebook.com'),
    ]

    results = {}

    for name, endpoint_base in endpoints:
        print(f"\n\n{'#'*70}")
        print(f"# ENDPOINT: {name}")
        print(f"{'#'*70}")

        # Test token validity first (graph.facebook.com for debug_token)
        if name == 'graph.facebook.com':
            test_token_debug(token, endpoint_base)

        # Test account verification
        test_account_id_verification(token, account_id, endpoint_base)

        # Test insights with common metrics
        success, data = test_instagram_endpoint(token, account_id, endpoint_base)
        results[name] = success

        # If common metrics failed, try without filter
        if not success:
            test_available_metrics(token, account_id, endpoint_base)

    # Summary
    print(f"\n\n{'='*70}")
    print("SUMMARY")
    print('='*70)
    for name, success in results.items():
        status = "✅ WORKS" if success else "❌ FAILS" if success is False else "⚠️  PARTIAL"
        print(f"{name}: {status}")

    print("\n📋 Recommendation:")
    if results.get('graph.facebook.com'):
        print("   Use: graph.facebook.com (recommended by Meta for modern API)")
    elif results.get('graph.instagram.com'):
        print("   Use: graph.instagram.com (Instagram-specific endpoint)")
    else:
        print("   Neither endpoint worked. Check:")
        print("   1. Token validity and permissions")
        print("   2. Account ID format")
        print("   3. API version compatibility")


if __name__ == '__main__':
    main()
