import os
import requests
import yfinance as yf
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold # 필터 해제용
import feedparser
import time
from datetime import datetime

# 1. 설정
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)

def get_market_data():
    print("▶️ 1단계: 시장 데이터 수집 중...")
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
    print("▶️ 2단계: 최신 뉴스 수집 중...")
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
    model_name = 'models/gemini-2.5-flash'    

    prompt = f"""
    너는 실전 경험이 풍부하고 핵심만 짚어주는 친절한 주식 시황 분석가야.
    이 글을 읽는 사람은 한국 주식(KOSPI/KOSDAQ)을 매매하는 성인 투자자야. 
    불필요한 서론/결론은 빼고, 텔레그램 HTML 태그를 사용해서 모바일 가독성을 극대화해줘.
    
    [작성 핵심 규칙]
    1. 강조할 문장이나 핵심 요약, 종목명 등은 <b>텍스트</b> 태그로 굵게 처리해. (주의: 터치 복사 기능이 있는 <code> 태그는 절대 쓰지 마)
    2. 어려운 전문 용어는 직관적이고 쉬운 일상어로 바꿔서 설명하거나, 옆에 괄호로 뜻을 달아줘.
    3. 엔터(줄바꿈)를 넉넉히 쓰고, 시각적으로 깔끔하게 기호(■, ▶, 💡, 🎯, ⚠️, ✅ 등)를 적절히 배치해.
    4. 줄바꿈을 할 때 절대 <br>이나 <p> 같은 HTML 태그를 쓰지 말고, 실제 엔터키로 줄바꿈을 해.

    [어젯밤 미국 시장 데이터]: {data}
    [미국 시장 주요 뉴스]: {news}

    아래 양식에 맞춰서 리포트를 작성해:

    <b>■ 1. 간밤 미장 핵심 요약</b>
    ▶ <b>시장 흐름</b>: (미장 상승/하락의 진짜 이유를 쉬운 말로 요약)
    ▶ <b>숨은 의미</b>: (금리/환율 등의 움직임이 투자자에게 주는 시그널 쉽게 풀이)

    <b>■ 2. 돈이 몰린 섹터와 특징주</b>
    ▶ <b>강세 섹터</b>: (왜 올랐는지 쉬운 말로 설명)
    ▶ <b>약세 섹터</b>: (왜 내렸는지 설명)
    💡 <b>국장 연결 고리</b>: (미장 흐름이 우리나라 특정 테마에 어떤 영향을 줄지 분석)

    <b>■ 3. 오늘 국장 대응 전략</b>
    🎯 <b>관심 집중 테마</b>: (오늘 시초가부터 돈이 몰릴 섹터와 이유)
    ⚠️ <b>주의 및 관망</b>: (수급이 꼬일 수 있어 피해야 할 섹터)
    ✅ <b>오늘의 매매 팁</b>: (오늘 장에서 취해야 할 전반적인 매매 스탠스와 주의점)
    """
    
    for attempt in range(3):
        try:
            print(f"▶️ 3단계: {model_name} AI 분석 중... ({attempt + 1}/3)")
            model = genai.GenerativeModel(model_name)
            
            # 🚨 보안 추가: 30초 안에 응답 안 하면 강제로 끊고 에러 처리!
            response = model.generate_content(
                prompt,
                request_options={"timeout": 30}, # 타임아웃 설정
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            print("✅ AI 분석 완료!")
            return response.text
        except Exception as e:
            # 30초가 지나면 여기서 강제로 에러를 뱉어냅니다.
            print(f"⚠️ AI 분석 에러 발생 (응답 지연 등): {e}") 
            if attempt < 2:
                print("⏳ 10초 대기 후 다시 시도합니다...")
                time.sleep(10)
            else:
                return f"❌ 3번 재시도했으나 서버 무응답으로 분석 실패: {e}"
def send_telegram(text):
    print("▶️ 4단계: 텔레그램 전송 중...")
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # 🚨 핵심 방어막: AI가 마음대로 넣은 금지 태그(<br> 등)를 일반 줄바꿈(\n)으로 청소!
    safe_text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n").replace("</br>", "\n")
    
    for i in range(0, len(safe_text), 4000):
        # 1차 시도: 예쁜 HTML 디자인 적용해서 보내기
        payload = {
            "chat_id": chat_id, 
            "text": safe_text[i:i+4000],
            "parse_mode": "HTML"
        }
        res = requests.post(url, json=payload)
        
        if res.status_code == 200:
            print("✅ 텔레그램 메시지 전송 성공!")
        else:
            print(f"⚠️ HTML 전송 거부됨! 이유: {res.text}")
            print("🔄 일반 텍스트 모드로 안전하게 재시도합니다...")
            
            # 2차 시도: 에러가 나면 디자인(HTML) 옵션을 빼고 순수 글자만 강제 전송
            payload.pop("parse_mode", None)
            res_retry = requests.post(url, json=payload)
            
            if res_retry.status_code == 200:
                print("✅ 일반 텍스트로 전송 성공!")
            else:
                print(f"❌ 텔레그램 전송 완전 실패! 이유: {res_retry.text}")

if __name__ == "__main__":
    m_data = get_market_data()
    n_data = get_latest_news()
    report = analyze_with_gemini(m_data, n_data)
    final_msg = f"🦅 [미장 마감 브리핑 - {datetime.now().strftime('%Y-%m-%d')}]\n\n{report}"    
    send_telegram(final_msg)
    print("🏁 모든 작업이 종료되었습니다.")

