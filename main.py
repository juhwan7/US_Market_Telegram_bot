import os
import requests
import yfinance as yf
from google import genai # Import 방식을 이렇게 바꿔야 합니다
import feedparser
from datetime import datetime

# 설정
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
# 최신 SDK 클라이언트 초기화
client = genai.Client(api_key=GEMINI_KEY) 

def get_market_data():
    tickers = {
        "나스닥": "^IXIC", "S&P500": "^GSPC", "반도체(SOX)": "^SOX",
        "러셀2000": "^RUT", "VIX(공포지수)": "^VIX", "미10년물금리": "^TNX",
        "원달러환율": "KRW=X", "XLK(기술)": "XLK", "XLF(금융)": "XLF"
    }
    
    data_str = "📊 [전일 주요 지표 및 섹터 등락]\n"
    for name, sym in tickers.items():
        try:
            d = yf.Ticker(sym).history(period="2d")
            if len(d) >= 2:
                current = d['Close'].iloc[-1]
                prev = d['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                data_str += f"- {name}: {current:.2f} ({change:+.2f}%)\n"
        except:
            pass
    return data_str

def get_latest_news():
    url = "https://www.investing.com/rss/news_25.rss"
    try:
        feed = feedparser.parse(url)
        news_titles = [f"- {entry.title}" for entry in feed.entries[:15]]
        return "\n".join(news_titles)
    except:
        return "- 뉴스 수집 실패"

def analyze_with_gemini(data, news):
    prompt = f"""
    너는 기관 투자자 수준의 정보력을 가진 전문 프랍 트레이더야.
    한국 KOSPI/KOSDAQ 시장에서 수급과 차트를 기반으로 매매하는 전문 전업 투자자를 위해 '미장 딥다이브 리포트'를 작성해줘.

    [시장 데이터]: {data}
    [뉴스 헤드라인]: {news}
    
    [필수 포함 내용]
    1. 🌐 글로벌 매크로 분석: 금리, 환율, VIX 변화가 시장에 준 시그널
    2. 🏢 섹터 로테이션: 돈이 어디서 빠져서 어디로 들어갔는가? (XLK, XLF 등 참고)
    3. 🔥 특징주 요약: 변동성이 컸던 미장 종목과 그 이유
    4. 🎯 국장 대응 시나리오: 오늘 시초가 주도 섹터 예측 및 리스크 관리 전략
    
    트레이딩 전문 용어를 사용하고, 매우 상세하고 날카롭게 분석해줘.
    """
    try:
        # 모델명 정확히 입력
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite-preview',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"분석 오류: {e}"

def send_telegram(text):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for i in range(0, len(text), 4000):
        requests.post(url, json={"chat_id": chat_id, "text": text[i:i+4000]})

if __name__ == "__main__":
    now = datetime.now().strftime('%Y-%m-%d')
    market_data = get_market_data()
    news_headlines = get_latest_news()
    ai_report = analyze_with_gemini(market_data, news_headlines)
    
    final_msg = f"🦅 [Pro 트레이더 미장 분석 - {now}]\n\n{ai_report}"
    send_telegram(final_msg)