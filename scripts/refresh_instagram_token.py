#!/usr/bin/env python3
"""
Instagram Long-lived Token Refresh Script
毎週実行して、トークン有効期限を確認し、必要に応じて自動更新
短期トークンの場合は長期トークンに交換
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
import requests


def exchange_short_lived_to_long_lived(token, app_id, app_secret):
    """Exchange short-lived token to long-lived token"""
    try:
        response = requests.get(
            'https://graph.facebook.com/v18.0/oauth/access_token',
            params={
                'grant_type': 'fb_exchange_token',
                'client_id': app_id,
                'client_secret': app_secret,
                'access_token': token
            },
            timeout=5
        )
        data = response.json()

        if 'error' in data:
            error = data['error']
            raise ValueError(f"Token exchange failed: {error.get('message', str(error))}")

        new_token = data.get('access_token')
        if not new_token:
            raise ValueError("No access_token in exchange response")

        return new_token

    except Exception as e:
        print(f"❌ Error exchanging token: {str(e)}")
        return None


def check_token_expiry(token):
    """Check Instagram token expiry using debug endpoint"""
    try:
        response = requests.get(
            'https://graph.instagram.com/debug_token',
            params={
                'input_token': token,
                'access_token': token
            },
            timeout=5
        )
        data = response.json()

        if 'error' in data:
            error = data['error']
            raise ValueError(f"Debug API error: {error.get('message', str(error))}")

        if 'data' not in data:
            raise ValueError("No token data in response")

        expires_at = data['data'].get('expires_at', 0)
        app_id = data['data'].get('app_id')

        if expires_at == 0:
            print("⏰ Token type: Long-lived (no expiry)")
            return None, None

        expires_dt = datetime.fromtimestamp(expires_at)
        now = datetime.now()
        days_remaining = (expires_dt - now).days
        hours_remaining = ((expires_dt - now).seconds // 3600) % 24

        return expires_dt, days_remaining, hours_remaining

    except Exception as e:
        print(f"❌ Error checking token expiry: {str(e)}")
        return None, None, None


def refresh_token(token):
    """Refresh Instagram long-lived token"""
    try:
        response = requests.get(
            'https://graph.instagram.com/refresh_access_token',
            params={
                'grant_type': 'ig_refresh_token',
                'access_token': token
            },
            timeout=5
        )
        data = response.json()

        if 'error' in data:
            error = data['error']
            raise ValueError(f"Refresh API error: {error.get('message', str(error))}")

        new_token = data.get('access_token')
        if not new_token:
            raise ValueError("No access_token in refresh response")

        return new_token

    except Exception as e:
        print(f"❌ Error refreshing token: {str(e)}")
        return None


def update_github_secret(token):
    """Update INSTAGRAM_GRAPH_TOKEN in GitHub Secrets using gh CLI"""
    try:
        env = os.environ.copy()
        env['GH_TOKEN'] = os.getenv('GITHUB_TOKEN', '')

        if not env['GH_TOKEN']:
            raise ValueError("GITHUB_TOKEN environment variable not set")

        process = subprocess.Popen(
            ['gh', 'secret', 'set', 'INSTAGRAM_GRAPH_TOKEN', '--repo', os.getenv('GITHUB_REPOSITORY', '')],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )

        stdout, stderr = process.communicate(input=token.encode(), timeout=10)

        if process.returncode != 0:
            raise RuntimeError(f"gh secret set failed: {stderr.decode()}")

        return True

    except Exception as e:
        print(f"❌ Error updating GitHub secret: {str(e)}")
        return False


def main():
    token = os.getenv('INSTAGRAM_GRAPH_TOKEN')
    if not token:
        print("❌ INSTAGRAM_GRAPH_TOKEN not set")
        sys.exit(1)

    print("🔍 Checking Instagram token...\n")

    # Try to check expiry, but if it fails, proceed with exchange attempt
    result = check_token_expiry(token)

    # If token check failed, it might be a short-lived token that can still be exchanged
    if result[0] is None and result[1] is None:
        print("⚠️  Token check failed (likely short-lived or expired)")
        print("    Attempting direct token exchange...\n")

        app_id = os.getenv('FACEBOOK_APP_ID')
        app_secret = os.getenv('FACEBOOK_APP_SECRET')

        if not app_id or not app_secret:
            print("❌ Cannot exchange token without FACEBOOK_APP_ID/SECRET")
            sys.exit(1)

        new_token = exchange_short_lived_to_long_lived(token, app_id, app_secret)
        if new_token:
            print("✅ Token exchanged to long-lived format")
            print("🔄 Updating GitHub Secrets...\n")
            if update_github_secret(new_token):
                print("✅ Long-lived token saved to GitHub Secrets!\n")
                sys.exit(0)
            else:
                print("❌ Failed to save token to GitHub Secrets\n")
                sys.exit(1)
        else:
            print("❌ Token exchange failed")
            sys.exit(1)

    expires_dt, days_remaining, hours_remaining = result

    # Long-lived token (no expiry)
    if expires_dt is None:
        print("✅ Token is long-lived with no expiry.")
        print("   No refresh needed.\n")
        sys.exit(0)

    print(f"📅 Token expires at: {expires_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"⏱️  Days remaining: {days_remaining} days, {hours_remaining} hours\n")

    # Check if token is short-lived (< 3 days)
    if days_remaining < 3:
        print(f"⚠️  Short-lived token detected (expires in {days_remaining} days)")
        print("   Attempting to exchange for long-lived token...\n")

        app_id = os.getenv('FACEBOOK_APP_ID')
        app_secret = os.getenv('FACEBOOK_APP_SECRET')

        if not app_id or not app_secret:
            print("❌ FACEBOOK_APP_ID or FACEBOOK_APP_SECRET not set")
            print("   Cannot exchange token. Continuing with refresh cycle.\n")
        else:
            new_token = exchange_short_lived_to_long_lived(token, app_id, app_secret)
            if new_token:
                print("✅ Token exchanged to long-lived format")
                print("🔄 Updating GitHub Secrets...\n")
                if update_github_secret(new_token):
                    print("✅ Long-lived token saved to GitHub Secrets!\n")
                    sys.exit(0)
                else:
                    print("❌ Failed to save token to GitHub Secrets\n")
                    sys.exit(1)
            else:
                print("⚠️  Token exchange failed. Continuing with short-lived token.\n")

    if days_remaining > 7:
        print("✅ Token is valid for more than 7 days.")
        print("   No refresh needed.\n")
        sys.exit(0)

    print(f"⚠️  Token expires in {days_remaining} days. Attempting refresh...\n")

    new_token = refresh_token(token)

    if not new_token:
        print("❌ REFRESH FAILED")
        print("   Manual re-authentication required.")
        print("   Please visit Instagram app settings and re-authorize.\n")
        sys.exit(1)

    print("🔄 New token obtained. Updating GitHub Secrets...\n")

    if not update_github_secret(new_token):
        print("❌ FAILED TO UPDATE GITHUB SECRETS")
        print("   Please manually update INSTAGRAM_GRAPH_TOKEN with the new token.\n")
        sys.exit(1)

    print("✅ TOKEN REFRESHED AND UPDATED SUCCESSFULLY!")
    print(f"   New token is valid until: {datetime.fromtimestamp(datetime.now().timestamp() + 5184000).strftime('%Y-%m-%d')}\n")


if __name__ == '__main__':
    main()
