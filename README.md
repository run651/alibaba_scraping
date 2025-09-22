alibabaスクレーパー - 追跡回避（テスト用）


 ✅追跡回避強化
- ステルスモード：高度なブラウザ指紋マスキング
- ランダムユーザーエージェント：現実的なブラウザ署名の回転
- 人間らしい挙動: ランダム待機、スクロール、マウス移動
- 強化ヘッダ：フルブラウザヘッダシミュレーション
- プロキシ対応：プロキシのローテーション機能内蔵
- Captcha検出: ブロッキング機構の自動検出


 📋 インストール

1. 依存関係のインストール:
 bash
py -m pip install -r requirements.txt


2. Playwright ブラウザのインス​​トール:
 bash
py -m playwright install chromium


 🎯 使い方

 GUIモード（推奨）
 bash
py scraper_gui.py


 コマンドラインモード
 bash
py scraper.py


 🔐 2Captcha連携
 2Captcha設定
1. APIキーを取得: `2Captcha.com`からAPIキーを取得する
2. GUIで有効にする：「自動的にCaptchaを解決する」を確認する
3. API キー入力: フィールドに API キーを貼り付ける
4. スクレイピング開始: Captchaは自動的に解決されます
