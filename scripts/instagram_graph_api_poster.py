#!/usr/bin/env python3
"""
Instagram Graph API を使った直接投稿モジュール
Postiz を経由せず、Meta API に直接投稿する
"""

import os
import requests
import json
import sys
import time
from pathlib import Path

def upload_video_to_instagram(
    video_url: str,
    caption: str,
    business_account_id: str,
    graph_token: str,
    api_version: str = "v18.0"
) -> dict:
    """
    Instagram Graph API を使ってビデオを直接投稿

    Args:
        video_url: 公開 URL のビデオファイル
        caption: 投稿キャプション
        business_account_id: Instagram Business Account ID
        graph_token: Instagram Graph API アクセストークン
        api_version: Graph API バージョン

    Returns:
        投稿結果（post_id, url 等を含む）
    """

    print("📱 Uploading video to Instagram via Graph API...")

    # Step 1: ビデオをメディアとしてアップロード
    print(f"  1️⃣ Uploading video: {video_url}")

    media_url = f"https://graph.facebook.com/{api_version}/{business_account_id}/media"
    media_payload = {
        "video_url": video_url,
        "caption": caption,
        "media_type": "REELS"
    }

    # トークンはクエリパラメータで渡す
    media_response = requests.post(media_url, json=media_payload, params={"access_token": graph_token})

    if media_response.status_code != 200:
        error_detail = media_response.json().get("error", {})
        print(f"❌ Media upload failed: {error_detail}")
        return {"success": False, "error": error_detail}

    media_data = media_response.json()
    media_id = media_data.get("id")

    if not media_id:
        print(f"❌ No media ID returned")
        return {"success": False, "error": "No media ID in response"}

    print(f"  ✅ Media created: {media_id}")

    # Step 1.5: メディアのエンコード完了を待つ
    print(f"  ⏳ Waiting for media encoding to complete...")

    status_url = f"https://graph.facebook.com/{api_version}/{media_id}"
    status_params = {
        "fields": "status_code",
        "access_token": graph_token
    }

    max_wait = 60  # seconds
    poll_interval = 2  # seconds
    elapsed = 0

    while elapsed < max_wait:
        status_response = requests.get(status_url, params=status_params)

        if status_response.status_code != 200:
            error_detail = status_response.json().get("error", {})
            print(f"❌ Status check failed: {error_detail}")
            return {"success": False, "error": error_detail, "media_id": media_id}

        status_data = status_response.json()
        status_code = status_data.get("status_code")

        if status_code == "FINISHED":
            print(f"  ✅ Encoding complete (status: {status_code})")
            break
        else:
            print(f"  ⏳ Status: {status_code} (waiting...)")
            time.sleep(poll_interval)
            elapsed += poll_interval
    else:
        print(f"❌ Timeout: Media encoding did not complete within {max_wait}s")
        return {"success": False, "error": "Encoding timeout", "media_id": media_id}

    # Step 2: メディアを公開
    print(f"  2️⃣ Publishing media...")

    # 正しいエンドポイント: /{ig-user-id}/media_publish
    # creation_id パラメータで media_id を指定
    publish_url = f"https://graph.facebook.com/{api_version}/{business_account_id}/media_publish"
    publish_payload = {
        "creation_id": media_id
    }

    # トークンはクエリパラメータで渡す
    publish_response = requests.post(
        publish_url,
        json=publish_payload,
        params={"access_token": graph_token}
    )

    if publish_response.status_code != 200:
        error_detail = publish_response.json().get("error", {})
        print(f"❌ Publish failed: {error_detail}")
        return {"success": False, "error": error_detail, "media_id": media_id}

    publish_data = publish_response.json()

    print(f"  ✅ Media published successfully")

    return {
        "success": True,
        "media_id": media_id,
        "response": publish_data
    }


if __name__ == "__main__":
    # .env ファイルを読み込む
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

    # テスト用
    token = os.environ.get("INSTAGRAM_GRAPH_TOKEN")
    account_id = os.environ.get("INSTAGRAM_BUSINESS_ACCOUNT_ID")

    if not token or not account_id:
        print("❌ Missing INSTAGRAM_GRAPH_TOKEN or INSTAGRAM_BUSINESS_ACCOUNT_ID")
        sys.exit(1)

    # テスト投稿
    result = upload_video_to_instagram(
        video_url="https://uploads.postiz.com/qv3M9POOXb.mp4",
        caption="🎯 Test post via Instagram Graph API",
        business_account_id=account_id,
        graph_token=token
    )

    print("\n📋 Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
