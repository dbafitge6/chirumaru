#!/usr/bin/env python3
"""
Convert short-lived Instagram token to long-lived token
Standalone utility for token conversion before setting in GitHub Secrets
"""

import os
import sys
import json
import requests
from datetime import datetime


def exchange_short_lived_to_long_lived(token, app_id, app_secret):
    """Exchange short-lived token to long-lived token"""
    print(f"Converting short-lived token to long-lived...")
    print(f"App ID: {app_id[:10]}...")
    print()

    try:
        response = requests.get(
            'https://graph.facebook.com/v18.0/oauth/access_token',
            params={
                'grant_type': 'fb_exchange_token',
                'client_id': app_id,
                'client_secret': app_secret,
                'access_token': token
            },
            timeout=10
        )

        data = response.json()

        if 'error' in data:
            error = data['error']
            print(f"❌ Exchange failed:")
            print(f"   Message: {error.get('message', 'Unknown error')}")
            print(f"   Type: {error.get('type')}")
            print(f"   Code: {error.get('code')}")
            return None

        new_token = data.get('access_token')
        if not new_token:
            print("❌ No access_token in response")
            return None

        expires_in = data.get('expires_in', 0)
        days_valid = expires_in // 86400 if expires_in > 0 else 0

        print(f"✅ Token exchange successful!")
        print()
        print(f"📋 Long-lived token details:")
        print(f"   Validity: {days_valid} days ({expires_in} seconds)")
        print(f"   Token length: {len(new_token)} characters")
        print()

        if days_valid < 60:
            print(f"⚠️  Warning: Token is only valid for {days_valid} days")
            print(f"   (Expected: 60+ days)")
        else:
            print(f"✅ Token is valid for {days_valid} days (OK)")
        print()

        return new_token

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None


def main():
    print("=" * 70)
    print("Instagram Token Converter: Short-lived → Long-lived")
    print("=" * 70)
    print()

    if len(sys.argv) < 2:
        print("Usage: python3 convert_token_to_long_lived.py <short_lived_token>")
        print()
        print("Environment variables required:")
        print("  - FACEBOOK_APP_ID")
        print("  - FACEBOOK_APP_SECRET")
        print()
        print("Example:")
        print("  export FACEBOOK_APP_ID=your_app_id")
        print("  export FACEBOOK_APP_SECRET=your_app_secret")
        print("  python3 convert_token_to_long_lived.py EAAXYZ...")
        sys.exit(1)

    short_token = sys.argv[1]
    app_id = os.getenv('FACEBOOK_APP_ID')
    app_secret = os.getenv('FACEBOOK_APP_SECRET')

    if not app_id or not app_secret:
        print("❌ Missing environment variables:")
        if not app_id:
            print("   - FACEBOOK_APP_ID")
        if not app_secret:
            print("   - FACEBOOK_APP_SECRET")
        sys.exit(1)

    print(f"Input token: {short_token[:30]}...")
    print()

    long_token = exchange_short_lived_to_long_lived(short_token, app_id, app_secret)

    if not long_token:
        print("❌ Conversion failed")
        sys.exit(1)

    print("=" * 70)
    print("RESULT: Long-lived token ready for GitHub Secrets")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Copy the token below:")
    print()
    print(f"   {long_token}")
    print()
    print("2. Set in GitHub Secrets:")
    print("   Name: INSTAGRAM_GRAPH_TOKEN")
    print("   Value: (paste the token above)")
    print()
    print("3. Verify with refresh_instagram_token.yml workflow")
    print()


if __name__ == '__main__':
    main()
