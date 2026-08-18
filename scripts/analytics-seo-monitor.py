#!/usr/bin/env python3
"""
GA4 + Search Console 日次モニタリングスクリプト
前日比±30%以上の変化があれば通知
"""

import json
import os
import base64
from datetime import datetime, timedelta
import sys

try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import RunReportRequest, Dimension, Metric
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except ImportError:
    print("❌ 必要なライブラリがインストールされていません")
    print("実行: pip install google-analytics-data google-api-python-client")
    sys.exit(1)


def load_service_account():
    """サービスアカウント認証情報を読み込む（環境変数から Base64 デコード）"""
    gcp_sa_key_b64 = os.getenv('GCP_SERVICE_ACCOUNT_KEY')
    if not gcp_sa_key_b64:
        print("❌ エラー: GCP_SERVICE_ACCOUNT_KEY 環境変数が設定されていません")
        sys.exit(1)

    try:
        key_json_str = base64.b64decode(gcp_sa_key_b64).decode('utf-8')
        key_json = json.loads(key_json_str)

        return service_account.Credentials.from_service_account_info(
            key_json,
            scopes=[
                "https://www.googleapis.com/auth/analytics.readonly",
                "https://www.googleapis.com/auth/webmasters.readonly",
            ]
        )
    except Exception as e:
        print(f"❌ 認証情報の読み込みに失敗しました: {e}")
        sys.exit(1)


def get_ga4_data(credentials, property_id="547703308"):
    """GA4 データを取得"""
    try:
        client = BetaAnalyticsDataClient(credentials=credentials)

        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        day_before_yesterday = today - timedelta(days=2)

        # 昨日のデータ
        request_yesterday = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[{
                "start_date": str(yesterday),
                "end_date": str(yesterday),
            }],
            dimensions=[Dimension(name="source")],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="sessions"),
            ],
        )
        response_yesterday = client.run_report(request_yesterday)

        # 一昨日のデータ
        request_day_before = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[{
                "start_date": str(day_before_yesterday),
                "end_date": str(day_before_yesterday),
            }],
            dimensions=[Dimension(name="source")],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="sessions"),
            ],
        )
        response_day_before = client.run_report(request_day_before)

        # データ抽出
        def aggregate_rows(response):
            total = {"activeUsers": 0, "sessions": 0}
            sources = {}

            for row in response.rows:
                source = row.dimension_values[0].value if len(row.dimension_values) > 0 else "Unknown"
                active_users = int(row.metric_values[0].value)
                sessions = int(row.metric_values[1].value)

                total["activeUsers"] += active_users
                total["sessions"] += sessions

                if source not in sources:
                    sources[source] = {"sessions": 0, "activeUsers": 0}
                sources[source]["sessions"] += sessions
                sources[source]["activeUsers"] += active_users

            return total, sources

        yesterday_total, yesterday_sources = aggregate_rows(response_yesterday)
        day_before_total, day_before_sources = aggregate_rows(response_day_before)

        # 主要な流入経路（トップ 3）
        top_sources = sorted(
            yesterday_sources.items(),
            key=lambda x: x[1]["sessions"],
            reverse=True
        )[:3]

        return {
            "date": str(yesterday),
            "yesterday": yesterday_total,
            "day_before": day_before_total,
            "top_sources": [{"source": src, **data} for src, data in top_sources],
        }

    except Exception as e:
        print(f"❌ GA4 データ取得エラー: {e}")
        return {"error": str(e)}


def get_search_console_data(credentials, site_url="sc-domain:chirumaru.jp"):
    """Search Console データを取得（3日前を起点に前日比較）"""
    try:
        service = build('webmasters', 'v3', credentials=credentials)

        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        three_days_ago = today - timedelta(days=3)
        four_days_ago = today - timedelta(days=4)

        # 昨日のデータ
        request_yesterday = {
            'startDate': str(yesterday),
            'endDate': str(yesterday),
            'dimensions': ['date'],
            'rowLimit': 10000,
        }

        response_yesterday = service.searchanalytics().query(
            siteUrl=site_url,
            body=request_yesterday
        ).execute()

        # 3日前のデータ（比較対象）
        request_comparison = {
            'startDate': str(three_days_ago),
            'endDate': str(three_days_ago),
            'dimensions': ['date'],
            'rowLimit': 10000,
        }

        response_comparison = service.searchanalytics().query(
            siteUrl=site_url,
            body=request_comparison
        ).execute()

        def calculate_totals(response):
            if not response.get('rows'):
                return {"clicks": 0, "impressions": 0, "ctr": 0, "position": 0}

            total_clicks = 0
            total_impressions = 0
            total_ctr = 0
            total_position = 0

            for row in response.get('rows', []):
                total_clicks += row.get('clicks', 0)
                total_impressions += row.get('impressions', 0)
                total_ctr += row.get('ctr', 0)
                total_position += row.get('position', 0)

            count = len(response.get('rows', []))
            return {
                "clicks": total_clicks,
                "impressions": total_impressions,
                "ctr": round(total_ctr / count if count > 0 else 0, 4),
                "position": round(total_position / count if count > 0 else 0, 2),
            }

        yesterday_data = calculate_totals(response_yesterday)
        comparison_data = calculate_totals(response_comparison)

        return {
            "date": str(yesterday),
            "yesterday": yesterday_data,
            "three_days_ago": comparison_data,
        }

    except Exception as e:
        print(f"⚠️  Search Console データ取得エラー: {e}")
        return {"error": str(e)}


def calculate_change_percentage(yesterday, day_before):
    """前日比を計算（パーセント）"""
    if not day_before or day_before == 0:
        return None
    return ((yesterday - day_before) / day_before) * 100


def check_significant_changes(ga4_data, sc_data, threshold=30):
    """±30%以上の変化をチェック"""
    changes = []

    # GA4 の変化チェック
    if "error" not in ga4_data and ga4_data.get("yesterday") and ga4_data.get("day_before"):
        for metric in ["activeUsers", "sessions"]:
            yesterday_val = ga4_data["yesterday"].get(metric, 0)
            day_before_val = ga4_data["day_before"].get(metric, 0)

            pct_change = calculate_change_percentage(yesterday_val, day_before_val)
            if pct_change is not None and abs(pct_change) >= threshold:
                changes.append({
                    "source": "GA4",
                    "metric": metric,
                    "yesterday": yesterday_val,
                    "day_before": day_before_val,
                    "change_percent": round(pct_change, 2),
                })

    # Search Console の変化チェック（3日前比較）
    if "error" not in sc_data and sc_data.get("yesterday") and sc_data.get("three_days_ago"):
        for metric in ["clicks", "impressions"]:
            yesterday_val = sc_data["yesterday"].get(metric, 0)
            comparison_val = sc_data["three_days_ago"].get(metric, 0)

            pct_change = calculate_change_percentage(yesterday_val, comparison_val)
            if pct_change is not None and abs(pct_change) >= threshold:
                changes.append({
                    "source": "Search Console",
                    "metric": metric,
                    "yesterday": yesterday_val,
                    "three_days_ago": comparison_val,
                    "change_percent": round(pct_change, 2),
                })

    return changes


def save_data(ga4_data, sc_data, changes):
    """データを JSON に保存（相対パス）"""
    output_dir = os.getenv('ANALYTICS_OUTPUT_DIR', 'analytics-results')
    os.makedirs(output_dir, exist_ok=True)

    today = datetime.now().strftime('%Y-%m-%d')
    output_file = os.path.join(output_dir, f'chirumaru-analytics-{today}.json')

    report = {
        "timestamp": datetime.now().isoformat(),
        "ga4": ga4_data,
        "search_console": sc_data,
        "significant_changes": changes,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return output_file


def print_report(ga4_data, sc_data, changes):
    """レポートを表示"""
    print("\n" + "="*50)
    print("📊 chirumaru.jp 日次モニタリング")
    print("="*50)

    # GA4 サマリー
    if "error" not in ga4_data:
        print("\n【GA4 データ】")
        print(f"  アクティブユーザー: {ga4_data['yesterday'].get('activeUsers', 0)}")
        print(f"  セッション数: {ga4_data['yesterday'].get('sessions', 0)}")
        if ga4_data.get('top_sources'):
            print("\n  主要な流入経路:")
            for src in ga4_data['top_sources'][:3]:
                print(f"    - {src['source']}: {src['sessions']} セッション")

    # Search Console サマリー
    if "error" not in sc_data:
        print("\n【Search Console】")
        print(f"  クリック数: {sc_data['yesterday'].get('clicks', 0)}")
        print(f"  表示回数: {sc_data['yesterday'].get('impressions', 0)}")
        print(f"  平均掲載順位: {sc_data['yesterday'].get('position', 0):.1f}")
        print(f"  平均CTR: {sc_data['yesterday'].get('ctr', 0):.4f}")

    # 変化の通知
    if changes:
        print("\n" + "⚠️  前日比±30%以上の変化を検出" + "\n")
        for change in changes:
            print(f"【{change['source']}】{change['metric']}")
            print(f"  昨日: {change['yesterday']}")
            if change['source'] == 'Search Console':
                print(f"  3日前: {change.get('three_days_ago', change.get('day_before'))}")
            else:
                print(f"  一昨日: {change.get('day_before', 'N/A')}")
            print(f"  変化率: {change['change_percent']:+.1f}%\n")
    else:
        print("\n✅ 有意な変化はありません（±30%未満）")

    print("="*50 + "\n")


def main():
    try:
        credentials = load_service_account()

        # データ取得
        print("📊 GA4 データを取得中...")
        ga4_data = get_ga4_data(credentials)

        print("📊 Search Console データを取得中...")
        sc_data = get_search_console_data(credentials)

        # 変化チェック
        changes = check_significant_changes(ga4_data, sc_data, threshold=30)

        # 保存
        output_file = save_data(ga4_data, sc_data, changes)
        print(f"✅ データを保存しました: {output_file}")

        # 表示
        print_report(ga4_data, sc_data, changes)

        return 0

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
