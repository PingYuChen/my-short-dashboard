import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 頁面設定 (手機優化) ---
st.set_page_config(page_title="短線操作", layout="wide", initial_sidebar_state="collapsed")

st.title("📱 短線操作 (Smart Trader)")
st.caption("AI 驅動的台美股資金流向與技術分析 | V1.7 旗艦版")

# --- 側邊欄 ---
menu = st.sidebar.radio("功能選單", ["1. 市場大盤戰情 (美/台)", "2. 個股全方位診斷"])

# --- Helper Functions ---
def calculate_change(current, previous):
    if previous == 0: return 0
    return round((current - previous) / previous * 100, 2)

# ==========================================
# 功能 1: 市場大盤戰情
# ==========================================
if menu == "1. 市場大盤戰情 (美/台)":
    
    tab_us, tab_tw = st.tabs(["🇺🇸 美股總結", "🇹🇼 台股總結"])

    # --- Tab 1: 美股 ---
    with tab_us:
        st.subheader("🇺🇸 美股收盤 AI 戰情")
        
        market_data = {}
        indices = {'道瓊': '^DJI', '那斯達克': '^IXIC', '費半': '^SOX', 'VIX': '^VIX'}
        
        c1, c2 = st.columns(2)
        
        for i, (name, ticker) in enumerate(indices.items()):
            col = c1 if i % 2 == 0 else c2
            try:
                df = yf.Ticker(ticker).history(period="2d")
                if len(df) >= 2:
                    latest = df['Close'].iloc[-1]
                    chg = calculate_change(latest, df['Close'].iloc[-2])
                    market_data[name] = {'change': chg}
                    color = "inverse" if name == 'VIX' else "normal"
                    col.metric(label=name, value=f"{latest:.0f}", delta=f"{chg}%", delta_color=color)
            except:
                col.metric(label=name, value="N/A")
        
        try:
            nvda = yf.Ticker('NVDA').history(period='2d')
            tsm = yf.Ticker('TSM').history(period='2d')
            nvda_chg = calculate_change(nvda['Close'].iloc[-1], nvda['Close'].iloc[-2])
            tsm_chg = calculate_change(tsm['Close'].iloc[-1], tsm['Close'].iloc[-2])
            
            st.write("---")
            k1, k2 = st.columns(2)
            k1.metric("NVIDIA", f"${nvda['Close'].iloc[-1]:.2f}", f"{nvda_chg}%")
            k2.metric("台積電 ADR", f"${tsm['Close'].iloc[-1]:.2f}", f"{tsm_chg}%")
        except: pass

        st.markdown("#### 🤖 AI 盤後解讀")
        sox_chg = market_data.get('費半', {}).get('change', 0)
        vix_chg = market_data.get('VIX', {}).get('change', 0)
        
        us_strategy = ""
        if sox_chg > 1 and tsm_chg > 1:
            us_strategy = "🔥 **極度樂觀**：費半與台積電 ADR 雙強，今日台股電子股易開高，適合順勢操作 AI 與半導體族群。"
        elif sox_chg < -1 and tsm_chg < -1:
            us_strategy = "❄️ **空方壓力**：美股半導體重挫，台股面臨外資提款壓力，早盤避開電子權值，觀察抗跌的傳產或防禦股。"
        elif vix_chg > 5:
            us_strategy = "⚠️ **避險情緒高**：雖然指數波動可能不大，但 VIX 飆高暗示大戶在買保險，操作宜短進短出。"
        else:
            us_strategy = "⚖️ **區間震盪**：美股缺乏明確方向，台股將回歸個股表現，建議「輕指數、重個股」。"
        st.info(us_strategy)

    # --- Tab 2: 台股 ---
    with tab_tw:
        st.subheader("🇹🇼 台股前日收盤 AI 戰情")
        with st.spinner("分析加權指數中..."):
            try:
                twii = yf.Ticker("^TWII").history(period="6mo")
                if not twii.empty:
                    twii.ta.sma(length=5, append=True)
                    twii.ta.sma(length=20, append=True)
                    twii.ta.stoch(append=True)
                    
                    latest = twii.iloc[-1]
                    prev = twii.iloc[-2]
                    
                    tc1, tc2 = st.columns(2)
                    idx_chg = calculate_change(latest['Close'], prev['Close'])
                    vol_ratio = latest['Volume'] / twii['Volume'].rolling(5).mean().iloc[-1]
                    
                    tc1.metric("加權指數", f"{latest['Close']:.0f}", f"{idx_chg}%")
                    tc2.metric("量能狀態", f"{vol_ratio:.1f}倍", "放量" if vol_ratio > 1 else "縮量", delta_color="off")
                    
                    close = latest['Close']
                    sma20 = latest.get('SMA_20', 0)
                    k = latest.get('STOCHk_14_3_3', 50)
                    d = latest.get('STOCHd_14_3_3', 50)
                    prev_k = prev.get('STOCHk_14_3_3', 50)
                    prev_d = prev.get('STOCHd_14_3_3', 50)
                    
                    tw_comment = ""
                    if close > sma20: tw_comment += "大盤站穩月線之上，技術面強勢，偏多操作。"
                    else: tw_comment += "大盤收在月線之下，弱勢整理，建議保守。"
                        
                    if k > d and prev_k < prev_d: tw_comment += " **KD 黃金交叉**，短線有反彈契機。"
                    elif k < d and prev_k > prev_d: tw_comment += " **KD 死亡交叉**，留意修正壓力。"
                        
                    st.success(f"{tw_comment}")
                    
                    fig = go.Figure(data=[go.Candlestick(x=twii.index, open=twii['Open'], high=twii['High'], low=twii['Low'], close=twii['Close'])])
                    fig.add_trace(go.Scatter(x=twii.index, y=twii['SMA_20'], line=dict(color='blue', width=1), name='月線'))
                    fig.update_layout(xaxis_rangeslider_visible=False, height=300, margin=dict(l=0, r=0, t=10, b=0))
                    st.plotly_chart(fig, use_container_width=True)
            except: st.error("無法取得台股資料")

# ==========================================
# 功能 2: 個股全方位診斷 (深度豐富版)
# ==========================================
elif menu == "2. 個股全方位診斷":
    st.header("🔎 個股診斷")
    
    ticker_input = st.text_input("股票代號", value="2330.TW") 
    period_input = st.selectbox("週期", ["3個月", "6個月", "1年"], index=1)
        
    if st.button("🚀 開始深度診斷", use_container_width=True):
        with st.spinner(f'AI 正在為您撰寫 {ticker_input} 完整報告...'):
            try:
                # 1. 數據獲取
                p_map = {"3個月": "3mo", "6個月": "6mo", "1年": "1y"}
                df = yf.Ticker(ticker_input).history(period=p_map[period_input])
                
                if df.empty:
                    st.error("查無資料，台股請加 .TW")
                else:
                    # 2. 指標計算
                    df.ta.sma(length=5, append=True)
                    df.ta.sma(length=20, append=True)
                    df.ta.sma(length=60, append=True)
                    df.ta.rsi(length=14, append=True)
                    df.ta.stoch(append=True) 
                    df.ta.macd(append=True)
                    df.ta.bbands(length=20, std=2, append=True)
                    
                    # 3. 繪圖
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_width=[0.2, 0.7])
                    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
                    if 'SMA_5' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA_5'], line=dict(color='orange', width=1), name='5MA'), row=1, col=1)
                    if 'SMA_20' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='blue', width=1), name='月線'), row=1, col=1)
                    
                    if 'BBU_20_2.0' in df.columns:
                        fig.add_trace(go.Scatter(x=df.index, y=df['BBU_20_2.0'], line=dict(color='gray', width=1, dash='dot'), name='布林上'), row=1, col=1)
                        fig.add_trace(go.Scatter(x=df.index, y=df['BBL_20_2.0'], line=dict(color='gray', width=1, dash='dot'), fill='tonexty', fillcolor='rgba(200,200,200,0.1)', name='布林下'), row=1, col=1)

                    colors = ['red' if row['Open'] - row['Close'] >= 0 else 'green' for index, row in df.iterrows()]
                    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='量'), row=2, col=1)
                    fig.update_layout(xaxis_rangeslider_visible=False, height=450, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

                    # 4. 深度邏輯分析
                    latest = df.iloc[-1]
                    prev = df.iloc[-2]
                    
                    close = latest['Close']
                    sma5 = latest.get('SMA_5', 0)
                    sma20 = latest.get('SMA_20', 0)
                    rsi = latest.get('RSI_14', 50)
                    k = latest.get('STOCHk_14_3_3', 50)
                    d = latest.get('STOCHd_14_3_3', 50)
                    prev_k = prev.get('STOCHk_14_3_3', 50)
                    prev_d = prev.get('STOCHd_14_3_3', 50)
                    macd_hist = latest.get('MACDh_12_26_9', 0)
                    
                    vol_today = latest['Volume']
                    vol_avg = df['Volume'].rolling(5).mean().iloc[-1]
                    vol_ratio = vol_today / vol_avg if vol_avg > 0 else 0
                    
                    # --- A. 趨勢細節 ---
                    trend_score = 0
                    trend_msgs = []
                    if close > sma20:
                        trend_msgs.append("✅ 股價站上月線 (20MA)，波段偏多。")
                        trend_score += 1
                    else:
                        trend_msgs.append("🔻 股價跌破月線，上方有壓。")
                        
                    if sma5 > sma20:
                        trend_msgs.append("✅ 均線呈現黃金排列 (5MA > 20MA)。")
                        trend_score += 1
                    
                    if macd_hist > 0:
                        trend_msgs.append("✅ MACD 柱狀體翻紅，多方動能增強。")
                        trend_score += 1
                    else:
                        trend_msgs.append("🔻 MACD 柱狀體翻綠，空方動能主導。")

                    # --- B. 轉折細節 ---
                    mom_msgs = []
                    kd_status = "中性"
                    if k > d and prev_k < prev_d:
                        mom_msgs.append("🔥 **KD 黃金交叉**：低檔轉折訊號，有利反彈。")
                        kd_status = "黃金交叉"
                    elif k < d and prev_k > prev_d:
                        mom_msgs.append("❄️ **KD 死亡交叉**：高檔轉折訊號，留意修正。")
                        kd_status = "死亡交叉"
                    
                    if rsi > 80: mom_msgs.append("⚠️ RSI 高檔過熱 (>80)，勿過度追價。")
                    elif rsi < 20: mom_msgs.append("🟢 RSI 進入超賣區 (<20)，醞釀反彈。")
                    else: mom_msgs.append(f"⚪ RSI 為 {rsi:.1f}，處於合理區間。")

                    # --- C. 資金/通道細節 ---
                    vol_msgs = []
                    if vol_ratio > 1.5: vol_msgs.append(f"🔥 今日爆量 (量能比 {vol_ratio:.1f}x)，人氣匯集。")
                    elif vol_ratio < 0.6: vol_msgs.append(f"💤 今日量縮 (量能比 {vol_ratio:.1f}x)，觀望氣氛濃。")
                    else: vol_msgs.append("⚪ 量能溫和，無異常變化。")
                    
                    bbu = latest.get('BBU_20_2.0', 99999)
                    bbl = latest.get('BBL_20_2.0', 0)
                    if close > bbu: vol_msgs.append("⚠️ 股價觸及布林上緣，短線乖離偏大。")
                    elif close < bbl: vol_msgs.append("🟢 股價觸及布林下緣，短線有支撐機會。")

                    # --- D. 總結評語 ---
                    summary_text = ""
                    action_text = ""
                    
                    if trend_score == 3:
                        summary_text = "目前呈現**強勢多頭**格局，各項技術指標均偏多。"
                        action_text = "順勢操作，沿 5日線 持股續抱。若未跌破月線不輕易看空。"
                    elif trend_score == 2:
                        summary_text = "目前呈現**震盪偏多**格局，趨勢向上但部分指標整理中。"
                        action_text = "拉回找買點，不建議過度追高。"
                    elif trend_score == 1:
                        summary_text = "目前呈現**多空拉鋸**，方向尚未明確。"
                        action_text = "觀望為主，或區間高出低進。"
                    else:
                        summary_text = "目前呈現**空頭弱勢**格局，上方套牢壓力大。"
                        action_text = "反彈站在賣方，空手者不宜輕易接刀。"

                    # 5. UI 顯示 (恢復豐富版面)
                    st.markdown("### 📊 AI 綜合戰力評分")
                    
                    # 總分卡片
                    sc1, sc2 = st.columns([1, 2])
                    with sc1:
                        st.metric("多方戰力", f"{trend_score}/3", kd_status)
                    with sc2:
                        st.info(f"**{summary_text}**\n\n💡 建議：{action_text}")
                    
                    # 詳細三欄分析 (在手機上會自動垂直排列，在電腦上會並排)
                    st.markdown("#### 📝 詳細分析報告")
                    c1, c2, c3 = st.columns(3)
                    
                    with c1:
                        st.markdown("**📈 趨勢面**")
                        for m in trend_msgs: st.write(m)
                    
                    with c2:
                        st.markdown("**🔄 轉折面**")
                        st.write(f"- KD值: K={k:.1f}, D={d:.1f}")
                        for m in mom_msgs: st.write(m)
                        
                    with c3:
                        st.markdown("**💰 資金面**")
                        for m in vol_msgs: st.write(m)

            except Exception as e:
                st.error(f"分析錯誤: {e}")