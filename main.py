import os
import requests
import yfinance as yf
import google.generativeai as genai
import feedparser
from datetime import datetime

# 1. 환경 설정
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_market_data():
    # 주요 지표 수집
    tickers = {"나스닥": "^IXIC", "반도체": "^SOX", "환율": "KRW=X", "EWY": "EWY"}
    data_str = ""
    for name, sym in tickers.items():
        d = yf.Ticker(sym).history(period="2d")
        change = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
        data_str += f"{name}: {change:+.2f}% / "
    return data_str

def get_latest_news():
    # 인베스팅닷컴 주요 뉴스 RSS (신뢰도 높은 소스)
    url = "https://www.investing.com/rss/news_25.rss" # 주식 시장 뉴스
    feed = feedparser.parse(url)
    news_titles = [entry.title for entry in feed.entries[:8]] # 최근 8개 뉴스 제목
    return "\n".join(news_titles)

def analyze_with_gemini(data, news):
    prompt = f"""
    너는 전문 주식 분석가야. 아래 미국장 데이터와 주요 뉴스를 보고 한국 시장(KOSPI/KOSDAQ)에 미칠 영향을 분석해줘.
    
    [미국장 데이터]: {data}
    [주요 뉴스]:
    {news}
    
    형식:
    1. 요약: (한 문장)
    2. 국장 영향: (반도체, 2차전지 등 섹터별 전망)
    3. 주의사항: (오늘 조심해야 할 점)
    말투는 친절하고 명확하게 한국어로 작성해줘.
    """
    response = model.generate_content(prompt)
    return response.text

def send_telegram(text):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

if __name__ == "__main__":
    market_data = get_market_data()
    news_headlines = get_latest_news()
    ai_analysis = analyze_with_gemini(market_data, news_headlines)
    
    final_msg = f"🤖 [AI 미국장 분석 리포트]\n\n{ai_analysis}"
    send_telegram(final_msg)