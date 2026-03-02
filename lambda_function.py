# -*- coding: utf-8 -*-

import os
import sys
import logging
import json

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage,
    FlexSendMessage, PostbackEvent, FollowEvent, SourceUser
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数からアクセストークンとChannel Secretを取得
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)

if channel_secret is None:
    logger.error('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    logger.error('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

# LINE Bot APIとWebhookHandlerのインスタンス化
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# Lambdaのメインハンドラ
def lambda_handler(event, context):
    # CloudWatch Logsに受信したevent全体を出力（デバッグに役立ちます）
    logger.info(json.dumps(event))

    # 署名検証
    signature = event["headers"]["x-line-signature"]
    body = event["body"]

    # Webhookからのイベントを処理
    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        logger.error(f"Got exception from LINE Messaging API: {e.message}\n")
        for m in e.error.details:
            logger.error(f"  {m.property}: {m.message}")
        return {"statusCode": 500, "body": "API Error"}
    except InvalidSignatureError:
        logger.error("Invalid signature. Please check your channel secret.")
        return {"statusCode": 400, "body": "Invalid Signature"}

    # 成功レスポンス
    return {"statusCode": 200, "body": "OK"}


# メッセージイベントの処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    
    # ユーザーIDと表示名を取得してログに出力
    user_id = event.source.user_id
    logger.info(f"受信したユーザーID: {user_id}")
    
    try:
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name
        logger.info(f"ユーザー名: {display_name}")
    except LineBotApiError:
        display_name = "Guest"
        logger.info("ユーザープロフィールの取得に失敗しました。")

    # 受信メッセージ
    send_message = event.message.text

    # 「おすすめのドリンクメニュー」と受信した場合
    if send_message == "おすすめのドリンクメニュー":
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(
                # 【マスキング箇所】実際のS3バケットURLからダミーURLに変更
                original_content_url="https://example.com/path/to/your/cafe_menu.png",
                preview_image_url="https://example.com/path/to/your/cafe_menu.png"
            )
        )
        
    # 「お問い合わせ」と受信した場合
    elif send_message == "お問い合わせ":
        bubble_string = """
        {
          "type": "bubble",
          "header": { "type": "box", "layout": "vertical",
            "contents": [
              { "type": "text", "text": "お問い合わせ", "weight": "bold", "align": "center", "color": "#ffffff" },
              { "type": "text", "text": "以下の質問に該当するものはありますか？タップしてください。", "wrap": true, "color": "#ffffff" }
            ],
            "backgroundColor": "#00CC62"
          },
          "body": { "type": "box", "layout": "vertical",
            "contents": [
              { "type": "box", "layout": "vertical", "contents": [ { "type": "text", "text": "営業時間を教えてください", "align": "center", "color": "#42659a" } ], "action": { "type": "postback", "label": "question", "data": "action=question&id=1", "displayText": "営業時間を教えてください" } },
              { "type": "box", "layout": "vertical", "contents": [ { "type": "text", "text": "場所はどこにありますか？", "color": "#42659a", "align": "center" } ], "margin": "12px", "action": { "type": "postback", "label": "question", "data": "action=question&id=2", "displayText": "場所はどこにありますか？" } },
              { "type": "box", "layout": "vertical", "contents": [ { "type": "text", "text": "駐車場はありますか？", "color": "#42659a", "align": "center" } ], "margin": "12px", "action": { "type": "postback", "label": "question", "data": "action=question&id=3", "displayText": "駐車場はありますか？" } },
              { "type": "box", "layout": "vertical", "contents": [ { "type": "text", "text": "テイクアウトやデリバリーはありますか？", "align": "center", "color": "#42659a" } ], "margin": "12px", "action": { "type": "postback", "label": "question", "data": "action=question&id=4", "displayText": "テイクアウトやデリバリーはありますか？" } }
            ]
          }
        }
        """
        message = FlexSendMessage(alt_text="お問い合わせ", contents=json.loads(bubble_string))
        line_bot_api.reply_message(event.reply_token, message)
        
    # 上記以外のメッセージが来た場合は何もしない
    else:
        logger.info(f"不明なメッセージを受信: {send_message}")


# ポストバックイベントの処理
@handler.add(PostbackEvent)
def handle_postback(event):
    logger.info(f"ポストバックデータ受信: {event.postback.data}")
    if event.postback.data == 'action=question&id=1':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='営業時間は平日8:30~17:00、土日祝は8:30~21:00まで開いております。'))
    elif event.postback.data == 'action=question&id=2':
        # 【補足】Googleマップの短縮URLはそのままでも問題ありません
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='下記リンクからGoogle Mapで確認できます。\nhttps://goo.gl/maps/m2KbyY6RA8QepLaa8'))
    elif event.postback.data == 'action=question&id=3':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='はい、お店の裏に6台分の駐車スペースがございます。また、近隣にコインパーキングもございます。'))
    elif event.postback.data == 'action=question&id=4':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='申し訳ございません。デリバリーやテイクアウトは行っておりません。'))


# フォローイベントの処理
@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    logger.info(f"フォローされました。ユーザーID: {user_id}")
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='ご登録いただきありがとうございます！Cafe BORCELLEのLINE公式アカウントです。\n\n下記Menuからおすすめのドリンクメニュー、クーポン、お問い合わせ、ホームページのリンクが確認できます。\n\n当botと会話をすることはできず、チャットで話しかけても返信は返ってきません。\n\nどうぞご活用くだされば幸いです。')
    )