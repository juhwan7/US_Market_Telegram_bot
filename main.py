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
    # 캡처 화면에서 확인된 할당량이 있는 정확한 모델명
    model_name = 'models/gemini-3.1-flash-lite-preview'
    
    prompt = f"""
    너는 주식 시장의 복잡한 뉴스와 데이터를 초등학생도 이해할 수 있을 만큼 아주 쉽고 친절하게 설명해주는 똑똑한 주식 선생님이야.
    어려운 전문 용어(예: 밸류에이션, 리레이팅, 매크로 등)나 불필요한 기호는 절대 쓰지 말고, 가독성 좋게 작성해줘.
    단순히 사실만 전달하지 말고, '이게 무슨 뜻인지' 그리고 '우리나라 주식 시장(특히 반도체, 2차전지 등)에 어떤 영향을 주는지' 꼭 풀어서 설명해줘야 해.

    [어젯밤 미국 시장 데이터]: {data}
    [미국 시장 주요 뉴스]: {news}

    아래 양식에 맞춰서 작성해줘:

    1. 🌍 간밤에 미국에서는 무슨 일이 있었을까?
    - (미국장이 왜 올랐는지 혹은 내렸는지 아주 쉬운 말로 요약)
    - 💡 이게 무슨 뜻이냐면: (이 상황이 의미하는 바를 초등학생에게 설명하듯 쉽게 풀이)
    - 🇰🇷 우리나라 시장에는 이런 영향을 줘요: (오늘 국장에 미칠 영향)

    2. 💰 어제 미국에서 가장 인기 있었던 주식은?
    - (어떤 회사나 분야에 돈이 많이 몰렸는지 쉬운 말로 설명)
    - 💡 이게 무슨 뜻이냐면: (왜 사람들이 그 주식을 샀는지 쉽게 풀이)
    - 🇰🇷 우리나라 시장에는 이런 영향을 줘요: (오늘 국장에서 어떤 테마/종목을 눈여겨봐야 하는지 연결해서 설명)

    3. 🎯 그래서 오늘 우리는 어떻게 해야 할까?
    - (오늘 한국 주식 시장에서 조심해야 할 점과, 관심 있게 지켜봐야 할 부분을 동화책 읽어주듯 쉽고 명확하게 설명)
    """
    
    # 끈질긴 재시도 로직 (최대 3번 시도, 중간에 10초씩 지연)
    for attempt in range(3):
        try:
            print(f"🚀 {model_name} 로 분석 시도 중... ({attempt + 1}/3)")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"⚠️ 에러 발생: {e}")
            if attempt < 2:
                print("⏳ 서버 안정화를 위해 10초 대기 후 다시 시도합니다...")
                time.sleep(10)
            else:
                return f"❌ 3번 재시도했으나 분석 실패: {e}"

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