import os
import requests
import yfinance as yf
import google.generativeai as genai
import feedparser
from datetime import datetime

# 설정
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)
# 지정하신 최신/초고속 모델 적용
model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

def get_market_data():
    # 지수뿐만 아니라 섹터별 자금 흐름을 파악하기 위해 주요 ETF 추가
    tickers = {
        "나스닥": "^IXIC", "S&P500": "^GSPC", "반도체(SOX)": "^SOX",
        "러셀2000": "^RUT", "VIX(공포지수)": "^VIX", "미10년물금리": "^TNX",
        "원달러환율": "KRW=X",
        "XLK(기술)": "XLK", "XLF(금융)": "XLF", 
        "XLE(에너지)": "XLE", "XLV(헬스케어)": "XLV"
    }
    
    data_str = "📊 [전일 종가 및 등락률]\n"
    for name, sym in tickers.items():
        try:
            d = yf.Ticker(sym).history(period="2d")
            if len(d) >= 2:
                current = d['Close'].iloc[-1]
                prev = d['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                data_str += f"- {name}: {current:.2f} ({change:+.2f}%)\n"
        except Exception as e:
            pass
    return data_str

def get_latest_news():
    # 뉴스 표본을 15개로 늘려 디테일한 시장 이슈 포착
    url = "https://www.investing.com/rss/news_25.rss"
    try:
        feed = feedparser.parse(url)
        news_titles = [f"- {entry.title}" for entry in feed.entries[:15]]
        return "\n".join(news_titles)
    except:
        return "- 뉴스 데이터를 불러오지 못했습니다."

def analyze_with_gemini(data, news):
    prompt = f"""
    너는 기관 투자자 수준의 정보력을 가진 탑티어 주식 시황 분석가이자 프랍 트레이더야.
    이 리포트를 읽는 사람은 한국 KOSPI/KOSDAQ 시장에서 수급과 차트를 기반으로 데이트레이딩 및 스윙 매매를 하는 '전문 전업 투자자'야.
    초보자용의 단순하고 피상적인 요약은 절대 사절하며, 투자자가 아침 1시간 동안 직접 외신을 뒤지고 섹터 흐름을 분석하는 수고를 완벽히 대체할 수 있는 '심층적이고 전문적인 분석 리포트'를 작성해야 해.

    [오늘의 시장 로우 데이터]:
    {data}
    
    [주요 외신 헤드라인(15개)]:
    {news}
    
    위 데이터를 바탕으로 아래 양식에 맞춰 매우 상세하고 깊이 있게 분석해줘.

    [리포트 양식]
    1. 🌐 글로벌 매크로 & 시장 심리
       - 간밤 주요 매크로 이벤트가 시장에 미친 구체적 영향 (헤드라인 뉴스 기반)
       - 국채 금리, VIX, 환율의 움직임이 시사하는 시장의 숨은 의도

    2. 🏢 섹터별 자금 흐름 (Sector Rotation)
       - 시장을 주도한 강세 섹터와 그 상승의 근본적/개별적 명분
       - 자금이 이탈한 약세/소외 섹터와 하락 이유 (XLK, XLF 등 ETF 데이터 참고)

    3. 🔥 핵심 특징주 리포트 (Key Movers)
       - 유의미한 거래대금이나 변동성을 보인 미장 특징주 분석 (상/하락 사유 및 모멘텀)

    4. 🎯 국내 시장(KOSPI/KOSDAQ) 트레이딩 시나리오
       - 미장 수급 흐름을 국장에 적용 시, 오늘 시초가에 돈이 몰릴 '구체적인 테마와 섹터'
       - 외국인/기관의 매도세가 우려되는 리스크 섹터
       - 당일 단기 매매 관점에서의 핵심 대응 전략 및 주의사항

    어투는 군더더기 없이 단호하고 객관적이며, '실제 트레이더들이 사용하는 실전 용어(수급, 갭상승, 차익실현, 모멘텀 등)'를 적극적으로 사용해줘.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 분석 중 오류 발생: {e}"

def send_telegram(text):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # 텔레그램은 메시지가 너무 길면 잘릴 수 있으므로 4000자 단위로 잘라서 보냄
    for i in range(0, len(text), 4000):
        requests.post(url, json={"chat_id": chat_id, "text": text[i:i+4000]})

if __name__ == "__main__":
    now = datetime.now().strftime('%Y-%m-%d')
    market_data = get_market_data()
    news_headlines = get_latest_news()
    
    ai_analysis = analyze_with_gemini(market_data, news_headlines)
    
    final_msg = f"🦅 [Pro 트레이더를 위한 미장 딥다이브 리포트 - {now}]\n\n{ai_analysis}"
    send_telegram(final_msg)
