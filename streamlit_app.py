import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import re
import time

# 1. 接続設定（余計なオプションをすべて排除）
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Secretsの設定を確認してください")

st.title("🚀 株スキャンAIエージェント")

if st.button("市場をスキャン"):
    # 2. モデル名を最も標準的なものに
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    with st.status("分析中...") as status:
        try:
            # 3. 銘柄選定
            res = model.generate_content("日本株（.T付き）と米国株から、今期待値が高い銘柄を5つ探してください。返信はティッカーのみを「7203.T,NVDA」のようにカンマ区切りで。")
            tickers = re.findall(r'[A-Z0-9\.]+', res.text)
            tickers = [t.strip('.') for t in tickers if t.endswith('.T') or (t.isalpha())][:5]
            
            st.write(f"ターゲット: {', '.join(tickers)}")
            
            # 4. 株価取得と分析
            results = []
            for t in tickers:
                stock = yf.Ticker(t)
                price = stock.history(period="1d")['Close'].iloc[-1] if not stock.history(period="1d").empty else 0
                
                ans = model.generate_content(f"{t}は買いですか？理由を1行で。")
                results.append({"銘柄": t, "価格": round(price, 2), "AI判断": ans.text})
                time.sleep(1)
            
            st.table(pd.DataFrame(results))
            status.update(label="完了！", state="complete")
            st.balloons()
        except Exception as e:
            st.error(f"エラー内容: {e}")
