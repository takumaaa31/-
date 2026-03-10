import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import time
import re

# --- 設定（StreamlitのSecretsから読み込み） ---
# 事前に詳細設定のSecretsに GEMINI_API_KEY = "..." を入れている前提です
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Secretsに GEMINI_API_KEY が設定されていないようです。詳細設定を確認してください。")

st.set_page_config(page_title="株スキャナーAI", layout="wide")

st.title("🚀 日米・期待値最高ランク投資エージェント")
st.caption("Geminiが市場をスキャンし、期待値の高い5銘柄を独自の視点で分析します。")

# --- メイン処理 ---
if st.button("市場をスキャンして5社選定"):
    model = genai.GenerativeModel('gemini-2.0-flash') # 最新の高速モデルを使用
    
    with st.status("🔍 AIが銘柄を選定中...", expanded=True) as status:
        # 1. 銘柄選定プロンプト
        st.write("1. 日米市場から有望銘柄をピックアップしています...")
        prompt = "日本株（.T付き）と米国株を混ぜて、今テクニカル・ファンダメンタル両面で期待値が高い(ランクSS~A)銘柄を5つ探してください。返信はティッカーのみを「7203.T,NVDA,AAPL」のようにカンマ区切りで出力してください。"
        
        try:
            res = model.generate_content(prompt)
            # ティッカーシンボルを抽出
            tickers = re.findall(r'[A-Z0-9\.]+', res.text)
            # 余計な文字を排除し、最大5つに絞る
            tickers = [t.strip('.') for t in tickers if t.endswith('.T') or (t.isalpha() and 1<=len(t)<=5)][:5]
            
            if not tickers:
                st.error("銘柄の抽出に失敗しました。もう一度試してください。")
                st.stop()
                
            st.write(f"ターゲット確定: {', '.join(tickers)}")
            
            results = []
            # 2. 各銘柄を深掘り分析
            for ticker in tickers:
                st.write(f"📊 {ticker} を個別分析中...")
                try:
                    stock = yf.Ticker(ticker)
                    # 現在値を取得（yfinanceの仕様に合わせて取得）
                    info = stock.fast_info
                    curr_price = round(info['last_price'], 2) if 'last_price' in info else "取得不可"
                    
                    analysis_prompt = f"""
                    銘柄:{ticker} 
                    現在の市場価格:{curr_price}
                    この銘柄の直近の期待値を分析し、以下のフォーマットで出力してください。
                    【判定】ランク(SS, S, A)
                    【目安】買値:◯円 / 売値:◯円 / 損切:◯円
                    【理由】短く2行以内で。
                    """
                    analysis_res = model.generate_content(analysis_prompt)
                    
                    results.append({
                        "時刻":
