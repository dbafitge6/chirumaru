# Noto Sans JP フォントセットアップ

自動ダウンロードに失敗した場合、以下の手順で手動セットアップしてください。

## macOS でのダウンロード

### 方法 1: ブラウザでダウンロード

1. 以下の URL を開く
   - Regular: https://www.fontspace.com/download/family/noto-sans-jp
   - または Google Fonts: https://fonts.google.com/noto/specimen/Noto+Sans+JP

2. `NotoSansJP-Regular.ttf` をダウンロード
3. `NotoSansJP-Bold.ttf` をダウンロード
4. このディレクトリ (`assets/fonts/`) に配置

### 方法 2: Homebrew で cask インストール

```bash
brew tap homebrew/cask-fonts
brew install font-noto-sans-jp
# インストール後、フォントをこのディレクトリにコピー
cp /Library/Fonts/NotoSansJP-*.ttf ./
```

### 方法 3: コマンドラインでダウンロード（wget 使用）

```bash
cd /Users/kobayashikazuya/chirumaru-repo/assets/fonts/
wget https://github.com/google/noto-fonts/raw/main/hinted/NotoSansJP-Regular.ttf
wget https://github.com/google/noto-fonts/raw/main/hinted/NotoSansJP-Bold.ttf
```

## Linux (GitHub Actions)

GitHub Actions で実行する場合、以下をワークフロー内に追加：

```yaml
- name: Install Noto Sans JP
  run: |
    mkdir -p assets/fonts
    curl -L https://www.fontspace.com/download/family/noto-sans-jp \
      -o /tmp/noto.zip
    unzip -j /tmp/noto.zip "*.ttf" -d assets/fonts/
```

またはシステムパッケージを使用：

```yaml
- name: Install Fonts
  run: |
    sudo apt-get update
    sudo apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra
    mkdir -p assets/fonts
    cp /usr/share/fonts/opentype/noto/NotoSansJP-*.otf assets/fonts/
    # OTF を TTF に変換 (fontforge を使用)
```

## フォントが見つからない場合

スクリプトは自動的にシステムフォントにフォールバックしますが、
Linux 環境ではフォントが存在せず、文字が豆腐になる可能性があります。

その場合は、このファイルの手順に従い、フォントを手動で配置してください。
