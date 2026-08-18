#!/usr/bin/env python3
"""
Night Research Script - Automated daily research of Instagram performance and website analytics
"""

import json
import os
import sys
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import requests
from anthropic import Anthropic
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, Dimension, Metric

# Initialize paths
RESEARCH_RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'research-results')
os.makedirs(RESEARCH_RESULTS_DIR, exist_ok=True)

def check_airtable_new_shops() -> Dict[str, Any]:
    """Check for newly added shops in Airtable (informational only, does not block)"""
    airtable_pat = os.getenv('AIRTABLE_TOKEN') or os.getenv('AIRTABLE_PAT')
    if not airtable_pat:
        raise ValueError("AIRTABLE_TOKEN or AIRTABLE_PAT environment variable not set")

    base_id = 'appyyoKM7RprQRht8'
    table_id = 'tblcOdcqCxzb7kX0e'

    headers = {'Authorization': f'Bearer {airtable_pat}'}
    url = f'https://api.airtable.com/v0/{base_id}/{table_id}'

    yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
    response = requests.get(
        url,
        headers=headers,
        params={'filterByFormula': f'CREATED_TIME() > "{yesterday}"'}
    )

    if response.status_code != 200:
        raise RuntimeError(f"Airtable API error: {response.status_code} {response.text}")

    data = response.json()
    if 'error' in data:
        raise RuntimeError(f"Airtable API error: {data['error']}")

    records = data.get('records', [])
    return {
        'type': 'new_shops',
        'count': len(records),
        'shops': [
            {
                'name': r['fields'].get('Store Name', 'N/A'),
                'area': r['fields'].get('Area', 'N/A'),
                'created_at': r['createdTime']
            }
            for r in records
        ]
    }

def get_instagram_performance() -> Dict[str, Any]:
    """Fetch Instagram Insights metrics"""
    token = os.getenv('INSTAGRAM_GRAPH_TOKEN')
    account_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')

    if not token or not account_id:
        raise ValueError("INSTAGRAM_GRAPH_TOKEN or INSTAGRAM_BUSINESS_ACCOUNT_ID not set")

    url = f'https://graph.facebook.com/v18.0/{account_id}/insights'
    params = {
        'metric': 'reach,follower_count',
        'period': 'day',
        'access_token': token
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise RuntimeError(f"Instagram API error: {response.status_code} {response.text}")

    data = response.json()
    if 'error' in data:
        raise RuntimeError(f"Instagram API error: {data['error']}")

    metrics = data.get('data', [])
    if not metrics:
        raise RuntimeError("No Instagram metrics data returned")

    return {
        'type': 'instagram_performance',
        'metrics': [
            {
                'name': m.get('name'),
                'value': m.get('values', [{}])[0].get('value', 0),
                'period': m.get('period')
            }
            for m in metrics
        ]
    }

def get_ga4_analytics() -> Dict[str, Any]:
    """Fetch GA4 website analytics for the last 7 days"""
    property_id = os.getenv('GA4_PROPERTY_ID')
    gcp_sa_key_b64 = os.getenv('GCP_SERVICE_ACCOUNT_KEY')

    if not property_id:
        raise ValueError("GA4_PROPERTY_ID environment variable not set")
    if not gcp_sa_key_b64:
        raise ValueError("GCP_SERVICE_ACCOUNT_KEY environment variable not set")

    key_json_str = base64.b64decode(gcp_sa_key_b64).decode('utf-8')
    key_json = json.loads(key_json_str)
    credentials = service_account.Credentials.from_service_account_info(key_json)

    client = BetaAnalyticsDataClient(credentials=credentials)

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[{'start_date': '7daysAgo', 'end_date': 'today'}],
        dimensions=[Dimension(name='date')],
        metrics=[
            Metric(name='sessions'),
            Metric(name='activeUsers'),
            Metric(name='engagedSessions')
        ]
    )

    response = client.run_report(request)

    if not response.rows:
        raise RuntimeError("No GA4 analytics data returned for the specified period")

    return {
        'type': 'ga4_analytics',
        'period': 'last_7_days',
        'rows': [
            {
                'date': row.dimension_values[0].value,
                'sessions': row.metric_values[0].value,
                'active_users': row.metric_values[1].value,
                'engaged_sessions': row.metric_values[2].value
            }
            for row in response.rows
        ]
    }

def get_market_trends() -> Dict[str, Any]:
    """Research market trends (placeholder)"""
    return {
        'type': 'market_trends',
        'note': 'Manual trend research placeholder - implement trend detection as needed',
        'trends': []
    }

def generate_analysis_and_suggestions(instagram_data: Optional[Dict[str, Any]], ga4_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate analysis and improvement suggestions using Claude"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("    ⚠ ANTHROPIC_API_KEY not set, skipping analysis")
        return {'type': 'analysis', 'suggestions': [], 'skipped': True}

    client = Anthropic()

    instagram_section = "Instagram Insights not available"
    if instagram_data:
        instagram_section = f"""**Instagram Insights (today):**
{json.dumps(instagram_data.get('metrics', []), ensure_ascii=False, indent=2)}"""

    prompt = f"""
You are a social media analytics expert for a bakery/cafe discovery website called "ちるまる" (Chirumaru).

Analyze the following data and provide specific, actionable improvement suggestions:

{instagram_section}

**Website Analytics (last 7 days):**
{json.dumps(ga4_data.get('rows', []), ensure_ascii=False, indent=2)}

Based on this data, provide 2-3 concrete improvement suggestions. For each suggestion:
1. **Problem:** What metric/trend indicates this issue?
2. **Root cause:** Why might this be happening?
3. **Suggestion:** What specific change to try?
4. **Expected impact:** How could this improve metrics?
5. **Implementation note:** If applicable, provide a code snippet or example (as Markdown)

Format your response as a JSON array of suggestion objects. Keep suggestions focused, practical, and implementable.

Example format:
```json
[
  {{
    "title": "Shorter hook text",
    "problem": "Posts with long hook text have lower reach",
    "root_cause": "Users scroll quickly; hooks >15 chars get less engagement",
    "suggestion": "Test hook text limited to 15 characters or less",
    "expected_impact": "Increase reach by 10-15%",
    "implementation_note": "Example: '新潟のパン屋7選' instead of '新潟県のおすすめパン屋さんを7つ厳選して紹介'"
  }}
]
```

Return ONLY the JSON array, no markdown code blocks, no explanation text, nothing else.
Start with [ and end with ], containing only valid JSON.
"""

    try:
        print(f"    [DEBUG] Sending prompt to Claude API (length: {len(prompt)} chars)")

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        print(f"    [DEBUG] Claude API response received. Content count: {len(message.content)}")

        if not message.content or len(message.content) == 0:
            print(f"    [DEBUG] ERROR: Response has no content blocks")
            return {'type': 'analysis', 'suggestions': [], 'error': 'No content in response'}

        print(f"    [DEBUG] First content block type: {message.content[0].type}")

        response_text = message.content[0].text.strip()
        print(f"    [DEBUG] Response text length: {len(response_text)} chars")

        if not response_text:
            print(f"    [DEBUG] ERROR: Response text is empty")
            return {'type': 'analysis', 'suggestions': [], 'error': 'Empty response text'}

        print(f"    [DEBUG] Response text (first 200 chars): {response_text[:200]}")

        # Remove Markdown code block wrapper if present
        if response_text.startswith('```'):
            print(f"    [DEBUG] Markdown code block detected. Stripping...")
            response_text = response_text[response_text.find('\n')+1:]
            if response_text.endswith('```'):
                response_text = response_text[:response_text.rfind('```')]
            response_text = response_text.strip()
            print(f"    [DEBUG] After stripping - text length: {len(response_text)}, first 100 chars: {response_text[:100]}")

        suggestions = json.loads(response_text)
        return {
            'type': 'analysis',
            'suggestions': suggestions,
            'timestamp': datetime.now().isoformat()
        }
    except json.JSONDecodeError as e:
        print(f"    [DEBUG] JSON decode error: {str(e)}")
        print(f"    [DEBUG] Response length: {len(response_text)} chars")
        print(f"    [DEBUG] Response last 200 chars: ...{response_text[-200:]}")
        print(f"    [DEBUG] Error position {e.pos}: context around error")
        if e.pos:
            start = max(0, e.pos - 50)
            end = min(len(response_text), e.pos + 50)
            print(f"    [DEBUG] Context: ...{response_text[start:end]}...")
        print(f"    ⚠ Analysis generation failed (non-critical): JSON parse error - {str(e)}")
        return {'type': 'analysis', 'suggestions': [], 'error': f'JSON parse: {str(e)}'}
    except Exception as e:
        print(f"    [DEBUG] Exception during analysis: {type(e).__name__}: {str(e)}")
        print(f"    ⚠ Analysis generation failed (non-critical): {str(e)}")
        return {'type': 'analysis', 'suggestions': [], 'error': str(e)}

def save_research_results(data: Dict[str, Any]) -> str:
    """Save research results to JSON file"""
    today = datetime.now().strftime('%Y-%m-%d')
    filename = f'research-{today}.json'
    filepath = os.path.join(RESEARCH_RESULTS_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filepath

def main():
    print("🌙 Starting night research...")

    results = []
    errors = []
    instagram_data = None
    ga4_data = None

    # Fetch Instagram Insights (non-critical, but preferred)
    try:
        print("  Fetching Instagram Insights...")
        instagram_data = get_instagram_performance()
        results.append(instagram_data)
        print("    ✓ Instagram Insights fetched")
    except Exception as e:
        print(f"    ⚠ Instagram Insights skipped (non-critical): {str(e)}")

    # Fetch GA4 Analytics (required)
    try:
        print("  Fetching GA4 Analytics...")
        ga4_data = get_ga4_analytics()
        results.append(ga4_data)
        print("    ✓ GA4 Analytics fetched")
    except Exception as e:
        error_msg = f"GA4 Analytics failed: {str(e)}"
        print(f"    ✗ {error_msg}")
        errors.append(error_msg)

    # Check Airtable for new shops (informational)
    try:
        print("  Checking Airtable for new shops...")
        results.append(check_airtable_new_shops())
        print("    ✓ Airtable check complete")
    except Exception as e:
        print(f"    ⚠ Airtable check failed (non-critical): {str(e)}")

    # Generate analysis and suggestions (optional - uses GA4 data)
    if ga4_data:
        try:
            print("  Generating analysis and suggestions...")
            analysis = generate_analysis_and_suggestions(instagram_data, ga4_data)
            results.append(analysis)
            print("    ✓ Analysis complete")
        except Exception as e:
            print(f"    ⚠ Analysis failed (non-critical): {str(e)}")

    # Check for critical errors
    if errors:
        print(f"\n❌ Research failed: {len(errors)} critical error(s)")
        for error in errors:
            print(f"   - {error}")
        sys.exit(1)

    # Save results
    research_data = {
        'timestamp': datetime.now().isoformat(),
        'timezone': 'Asia/Tokyo',
        'results': results
    }

    try:
        filepath = save_research_results(research_data)
        print(f"\n✅ Research complete. Results saved to {filepath}")
    except Exception as e:
        print(f"\n❌ Failed to save research results: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
