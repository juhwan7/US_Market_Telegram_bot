import yfinance as yf
import os
import requests
from datetime import datetime

def get_market_summary():
    # 1. 수집할 종목 (국내 증시 영향 지표)
    tickers = {
        "나스닥": "^IXIC",
        "필라델피아 반도체": "^SOX",  # 국장 반도체주 영향
        "한국 ETF (EWY)": "EWY",      # 외인 수급 예측
        "원/달러 환율": "KRW=X",      # 자금 유출입 지표
        "미 10년물 금리": "^TNX",     # 성장주 영향
        "엔비디아": "NVDA"            # AI 반도체 대장주
    }
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    msg = f"📊 [미국장/매크로 요약] {now}\n\n"
    
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="2d")
            
            if len(df) >= 2:
                current = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                change_pct = ((current - prev) / prev) * 100
                
                emoji = "🔴" if change_pct > 0 else "🔵"
                msg += f"{emoji} {name}: {current:,.2f} ({change_pct:+.2f}%)\n"
            else:
                msg += f"⚪ {name}: 데이터 수집 불가\n"
        except Exception as e:
            msg += f"⚠️ {name}: 에러 발생\n"
            
    msg += "\n💡 국장 팁: 반도체 지수와 EWY가 상승하면 코스피 상승 확률이 높습니다."
    return msg

def send_telegram(text):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    try:
        response = requests.post(url, json={"chat_id": chat_id, "text": text})
        print(f"전송 상태: {response.status_code}")
    except Exception as e:
        print(f"전송 에러: {e}")

if __name__ == "__main__":
    report = get_market_summary()
    send_telegram(report)