from flask import Flask, request, jsonify
import mysql.connector
import json
import hmac
import hashlib
import base64
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import feedparser

app = Flask(__name__)

# 設置資料庫連接
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="sgk.Vp]!3zqbbv@M",
    database="line_bot2_db"
)

cursor = db.cursor()

# 使用環境變量來設置LINE Bot API和Secret
line_bot_api = LineBotApi(os.environ.get('CHANNEL_ACCESS_TOKEN'))
channel_secret = os.environ.get('CHANNEL_SECRET')
handler = WebhookHandler(channel_secret)

# 用戶註冊處理器
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    sydrom = data['sydrom']
    email = data['email']

    try:
        cursor.execute(
            "INSERT INTO users (username, sydrom, email) VALUES (%s, %s, %s)",
            (username, sydrom, email)
        )
        db.commit()
        return jsonify({'message': '用戶資料登錄成功'})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)})

# LINE Bot webhook處理
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # 獲取請求的JSON主體
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 驗證請求的來源
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return 'Invalid signature', 400

    return 'OK', 200

# 處理文本消息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    tk = event.reply_token

    if msg == '@註冊會員':
        form_text = "請提供您的資訊，格式如下：\nusername:<你的名字>, sydrom:<症狀>, email:<你的信箱>"
        line_bot_api.reply_message(tk, TextSendMessage(text=form_text))
    elif msg.startswith("username:"):
        try:
            # 假設用戶輸入格式為：username:Name, sydrom:Symptoms, email:Email
            parts = msg.split(',')
            if len(parts) == 3:
                username = parts[0].split(":")[1].strip()
                sydrom = parts[1].split(":")[1].strip()
                email = parts[2].split(":")[1].strip()

                # 插入資料到資料庫
                cursor.execute(
                    "INSERT INTO users (username, sydrom, email) VALUES (%s, %s, %s)",
                    (username, sydrom, email)
                )
                db.commit()

                line_bot_api.reply_message(tk, TextSendMessage(text="您的資料已成功儲存！"))
            else:
                line_bot_api.reply_message(tk, TextSendMessage(text="請提供正確的格式：username:Name, sydrom:Symptoms, email:Email"))
        except Exception as e:
            print(f'Error occurred: {e}')
            line_bot_api.reply_message(tk, TextSendMessage(text="發生錯誤，請稍後再試。"))
    elif msg == "@附近醫療機構":
        google_maps_url = "https://www.google.com/maps/search/?api=1&query=hospitals&query"
        line_bot_api.reply_message(tk, TextSendMessage(text=f"請點擊以下連結來查看附近的醫療機構：\n{google_maps_url}"))
    elif msg == "@衛生署公告":
        feed_url = "https://www.mohw.gov.tw/rss-16-1.html"
        feed = feedparser.parse(feed_url)
        announcements = []
        for entry in feed.entries[:5]:  # 只取前5則公告
            title = entry.title
            link = entry.link
            announcements.append(f"{title}\n{link}")
        line_bot_api.reply_message(tk, TextSendMessage(text="\n\n".join(announcements)))
    else:
        line_bot_api.reply_message(tk, TextSendMessage(text=msg))

if __name__ == "__main__":
    app.run(port=5000, debug=True)
