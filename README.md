【業務効率化】Googleフォーム・LINE API連携 自動通知システム

【概要】
Googleフォームで受け付けた回答データを、担当者のLINEグループへリアルタイムで自動通知するシステムです。
GASを用いたデータ転送処理をメインとしつつ、開発・環境構築段階においてAWS Lambdaを利用してLINE Webhookを受信する環境を構築し、システム間連携を行っています。


【システム構成・使用技術】
・メイン処理　　　 ：Google Apps Script
・フロントエンド　 ：Google Forms, Google Sheets
・Webhook受信・解析：AWS Lambda, Amazon API Gateway, Python
・外部API　　　　  ：LINE Messaging API (line-bot-sdk)


【システムアーキテクチャと構築手順】
本システムは、以下の手順・アーキテクチャで構築されています。


①Webhook受信環境の構築とグループIDの取得（AWS Lambda）

LINEの仕様上、通知先となる「グループID」はアプリ上から確認できないため、以下の手順で取得環境を構築しました。
1. AWS Lambda上にPython環境を構築し、API Gatewayと連携してWebhookエンドポイントを作成。
2. 対象のLINEグループにBotアカウントを招待し、テストメッセージを送信。
3. Lambda関数（lambda_function.py）でイベントを受信し、CloudWatch Logsに出力されたJSONデータから対象の group_id を抽出。



②通知システムのメイン処理（GAS）

取得したグループIDを用いて、メインの通知処理を実装しています。
1. ユーザーがGoogleフォームから回答を送信し、スプレッドシートに記録。
2. スプレッドシートの更新をトリガーにGAS（line_notify.gs）が起動。
3. GASからLINE Messaging APIへPOSTリクエストを送信し、指定したLINEグループへ回答内容を通知。



【工夫点・意識した点】
セキュアな設計と環境変数の活用：LINEのアクセストークンやグループIDなどの機密情報は、ソースコード内に直接記述せず、GASの「スクリプトプロパティ」に格納して呼び出すセキュアな設計を徹底しました。
課題解決のためのインフラ活用  ：開発に必要なパラメータ（グループID）を取得するためだけに留まらず、AWS Lambdaを用いたサーバーレスなWebhook受信環境を自力で構築・デプロイし、課題を解決しました。
デプロイパッケージの適切な管理：AWS Lambdaの標準環境には含まれない外部ライブラリ（line-bot-sdk 等）を利用するため、ローカル環境で pip install -t . を用いて依存パッケージを収集し、ZIP化してデプロイを行いました。

---
※セキュリティ保護のため、本リポジトリで公開しているソースコード内の各種トークンやID、URL等はダミー文字列に変更しております。
