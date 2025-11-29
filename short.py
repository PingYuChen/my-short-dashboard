import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 頁面設定 ---
st.set_page_config(page_title="亞太短線戰情室", layout="wide")

st.title("📈 亞太短線戰情室 (Asia Momentum Trader)")
st.markdown("### 協助短期投資判斷：美股風向 x 深度個股診斷")

# --- 側邊欄 ---
menu = st.sidebar.radio("功能選單", ["1. 美股收盤分析 (風向球)", "2. 個股全方位診斷 (AI總結版)"])

# --- Helper Functions ---
def calculate_change(current, previous):
    if previous == 0: return 0
    return round((current - previous) / previous * 100, 2)

# ==========================================
# 功能 1: 美股收盤分析
# ==========================================
if menu == "1. 美股收盤分析 (風向球)":
    st.header("🇺🇸 美股收盤後分析")
    st.info("💡 提示：美股是台股的先行指標，觀察費半 (SOX) 與 NVDA 表現至關重要。")

    indices = {'S&P 500': '^GSPC', '納斯達克': '^IXIC', '費城半導體': '^SOX', '恐慌指數': '^VIX'}
    cols = st.columns(4)
    for i, (name, ticker) in enumerate(indices.items()):
        try:
            df = yf.Ticker(ticker).history(period="2d")
            if len(df) >= 2:
                latest = df['Close'].iloc[-1]
                chg = calculate_change(latest, df['Close'].iloc[-2])
                color = "inverse" if name == '恐慌指數' else "normal"
                cols[i].metric(label=name, value=f"{latest:.2f}", delta=f"{chg}%", delta_color=color)
        except:
            cols[i].metric(label=name, value="N/A")

    st.divider()
    st.subheader("🔥 關鍵科技股與 ADR")
    tech_stocks = {'NVIDIA': 'NVDA', '台積電 ADR': 'TSM', 'AMD': 'AMD', '特斯拉': 'TSLA', '蘋果': 'AAPL'}
    tech_cols = st.columns(len(tech_stocks))
    for i, (name, ticker) in enumerate(tech_stocks.items()):
        try:
            t = yf.Ticker(ticker)
            info = t.history(period='2d')
            if len(info) >= 2:
                latest = info['Close'].iloc[-1]
                chg = calculate_change(latest, info['Close'].iloc[-2])
                tech_cols[i].metric(label=name, value=f"${latest:.2f}", delta=f"{chg}%")
        except: pass

# ==========================================
# 功能 2: 個股全方位診斷 (AI總結版)
# ==========================================
elif menu == "2. 個股全方位診斷 (AI總結版)":
    st.header("🔎 個股三維分析儀 (Stock X-Ray Pro)")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        ticker_input = st.text_input("輸入股票代號", value="NVDA") 
        period_input = st.selectbox("分析週期", ["3個月", "6個月", "1年"], index=1)
        
    if st.button("開始深度診斷"):
        with st.spinner(f'AI 正在為您撰寫 {ticker_input} 分析報告...'):
            try:
                # 1. 取得數據
                p_map = {"3個月": "3mo", "6個月": "6mo", "1年": "1y"}
                df = yf.Ticker(ticker_input).history(period=p_map[period_input])
                
                if df.empty:
                    st.error("無法取得數據，請確認代號。")
                else:
                    # 2. 計算技術指標
                    df.ta.sma(length=5, append=True)
                    df.ta.sma(length=10, append=True)
                    df.ta.sma(length=20, append=True)
                    df.ta.sma(length=60, append=True)
                    df.ta.rsi(length=14, append=True)
                    df.ta.stoch(append=True) 
                    df.ta.macd(append=True)
                    df.ta.bbands(length=20, std=2, append=True)
                    
                    # 3. 繪圖
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                        vertical_spacing=0.03, subplot_titles=(f'{ticker_input} 走勢圖', '成交量'),
                                        row_width=[0.2, 0.7])

                    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                    low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
                    
                    if 'SMA_5' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA_5'], line=dict(color='orange', width=1), name='5MA'), row=1, col=1)
                    if 'SMA_20' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='blue', width=1), name='20MA'), row=1, col=1)
                    if 'SMA_60' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA_60'], line=dict(color='green', width=1), name='60MA'), row=1, col=1)
                    
                    if 'BBU_20_2.0' in df.columns:
                        fig.add_trace(go.Scatter(x=df.index, y=df['BBU_20_2.0'], line=dict(color='gray', width=1, dash='dot'), name='布林上緣'), row=1, col=1)
                        fig.add_trace(go.Scatter(x=df.index, y=df['BBL_20_2.0'], line=dict(color='gray', width=1, dash='dot'), fill='tonexty', fillcolor='rgba(200,200,200,0.1)', name='布林下緣'), row=1, col=1)

                    colors = ['red' if row['Open'] - row['Close'] >= 0 else 'green' for index, row in df.iterrows()]
                    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='成交量'), row=2, col=1)

                    fig.update_layout(xaxis_rangeslider_visible=False, height=600, showlegend=True)
                    st.plotly_chart(fig, use_container_width=True)

                    # 4. 深度診斷邏輯
                    latest = df.iloc[-1]
                    prev = df.iloc[-2]
                    
                    rsi = latest.get('RSI_14', 50)
                    k_val = latest.get('STOCHk_14_3_3', 50)
                    d_val = latest.get('STOCHd_14_3_3', 50)
                    macd_hist = latest.get('MACDh_12_26_9', 0)
                    
                    vol_today = latest['Volume']
                    vol_avg = df['Volume'].rolling(5).mean().iloc[-1]
                    vol_ratio = vol_today / vol_avg if vol_avg > 0 else 0
                    
                    close_price = latest['Close']
                    sma5 = latest.get('SMA_5', 0)
                    sma20 = latest.get('SMA_20', 0)
                    sma60 = latest.get('SMA_60', 0)
                    bbu = latest.get('BBU_20_2.0', 0)
                    bbl = latest.get('BBL_20_2.0', 0)

                    # --- 訊號判讀 ---
                    trend_score = 0
                    trend_msg = []
                    
                    if close_price > sma20:
                        trend_msg.append("✅ 站上月線")
                        trend_score += 1
                    else:
                        trend_msg.append("🔻 跌破月線")
                    
                    if sma5 > sma20:
                        trend_msg.append("✅ 均線黃金排列")
                        trend_score += 1
                    
                    if macd_hist > 0:
                        trend_msg.append("✅ MACD 偏多")
                        trend_score += 1
                    else:
                        trend_msg.append("🔻 MACD 偏空")

                    # KD 交叉判斷
                    prev_k = prev.get('STOCHk_14_3_3', 50)
                    prev_d = prev.get('STOCHd_14_3_3', 50)
                    kd_signal = "中性"
                    if k_val > d_val and prev_k < prev_d: kd_signal = "🔥 黃金交叉 (買)"
                    elif k_val < d_val and prev_k > prev_d: kd_signal = "❄️ 死亡交叉 (賣)"

                    # 5. 生成 AI 總結評語
                    ai_comment = ""
                    action_suggestion = ""
                    
                    # (1) 趨勢定調
                    if trend_score == 3:
                        ai_comment += f"目前技術面呈現**極致多頭**格局，股價站穩月線之上，且 MACD 動能充沛。均線呈現多頭排列，顯示主力控盤意願強烈。"
                        action_suggestion = "順勢操作，持股續抱，或沿 5日線 加碼。若未跌破月線前不輕易看空。"
                    elif trend_score == 2:
                        ai_comment += f"目前處於**震盪偏多**格局。雖然趨勢向上，但部分指標出現分歧，顯示多方尚未完全掌控局面。"
                        action_suggestion = "拉回找買點，不建議過度追高。可沿 10日線 或 月線 佈局。"
                    elif trend_score == 1:
                        ai_comment += f"目前處於**多空拉鋸**的整理階段。均線糾結，方向尚未明確，操作難度較高。"
                        action_suggestion = "觀望為主，等待帶量突破或跌破區間後再動作。區間操作者可高出低進。"
                    else:
                        ai_comment += f"目前呈現**空頭弱勢**格局。股價遭月線反壓，且指標偏弱，上方層層套牢賣壓沈重。"
                        action_suggestion = "反彈站在賣方，嚴設停損。空手者不宜輕易接刀，等待底部型態確立。"

                    # (2) 風險/機會提示
                    risk_msg = ""
                    if rsi > 75 or k_val > 80:
                        risk_msg = "⚠️ 需留意**指標嚴重過熱**（RSI/KD 高檔），短線乖離過大，隨時有獲利了結賣壓回測 5日線 的風險。"
                        action_suggestion += " (短線過熱，勿追高)"
                    elif rsi < 25 or k_val < 20:
                        risk_msg = "🟢 指標已進入**超賣區**，且可能出現乖離過大後的技術性反彈。"
                        if kd_signal == "🔥 黃金交叉 (買)":
                            risk_msg += " 加上 KD 低檔黃金交叉，**搶反彈勝率提高**。"
                            action_suggestion = "激進者可嘗試搶短，但需嚴設前低為停損點。"
                    
                    # (3) 量能與通道
                    vol_msg = ""
                    if vol_ratio > 1.5:
                        vol_msg = "今日**爆出巨量**，顯示多空交戰激烈，是變盤訊號。"
                    elif vol_ratio < 0.6:
                        vol_msg = "近期**量能急凍**，市場觀望氣氛濃厚。"
                    
                    bb_msg = ""
                    if close_price > bbu:
                        bb_msg = "股價已**頂到布林上緣**，短線阻力較大。"
                    elif close_price < bbl:
                        bb_msg = "股價已**觸及布林下緣**，短線或有支撐。"

                    # 組裝最終評語
                    final_summary = f"{ai_comment} {risk_msg} {vol_msg} {bb_msg}"

                    # 6. 顯示 UI
                    st.subheader("🤖 AI 綜合戰力評分")
                    
                    # 總分儀表板
                    score_col, summary_col = st.columns([1, 3])
                    
                    with score_col:
                        st.metric(label="多方戰力指數", value=f"{trend_score}/3", delta=kd_signal)
                        st.write(f"RSI: **{rsi:.1f}**")
                        st.write(f"量能比: **{vol_ratio:.2f}x**")
                    
                    with summary_col:
                        st.markdown(f"#### 📝 AI 總結評語")
                        st.info(final_summary)
                        st.markdown(f"**💡 操作建議：** {action_suggestion}")

            except Exception as e:
                st.error(f"分析發生錯誤: {e}")

st.markdown("---")
st.caption("Designed for Professional Traders | AI Summary Version v1.3")