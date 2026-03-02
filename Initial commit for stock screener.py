pip install yfinance pandas pandas_ta
import yfinance as yf
import pandas as pd
import pandas_ta as ta

def screen_hk_stocks(ticker_list):
    results = []

    for ticker in ticker_list:
        try:
            # 獲取數據 (需要足夠長度計算 SMA50 和 前浪頂)
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            info = stock.info
            
            if len(df) < 50: continue

            score = 0
            status = ""

            # --- 指標計算 ---
            # Level 1: RSI
            df['RSI'] = ta.rsi(df['Close'], length=14)
            current_rsi = df['RSI'].iloc[-1]

            # Level 2: 布林線 (頂/中/底)
            bbands = ta.bbands(df['Close'], length=20, std=2)
            upper = bbands['BBU_20_2.0'].iloc[-1]
            mid = bbands['BBM_20_2.0'].iloc[-1]
            lower = bbands['BBL_20_2.0'].iloc[-1]
            price = df['Close'].iloc[-1]

            # Level 3: MACD
            macd = ta.macd(df['Close'])
            macd_val = macd['MACD_12_26_9'].iloc[-1]
            signal_val = macd['MACDs_12_26_9'].iloc[-1]

            # Level 4: 市值 & 前浪頂 (用過去一年最高價作為浪頂)
            market_cap = info.get('marketCap', 0)
            prev_peak = df['Close'].max()
            dist_to_peak = (prev_peak - price) / prev_peak

            # Level 5: SMA
            sma10 = ta.sma(df['Close'], length=10).iloc[-1]
            sma20 = ta.sma(df['Close'], length=20).iloc[-1]
            sma50 = ta.sma(df['Close'], length=50).iloc[-1]

            # --- 評分邏輯 ---
            
            # Level 1: RSI
            if current_rsi > 70: score += 2
            elif current_rsi > 50: score += 1
            else: continue # 弱勢直接跳過

            # Level 2: 價格位置
            if price >= upper: score += 2
            elif price >= mid: score += 1
            elif price < lower: continue # 弱勢直接跳過

            # Level 3: MACD
            if macd_val > 0:
                if macd_val > signal_val: score += 2
                else: score += 1
            else: continue # 弱勢

            # Level 4: 市值與浪頂
            if market_cap >= 2_000_000_000: # 20億
                if dist_to_peak < 0.15: score += 2
                else: continue
            else: continue

            # Level 5: SMA 排列
            if sma10 > sma20:
                if sma10 > sma50 and sma20 > sma50: score += 2
                elif sma10 > sma50 and sma20 < sma50: score += 1
                else: continue
            else: continue

            # --- 最終判定 ---
            if score >= 10: status = "🔥 超級強勢"
            elif score >= 8: status = "💪 強勢"
            elif score == 5: status = "⚖️ 合格普通"
            else: status = "☁️ 弱勢/不合格"

            results.append({
                '代號': ticker,
                '現價': round(price, 2),
                '總分': score,
                '狀態': status,
                'RSI': round(current_rsi, 1),
                '市值(億)': round(market_cap / 100_000_000, 2)
            })

        except Exception as e:
            print(f"無法分析 {ticker}: {e}")

    return pd.DataFrame(results)

# --- 測試運行 ---
# 港股代碼格式為 "數字.HK"，例如騰訊是 0700.HK
test_tickers = ["0700.HK", "3690.HK", "9988.HK", "1211.HK", "2800.HK", "0005.HK", "1810.HK"]
final_list = screen_hk_stocks(test_tickers)

print(final_list.sort_values(by='總分', ascending=False))
