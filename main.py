import os
import requests
import yfinance as yf
import google.generativeai as genai
import feedparser
import time
from datetime import datetime

# 1. 설정 (GitHub Secrets에서 가져옴)
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)

def get_market_data():
    # 지수 및 섹터 ETF 데이터 수집
    tickers = {
        "나스닥": "^IXIC", "S&P500": "^GSPC", "반도체(SOX)": "^SOX",
        "VIX(공포)": "^VIX", "미10년물금리": "^TNX", "원달러환율": "KRW=X",
        "XLK(기술)": "XLK", "XLF(금융)": "XLF"
    }
    data_str = "📊 [전일 주요 지표]\n"
    for name, sym in tickers.items():
        try:
            d = yf.Ticker(sym).history(period="2d")
            if len(d) >= 2:
                current, prev = d['Close'].iloc[-1], d['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                data_str += f"- {name}: {current:.2f} ({change:+.2f}%)\n"
        except: continue
    return data_str

def get_latest_news():
    # Yahoo Finance 및 CNBC 뉴스 수집
    urls = ["https://finance.yahoo.com/news/rssindex", "https://search.cnbc.com/rs/search/all/view.rss?partnerId=2000&keywords=stock%20market"]
    news = []
    for url in urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                news.append(f"📌 {entry.title}")
        except: continue
    return "\n".join(news) if news else "뉴스 수집 실패"

def analyze_with_gemini(data, news):
    # 우리가 방금 조회한 리스트 중 가장 똑똑한 모델들로 구성
    model_priority = [
        'models/gemini-3.1-pro-preview', 
        'models/gemini-2.5-pro',
        'models/gemini-1.5-pro'
    ]
    
    prompt = f"""
    너는 전문 프랍 트레이더야. 국장 트레이더를 위한 심층 분석 리포트를 작성해.
    [데이터]: {data}
    [뉴스]: {news}
    [요청]: 글로벌 매크로 분석, 섹터 로테이션, 특징주, 국장 시나리오(반도체/2차전지 등)를 전문 용어를 써서 매우 상세하게 분석해줘.
    """
    
    for m_name in model_priority:
                print(f"🚀 {m_name} 모델로 분석 시작...")
        try:
            print(f"🚀 {m_name} 분석 시도...")
            model = genai.GenerativeModel(m_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"⚠️ {m_name} 실패: {e}")
            time.sleep(2)
            continue
    return "❌ AI 분석 실패"

def send_telegram(text):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for i in range(0, len(text), 4000):
        requests.post(url, json={"chat_id": chat_id, "text": text[i:i+4000]})

if __name__ == "__main__":
    m_data = get_market_data()
    n_data = get_latest_news()
    report = analyze_with_gemini(m_data, n_data)
    final_msg = f"🦅 [Pro 트레이더 분석 - {datetime.now().strftime('%Y-%m-%d')}]\n\n{report}"
    send_telegram(final_msg)