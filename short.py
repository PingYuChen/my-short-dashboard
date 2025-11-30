import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import urllib3

# --- 忽略 SSL 警告 ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 頁面設定 ---
st.set_page_config(page_title="短線操作", layout="wide", initial_sidebar_state="collapsed")

st.title("📱 短線操作 (Smart Trader)")
st.caption("AI 驅動的台美股資金流向與技術分析 | V2.0 完美復刻版")

# --- 側邊欄 ---
menu = st.sidebar.radio("功能選單", ["1. 市場大盤戰情 (美/台)", "2. 個股全方位診斷"])

# --- Helper Functions ---
def calculate_change(current, previous):
    if previous == 0: return 0
    return round((current - previous) / previous * 100, 2)

@st.cache_data(ttl=300)
def get_tw_hot_sectors():
    url = "https://tw.stock.yahoo.com/_td-stock/api/resource/StockServices.rank;exchange=TAI;limit=10;period=day;rankType=industry"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=5)
        data = r.json()
        rank_list = data.get('list', [])
        sector_data = []
        for item in rank_list:
            name = item.get('symbolName', '')
            change_pct = item.get('changePercent', 0)
            sector_data.append({"族群名稱": name, "漲跌幅": float(change_pct)})
        return pd.DataFrame(sector_data)
    except:
        return None

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
        
        sox_chg = market_data.get('費半', {}).get('change', 0)
        vix_chg = market_data.get('VIX', {}).get('change', 0)
        
        st.markdown("#### 🤖 AI 盤後解讀")
        if sox_chg > 1: st.info("🔥 **極度樂觀**：費半強勢，有利台股電子族群開高。")
        elif sox_chg < -1: st.info("❄️ **空方壓力**：半導體回檔，提防外資提款權值股。")
        elif vix_chg > 5: st.warning("⚠️ **避險升溫**：VIX 飆高，市場波動恐加大。")
        else: st.success("⚖️ **區間震盪**：方向未明，個股表現為主。")

    # --- Tab 2: 台股 ---
    with tab_tw:
        st.subheader("🇹🇼 台股盤勢 & 熱門族群")
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
                    if close > sma20: tw_comment += "大盤站穩月線之上，多頭格局不變。"
                    else: tw_comment += "大盤跌破月線，短線轉弱整理。"
                    if k > d and prev_k < prev_d: tw_comment += " 且 **KD 黃金交叉**，有反彈機會。"
                    
                    st.success(f"🤖 **AI 總結：** {tw_comment}")
                    
                    fig = go.Figure(data=[go.Candlestick(
                        x=twii.index, open=twii['Open'], high=twii['High'], low=twii['Low'], close=twii['Close'],
                        increasing_line_color='red', decreasing_line_color='green'
                    )])
                    fig.add_trace(go.Scatter(x=twii.index, y=twii['SMA_20'], line=dict(color='blue', width=1), name='月線'))
                    fig.update_layout(xaxis_rangeslider_visible=False, height=300, margin=dict(l=0, r=0, t=10, b=0))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown("#### 🔥 本日強勢族群")
                    df_sector = get_tw_hot_sectors()
                    if df_sector is not None and not df_sector.empty:
                        st.dataframe(
                            df_sector.style.format({"漲跌幅": "{:.2f}%"})
                            .applymap(lambda v: 'color: red' if v > 0 else 'color: green', subset=['漲跌幅']),
                            use_container_width=True, hide_index=True
                        )
                    else: st.info("暫時無法取得族群資料")
            except: st.error("無法取得台股資料")

# ==========================================
# 功能 2: 個股全方位診斷 (V1.8 完整邏輯復刻)
# ==========================================
elif menu == "2. 個股全方位診斷":
    st.header("🔎 個股診斷")
    
    ticker_input = st.text_input("股票代號", value="2330.TW") 
    period_input = st.selectbox("週期", ["3個月", "6個月", "1年"], index=1)
        
    if st.button("🚀 開始深度診斷", use_container_width=True):
        with st.spinner(f'AI 正在進行多因子交叉分析...'):
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
                    
                    # 3. 繪圖 (保留 V1.9 紅漲綠跌)
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_width=[0.2, 0.7])
                    fig.add_trace(go.Candlestick(
                        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線',
                        increasing_line_color='red', decreasing_line_color='green'
                    ), row=1, col=1)
                    
                    if 'SMA_5' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA_5'], line=dict(color='orange', width=1), name='5MA'), row=1, col=1)
                    if 'SMA_20' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='blue', width=1), name='月線'), row=1, col=1)
                    if 'SMA_60' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA_60'], line=dict(color='green', width=1), name='季線'), row=1, col=1)
                    
                    if 'BBU_20_2.0' in df.columns:
                        fig.add_trace(go.Scatter(x=df.index, y=df['BBU_20_2.0'], line=dict(color='gray', width=1, dash='dot'), name='布林上'), row=1, col=1)
                        fig.add_trace(go.Scatter(x=df.index, y=df['BBL_20_2.0'], line=dict(color='gray', width=1, dash='dot'), fill='tonexty', fillcolor='rgba(200,200,200,0.1)', name='布林下'), row=1, col=1)

                    colors = ['red' if row['Close'] >= row['Open'] else 'green' for index, row in df.iterrows()]
                    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='量'), row=2, col=1)
                    fig.update_layout(xaxis_rangeslider_visible=False, height=450, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

                    # 4. 數據提取與復刻 V1.8 邏輯
                    latest = df.iloc[-1]
                    prev = df.iloc[-2]
                    close = latest['Close']
                    high_price = df['High'].max()
                    
                    sma20 = latest.get('SMA_20', 0)
                    sma60 = latest.get('SMA_60', 0)
                    bbu = latest.get('BBU_20_2.0', 0)
                    bbl = latest.get('BBL_20_2.0', 0)
                    
                    # 壓力支撐
                    resistances = []
                    supports = []
                    for price, name in [(sma20, "月線"), (sma60, "季線"), (bbu, "布林上"), (bbl, "布林下"), (high_price, "前高")]:
                        if price > 0:
                            if close < price: resistances.append((price, name))
                            elif close > price: supports.append((price, name))
                    
                    resistances.sort(key=lambda x: x[0])
                    supports.sort(key=lambda x: x[0], reverse=True)
                    nearest_res = resistances[0] if resistances else (None, "無")
                    nearest_sup = supports[0] if supports else (None, "無")

                    # 詳細報告邏輯 (復刻 V1.8)
                    sma5 = latest.get('SMA_5', 0)
                    macd_hist = latest.get('MACDh_12_26_9', 0)
                    k = latest.get('STOCHk_14_3_3', 50)
                    d = latest.get('STOCHd_14_3_3', 50)
                    prev_k = prev.get('STOCHk_14_3_3', 50)
                    prev_d = prev.get('STOCHd_14_3_3', 50)
                    rsi = latest.get('RSI_14', 50)
                    vol_ratio = latest['Volume'] / df['Volume'].rolling(5).mean().iloc[-1]
                    
                    # A. 趨勢細節
                    trend_score = 0
                    trend_msgs = []
                    if close > sma20:
                        trend_msgs.append("✅ 站上月線 (20MA)，波段偏多。")
                        trend_score += 1
                    else: trend_msgs.append("🔻 跌破月線，上方有壓。")
                        
                    if sma5 > sma20:
                        trend_msgs.append("✅ 均線黃金排列 (5MA > 20MA)。")
                        trend_score += 1
                    
                    if macd_hist > 0:
                        trend_msgs.append("✅ MACD 紅柱，多方動能增強。")
                        trend_score += 1
                    else: trend_msgs.append("🔻 MACD 綠柱，空方動能主導。")

                    # B. 轉折細節
                    mom_msgs = []
                    if k > d and prev_k < prev_d: mom_msgs.append("🔥 **KD 黃金交叉**：低檔轉折訊號。")
                    elif k < d and prev_k > prev_d: mom_msgs.append("❄️ **KD 死亡交叉**：高檔轉折訊號。")
                    else: mom_msgs.append(f"⚪ KD 無明顯交叉 (K:{k:.0f})。")
                    
                    if rsi > 80: mom_msgs.append("⚠️ RSI 高檔過熱，勿追價。")
                    elif rsi < 20: mom_msgs.append("🟢 RSI 超賣，醞釀反彈。")
                    else: mom_msgs.append(f"⚪ RSI {rsi:.1f} 合理區間。")

                    # C. 資金/通道細節
                    vol_msgs = []
                    if vol_ratio > 1.5: vol_msgs.append(f"🔥 今日爆量 ({vol_ratio:.1f}x)，人氣匯集。")
                    elif vol_ratio < 0.6: vol_msgs.append(f"💤 今日量縮 ({vol_ratio:.1f}x)，觀望氣氛。")
                    else: vol_msgs.append("⚪ 量能溫和。")
                    
                    if close > bbu: vol_msgs.append("⚠️ 觸及布林上緣，乖離偏大。")
                    elif close < bbl: vol_msgs.append("🟢 觸及布林下緣，有支撐機會。")

                    # 操作建議
                    advice = ""
                    color_code = "blue"
                    if trend_score == 3:
                        advice = "🔥 **強勢多頭**：趨勢向上。"
                        if nearest_res[0] and (nearest_res[0]-close)/close < 0.02:
                            advice += f" 但逼近壓力 **${nearest_res[0]:.2f}**，勿追高。"
                            color_code = "orange"
                        else:
                            advice += " 可順勢操作。"
                            color_code = "green"
                    elif trend_score <= 1:
                        advice = "🐻 **空頭弱勢**：建議觀望。"
                        color_code = "red"
                    else:
                        advice = "📈 **震盪整理**：拉回找買點。"
                        color_code = "green"

                    # 5. UI 顯示 (恢復 V1.8 豐富佈局)
                    st.markdown("### 💡 AI 操作總結")
                    if color_code == "green": st.success(advice)
                    elif color_code == "orange": st.warning(advice)
                    else: st.error(advice)

                    st.markdown("#### 🛑 關鍵價位")
                    kp1, kp2 = st.columns(2)
                    with kp1:
                        if nearest_res[0]: st.metric("壓力", f"${nearest_res[0]:.2f}", nearest_res[1], delta_color="inverse")
                        else: st.metric("壓力", "天空", "無")
                    with kp2:
                        if nearest_sup[0]: st.metric("支撐", f"${nearest_sup[0]:.2f}", nearest_sup[1])
                        else: st.metric("支撐", "深淵", "無")

                    st.markdown("#### 📝 詳細技術分析")
                    # 這裡就是您要的：三欄詳細資料回歸！
                    c1, c2, c3 = st.columns(3)
                    
                    with c1:
                        st.markdown("**📈 趨勢面**")
                        st.write(f"• 趨勢分: {trend_score}/3")
                        for m in trend_msgs: st.write(m)
                    
                    with c2:
                        st.markdown("**🔄 轉折面**")
                        st.write(f"• KD值: K{k:.0f} / D{d:.0f}")
                        for m in mom_msgs: st.write(m)
                        
                    with c3:
                        st.markdown("**💰 資金面**")
                        st.write(f"• 量能比: {vol_ratio:.1f}倍")
                        for m in vol_msgs: st.write(m)

            except Exception as e:
                st.error(f"分析錯誤: {e}")