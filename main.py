import os
import requests

# GitHub Secrets에서 토큰과 아이디를 불러옵니다.
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, json=payload)

# 1. 여기서 미국장 데이터를 수집/정리하는 코드를 작성합니다.
market_summary = "오늘의 미국장 요약: 나스닥 상승, S&P 500 보합..." # (예시)

# 2. 정리된 텍스트를 텔레그램으로 전송합니다.
send_telegram_message(market_summary)
