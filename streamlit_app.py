import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import time
import re

# --- 設定（StreamlitのSecretsから読み込み） ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Secretsに GEMINI_API_KEY が設定されていないようです。")

st.set_page_config(page_title="株スキャナーAI", layout="wide")
st.title("🚀 日米・期待値最高ランク投資エージェント")

# --- メイン処理 ---
if st.button("市場をスキャンして5社選定"):
    model = genai.GenerativeModel('gemini-pro')
    
    with st.status("🔍 AIが銘柄を選定中...", expanded=True) as status:
        st.write("1. 日米市場から銘柄を抽出中...")
        prompt = "日本株（.T付き）と米国株を混ぜて、期待値が高い銘柄を5つ探してください。返信はティッカーのみを「7203.T,NVDA,AAPL」のように出力してください。"
        
        try:
            res = model.generate_content(prompt)
            tickers = re.findall(r'[A-Z0-9\.]+', res.text)
            tickers = [t.strip('.') for t in tickers if t.endswith('.T') or (t.isalpha() and 1<=len(t)<=5)][:5]
            
            results = []
            for ticker in tickers:
                st.write(f"📊 {ticker} を個別分析中...")
                try:
                    stock = yf.Ticker(ticker)
                    curr_price = stock.fast_info['last_price'] if 'last_price' in stock.fast_info else "N/A"
                    
                    analysis_prompt = f"銘柄:{ticker} 現在価格:{curr_price}。この株の買い時・売り時を1行で判定し、理由を短く書いてください。"
                    analysis_res = model.generate_content(analysis_prompt)
                    
                    # 👈 エラー箇所：ここから下の閉じカッコまでを確実に入れる！
                    results.append({
                        "時刻": datetime.now().strftime("%H:%M"),
                        "銘柄": ticker,
                        "現在値": curr_price,
                        "AI分析結果": analysis_res.text
                    })
                except:
                    continue
                time.sleep(1)
            
            status.update(label="✅ 分析完了！", state="complete")
            st.table(pd.DataFrame(results))
            st.balloons()
            
        except Exception as e:
            st.error(f"エラー: {e}")

# --- サイドバー ---
with st.sidebar:
    st.info("最終判断は自己責任でお願いします。")
