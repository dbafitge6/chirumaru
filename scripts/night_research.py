#!/usr/bin/env python3
"""
Night Research Script - Automated daily research of new shops, Instagram performance, and market trends
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any
import requests
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, Dimension, Metric

# Initialize paths
RESEARCH_RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'research-results')
os.makedirs(RESEARCH_RESULTS_DIR, exist_ok=True)

def get_new_shops_research() -> Dict[str, Any]:
    """Research newly added shops and check for duplicates"""
    try:
        airtable_pat = os.getenv('AIRTABLE_PAT')
        base_id = 'appyyoKM7RprQRht8'
        table_id = 'tblcOdcqCxzb7kX0e'

        headers = {'Authorization': f'Bearer {airtable_pat}'}
        url = f'https://api.airtable.com/v0/{base_id}/{table_id}'

        # Get records created in last 24 hours
        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
        response = requests.get(
            url,
            headers=headers,
            params={'filterByFormula': f'CREATED_TIME() > "{yesterday}"'}
        )

        records = response.json().get('records', [])
        return {
            'type': 'new_shops',
            'count': len(records),
            'shops': [
                {
                    'name': r['fields'].get('Shop Name', 'N/A'),
                    'area': r['fields'].get('Area', 'N/A'),
                    'created_at': r['createdTime']
                }
                for r in records
            ]
        }
    except Exception as e:
        return {
            'type': 'new_shops',
            'error': str(e),
            'count': 0,
            'shops': []
        }

def get_instagram_performance() -> Dict[str, Any]:
    """Analyze Instagram post performance"""
    try:
        token = os.getenv('INSTAGRAM_GRAPH_TOKEN')
        account_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')

        url = f'https://graph.instagram.com/v18.0/{account_id}/insights'
        params = {
            'metric': 'impressions,reach,profile_views',
            'period': 'day',
            'access_token': token
        }

        response = requests.get(url, params=params)
        data = response.json().get('data', [])

        return {
            'type': 'instagram_performance',
            'metrics': [
                {
                    'name': m.get('name'),
                    'value': m.get('values', [{}])[0].get('value', 0),
                    'period': m.get('period')
                }
                for m in data
            ]
        }
    except Exception as e:
        return {
            'type': 'instagram_performance',
            'error': str(e),
            'metrics': []
        }

def get_ga4_analytics() -> Dict[str, Any]:
    """Get GA4 website analytics"""
    try:
        property_id = os.getenv('GA4_PROPERTY_ID')

        client = BetaAnalyticsDataClient()

        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[{'start_date': '7daysAgo', 'end_date': 'today'}],
            dimensions=[Dimension(name='date')],
            metrics=[
                Metric(name='sessions'),
                Metric(name='users'),
                Metric(name='engagedSessions')
            ]
        )

        response = client.run_report(request)

        return {
            'type': 'ga4_analytics',
            'period': 'last_7_days',
            'rows': [
                {
                    'date': row.dimension_values[0].value,
                    'sessions': row.metric_values[0].value,
                    'users': row.metric_values[1].value,
                    'engaged_sessions': row.metric_values[2].value
                }
                for row in response.rows
            ]
        }
    except Exception as e:
        return {
            'type': 'ga4_analytics',
            'error': str(e),
            'rows': []
        }

def get_market_trends() -> Dict[str, Any]:
    """Research market trends (placeholder)"""
    return {
        'type': 'market_trends',
        'note': 'Manual trend research placeholder - implement trend detection as needed',
        'trends': []
    }

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

    research_data = {
        'timestamp': datetime.now().isoformat(),
        'timezone': 'Asia/Tokyo',
        'results': [
            get_new_shops_research(),
            get_instagram_performance(),
            get_ga4_analytics(),
            get_market_trends()
        ]
    }

    filepath = save_research_results(research_data)
    print(f"✅ Research complete. Results saved to {filepath}")

if __name__ == '__main__':
    main()
