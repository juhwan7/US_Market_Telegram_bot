import yfinance as yf
import os
import requests

def get_market_data():
    # 가져올 종목 리스트 (나스닥, 반도체지수, 한국ETF, 환율, 10년물 금리)
    tickers = {
        "나스닥": "^IXIC",
        "반도체지수": "^SOX",
        "한국ETF(EWY)": "EWY",
        "원/달러환율": "KRW=X",
        "미10년물금리": "^TNX"
    }
    
    msg = "📢 [미국장 정리 및 국장 전망]\n\n"
    
    for name, ticker in tickers.items():
        data = yf.Ticker(ticker).history(period="2d")
        if len(data) < 2: continue
        
        current = data['Close'].iloc[-1]
        prev = data['Close'].iloc[-2]
        change = ((current - prev) / prev) * 100
        
        emoji = "🔴" if change > 0 else "🔵"
        msg += f"{emoji} {name}: {current:.2f} ({change:+.2f}%)\n"
    
    return msg

# 텔레그램 전송 함수 (기존과 동일)
def send_telegram(text):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

if __name__ == "__main__":
    report = get_market_data()
    send_telegram(report)