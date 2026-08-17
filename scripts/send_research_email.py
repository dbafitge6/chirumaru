#!/usr/bin/env python3
"""
Send research results via email
"""

import json
import os
import sys
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

RESEARCH_RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'research-results')

def load_latest_research() -> dict:
    """Load the latest research results"""
    today = datetime.now().strftime('%Y-%m-%d')
    filepath = os.path.join(RESEARCH_RESULTS_DIR, f'research-{today}.json')

    if not os.path.exists(filepath):
        return None

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_research_report(data: dict) -> str:
    """Format research data into email body"""
    html = """
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .header { background: #2c3e50; color: white; padding: 20px; text-align: center; }
            .section { margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; }
            .metric { display: inline-block; margin: 10px 20px 10px 0; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #f5f5f5; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 ちるまる 夜間リサーチレポート</h1>
            <p>{}</p>
        </div>
    """.format(data['timestamp'])

    for result in data['results']:
        result_type = result.get('type', 'unknown')

        if result_type == 'new_shops':
            count = result.get('count', 0)
            html += f"""
            <div class="section">
                <h2>🏪 新規店舗調査</h2>
                <p>過去24時間に追加された店舗: <strong>{count}</strong>件</p>
            """
            if result.get('shops'):
                html += "<table><tr><th>店名</th><th>エリア</th><th>追加日時</th></tr>"
                for shop in result['shops']:
                    html += f"""
                    <tr>
                        <td>{shop.get('name', 'N/A')}</td>
                        <td>{shop.get('area', 'N/A')}</td>
                        <td>{shop.get('created_at', 'N/A')[:10]}</td>
                    </tr>
                    """
                html += "</table>"
            html += "</div>"

        elif result_type == 'instagram_performance':
            html += "<div class='section'><h2>📱 Instagram パフォーマンス</h2>"
            if result.get('metrics'):
                for metric in result['metrics']:
                    html += f"""
                    <div class="metric">
                        <strong>{metric.get('name', 'N/A')}</strong><br>
                        {metric.get('value', 0)}
                    </div>
                    """
            else:
                html += "<p>データなし</p>"
            html += "</div>"

        elif result_type == 'ga4_analytics':
            html += "<div class='section'><h2>📈 Webサイト分析</h2>"
            if result.get('rows'):
                html += "<table><tr><th>日付</th><th>セッション</th><th>ユーザー</th><th>エンゲージメント</th></tr>"
                for row in result['rows']:
                    html += f"""
                    <tr>
                        <td>{row.get('date', 'N/A')}</td>
                        <td>{row.get('sessions', 0)}</td>
                        <td>{row.get('users', 0)}</td>
                        <td>{row.get('engaged_sessions', 0)}</td>
                    </tr>
                    """
                html += "</table>"
            else:
                html += "<p>データなし</p>"
            html += "</div>"

        elif result_type == 'market_trends':
            html += "<div class='section'><h2>🔍 市場トレンド</h2><p>{}</p></div>".format(
                result.get('note', 'No data available')
            )

    html += """
    </body>
    </html>
    """
    return html

def send_email(recipient: str, subject: str, html_body: str) -> bool:
    """Send email via Gmail SMTP"""
    try:
        sender_email = os.getenv('EMAIL_USER', 'your-email@gmail.com')
        password = os.getenv('EMAIL_PASSWORD', '')

        if not password:
            print("⚠️  EMAIL_PASSWORD not set. Skipping email send.")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = recipient

        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient, msg.as_string())

        print(f"✅ Email sent to {recipient}")
        return True

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python send_research_email.py <recipient_email>")
        sys.exit(1)

    recipient = sys.argv[1]
    data = load_latest_research()

    if not data:
        print("❌ No research results found for today")
        sys.exit(1)

    subject = f"📊 ちるまる 夜間リサーチレポート - {datetime.now().strftime('%Y年%m月%d日')}"
    html_body = format_research_report(data)

    send_email(recipient, subject, html_body)

if __name__ == '__main__':
    main()
