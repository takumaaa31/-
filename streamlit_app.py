import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import time
import re

# --- ページ設定 ---
st.set_page_config(page_title="株スキャナーAI", layout="wide")

# --- 設定（API接続） ---
try:
    # 接続エラーを回避するため、最新の安定版ルート(v1)を指定
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"APIキーの設定エラー: {e}")

st.title("🚀 日米・期待値最高ランク投資エージェント")
st.caption("Gemini 1.5 Flashが市場をスキャンし、独自の視点で分析します。")

# --- メイン処理 ---
if st.button("市場をスキャンして5社選定"):
    # モデル名を最新の安定版に指定
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    with st.status("🔍 AIが銘柄を選定中...", expanded=True) as status:
        st.write("1. 日米市場から有望銘柄をピックアップ中...")
        
        # 銘柄抽出プロンプト
        prompt = "日本株（.T付き）と米国株から、今期待値が高い(SS~A)銘柄を5つ探してください。返信はティッカーのみを「7203.T,NVDA,AAPL」のようにカンマ区切りだけで出力してください。"
        
        try:
            res = model.generate_content(prompt)
            # ティッカーシンボルを抽出
            tickers = re.findall(r'[A-Z0-9\.]+', res.text)
            tickers = [t.strip('.') for t in tickers if t.endswith('.T') or (t.isalpha() and 1<=len(t)<=5)][:5]
            
            if not tickers:
                st.error("銘柄の抽出に失敗しました。もう一度試してください。")
                st.stop()
                
            st.write(f"ターゲット確定: {', '.join(tickers)}")
            
            results = []
            for ticker in tickers:
                st.write(f"📊 {ticker} を個別分析中...")
                try:
                    stock = yf.Ticker(ticker)
                    # 現在値を取得
                    price_val = stock.fast_info['last_price']
                    curr_price = round(price_val, 2) if price_val else "取得不可"
                    
                    analysis_prompt = f"銘柄:{ticker} 現在価格:{curr_price}。この株の期待値(SS~A)、買い目安、理由を2行で書いてください。"
                    analysis_res = model.generate_content(analysis_prompt)
                    
                    results.append({
                        "時刻": datetime.now().strftime("%H:%M"),
                        "銘柄": ticker,
                        "現在値": curr_price,
                        "AI分析": analysis_res.text
                    })
                except Exception:
                    continue
                time.sleep(1) # API制限回避
            
            status.update(label="✅ 全分析完了！", state="complete")
            
            # 結果表示
            st.divider()
            st.subheader("📋 分析結果シート")
            st.table(pd.DataFrame(results))
            st.balloons()
            
        except Exception as e:
            st.error(f"解析中にエラーが発生しました: {e}")

# --- サイドバー ---
with st.sidebar:
    st.info("最終的な投資判断は自己責任で行ってください。")
