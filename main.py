import os
import requests
import yfinance as yf
import google.generativeai as genai
import feedparser
import time
from datetime import datetime

# 1. 설정
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)

def get_market_data():
    tickers = {
        "나스닥": "^IXIC", "S&P500": "^GSPC", "반도체(SOX)": "^SOX",
        "VIX(공포)": "^VIX", "미10년물금리": "^TNX", "원달러환율": "KRW=X",
        "XLK(기술)": "XLK", "XLF(금융)": "XLF", "XLE(에너지)": "XLE"
    }
    data_str = "📊 [시장 주요 지표]\n"
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
    urls = [
        "https://finance.yahoo.com/news/rssindex",
        "https://search.cnbc.com/rs/search/all/view.rss?partnerId=2000&keywords=stock%20market"
    ]
    news = []
    for url in urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                news.append(f"📌 {entry.title}")
        except: continue
    return "\n".join(news) if news else "뉴스 수집 실패"

def analyze_with_gemini(data, news):
    # 확인된 모델 리스트 중 최적의 조합 (models/ 경로 포함 필수)
    model_priority = [
        'models/gemini-3.1-pro-preview', 
        'models/gemini-2.5-pro',
        'models/gemini-3.1-flash-lite-preview'
    ]
    
    prompt = f"""
    너는 기관 투자자 수준의 분석력을 가진 전문 프랍 트레이더야.
    아래 데이터를 바탕으로 오늘 한국 시장(KOSPI/KOSDAQ)의 대응 시나리오를 매우 상세하게 작성해줘.

    [시장 지표]: {data}
    [해외 뉴스]: {news}
    
    분석에 포함할 내용:
    - 매크로 환경(금리, 환율)이 국장 수급에 주는 시그널
    - 미장 섹터 로테이션에 따른 오늘 국장 주도 테마(반도체, 2차전지 등) 예측
    - 트레이더가 오늘 장 중 반드시 체크해야 할 리스크 포인트
    """
    
    for m_name in model_priority:
        for attempt in range(2): # 각 모델당 2번씩 시도
            try:
                print(f"🚀 {m_name} 모델로 분석 시작...")
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"⚠️ {m_name} 실패: {e}")
                time.sleep(5) # 5초 대기 후 재시도 또는 다음 모델로
                
    return "❌ 모든 AI 모델이 응답하지 않습니다. 지표 데이터를 직접 확인하세요."

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