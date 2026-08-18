#!/usr/bin/env python3
"""Analytics data collection script for ちるまる.

Collects Instagram Insights and GA4 analytics data, records to data/analytics.json.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, Dimension, Metric


def load_env():
    """Load environment variables from .env file."""
    from dotenv import load_dotenv
    load_dotenv()


def check_instagram_token_expiry():
    """Check Instagram token expiry and return status."""
    token = os.getenv("INSTAGRAM_GRAPH_TOKEN")
    if not token:
        return {"status": "missing", "warning": "INSTAGRAM_GRAPH_TOKEN not set"}

    # Verify token is still valid by making a test request
    try:
        url = f"https://graph.instagram.com/me?fields=id,username&access_token={token}"
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return {"status": "invalid", "warning": "Token validation failed"}
    except Exception as e:
        return {"status": "error", "warning": f"Token check error: {str(e)}"}

    # Calculate days remaining (assume 60-day validity from issue date)
    # This is a placeholder; actual expiry date should be tracked separately
    return {
        "status": "valid",
        "issued_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=60)).isoformat(),
        "days_remaining": 60,
        "warning": None
    }


def fetch_instagram_insights(account_id: str, token: str) -> list:
    """Fetch Instagram Insights via Postiz API (more reliable)."""
    insights = []

    try:
        import subprocess
        import json
        import re

        # Use Postiz CLI to fetch Instagram analytics
        result = subprocess.run(
            ["postiz", "analytics:platform", "cmsopxrcz024opo0ygfgl0m4q", "-d", "7"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            # Extract JSON from output (skip the emoji prefix line)
            output = result.stdout
            # Find JSON array
            match = re.search(r'\[\s*\{.*\}\s*\]', output, re.DOTALL)
            if match:
                try:
                    insights = json.loads(match.group())
                    print(f"✓ Fetched {len(insights)} Instagram metrics via Postiz")
                except Exception as parse_err:
                    print(f"⚠ JSON parsing error: {str(parse_err)}")
            else:
                print("⚠ No JSON data found in Postiz response")
        else:
            print(f"✗ Postiz analytics error: {result.stderr}")

    except Exception as e:
        print(f"✗ Instagram fetch error: {str(e)}")

    return insights


def fetch_ga4_analytics(property_id: str, service_account_key: str) -> dict:
    """Fetch GA4 analytics data via two requests: site-wide and by traffic source."""
    analytics = {}

    try:
        import base64
        key_data = base64.b64decode(service_account_key)
        key_json = json.loads(key_data)

        credentials = service_account.Credentials.from_service_account_info(key_json)
        client = BetaAnalyticsDataClient(credentials=credentials)

        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        # Request A: Site-wide metrics (no dimensions)
        request_a = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[{"start_date": start_date, "end_date": end_date}],
            dimensions=[],
            metrics=[
                Metric(name="sessions"),
                Metric(name="totalUsers"),
                Metric(name="screenPageViews"),
            ],
        )

        response_a = client.run_report(request_a)

        # Process site-wide results
        if len(response_a.rows) > 0:
            row = response_a.rows[0]
            analytics["site_total"] = {
                "period": "last_90_days",
                "sessions": int(row.metric_values[0].value),
                "total_users": int(row.metric_values[1].value),
                "screen_page_views": int(row.metric_values[2].value),
            }
            print(f"✓ Fetched GA4 site-wide metrics")
        else:
            print(f"⚠ No site-wide data available")

        # Request B: By traffic source
        request_b = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[{"start_date": start_date, "end_date": end_date}],
            dimensions=[Dimension(name="sessionSource")],
            metrics=[Metric(name="sessions")],
        )

        response_b = client.run_report(request_b)

        # Process source-based results
        analytics["by_source"] = []
        for row in response_b.rows:
            analytics["by_source"].append({
                "source": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
            })

        print(f"✓ Fetched GA4 analytics from {len(analytics['by_source'])} sources")

    except Exception as e:
        print(f"✗ GA4 fetch error: {str(e)}")
        analytics["error"] = str(e)

    return analytics


def append_to_analytics_json(token_status: dict, instagram_insights: list, ga4_analytics: dict):
    """Append data to data/analytics.json in append-only format."""
    analytics_file = Path("data/analytics.json")

    # Initialize if file doesn't exist
    if not analytics_file.exists():
        analytics_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "instagram_token_status": [],
            "instagram_insights": [],
            "ga4_site_metrics": [],
            "ga4_source_breakdown": [],
        }
    else:
        with open(analytics_file) as f:
            data = json.load(f)

    # Append token status
    data["instagram_token_status"].append({
        "timestamp": datetime.now().isoformat(),
        **token_status
    })

    # Append Instagram insights if available
    if instagram_insights:
        data["instagram_insights"].append({
            "timestamp": datetime.now().isoformat(),
            "insights": instagram_insights
        })

    # Append GA4 data if available
    if ga4_analytics and "error" not in ga4_analytics:
        if "site_total" in ga4_analytics:
            data["ga4_site_metrics"].append({
                "timestamp": datetime.now().isoformat(),
                **ga4_analytics["site_total"]
            })

        if "by_source" in ga4_analytics:
            data["ga4_source_breakdown"].append({
                "timestamp": datetime.now().isoformat(),
                "sources": ga4_analytics["by_source"]
            })

    # Write back to file
    with open(analytics_file, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ Appended data to {analytics_file}")


def main():
    """Main entry point."""
    print("=== ちるまる Analytics Collector ===\n")

    load_env()

    # Check token expiry
    print("Checking Instagram token...")
    token_status = check_instagram_token_expiry()

    if token_status["status"] == "missing":
        print("✗ INSTAGRAM_GRAPH_TOKEN not configured")
        return 1

    if token_status.get("warning"):
        print(f"⚠ Warning: {token_status['warning']}")

    # Fetch data
    instagram_account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
    instagram_token = os.getenv("INSTAGRAM_GRAPH_TOKEN")
    ga4_property_id = os.getenv("GA4_PROPERTY_ID")
    ga4_service_account_key = os.getenv("GCP_SERVICE_ACCOUNT_KEY")

    instagram_insights = []
    ga4_analytics = {}

    if instagram_account_id and instagram_token:
        print("\nFetching Instagram Insights...")
        instagram_insights = fetch_instagram_insights(instagram_account_id, instagram_token)
    else:
        print("⚠ Skipping Instagram: INSTAGRAM_BUSINESS_ACCOUNT_ID or token not set")

    if ga4_property_id and ga4_service_account_key:
        print("\nFetching GA4 Analytics...")
        ga4_analytics = fetch_ga4_analytics(ga4_property_id, ga4_service_account_key)
    else:
        print("⚠ Skipping GA4: GA4_PROPERTY_ID or GCP_SERVICE_ACCOUNT_KEY not set")

    # Save to file
    print("\nSaving data...")
    append_to_analytics_json(token_status, instagram_insights, ga4_analytics)

    print("\n=== Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
