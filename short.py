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
st.caption("AI 驅動的台美股資金流向與技術分析 | V2.6 深度投顧版")

# --- 側邊欄 ---
menu = st.sidebar.radio("功能選單", ["1. 市場大盤戰情 (美/台)", "2. 個股全方位診斷"])

# --- Helper Functions ---
def calculate_change(current, previous):
    if previous == 0: return 0
    return round((current - previous) / previous * 100, 2)

# V2.4 強力修復：中文名稱抓取
def get_stock_name(ticker):
    stock_id = ticker.split('.')[0]
    try:
        url1 = f"https://tw.stock.yahoo.com/_td-stock/api/resource/AutocompleteService;query={stock_id}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url1, headers=headers, verify=False, timeout=3)
        data = r.json()
        for result in data.get('result', []):
            if result.get('symbol') == f"{stock_id}.TW" or result.get('symbol') == f"{stock_id}.TWO":
                return result.get('name', ticker)
    except: pass
    try:
        url2 = f"https://tw.stock.yahoo.com/_td-stock/api/resource/StockServices.stockId;stockId={stock_id}"
        r = requests.get(url2, headers=headers, verify=False, timeout=3)
        data = r.json()
        return data.get('symbolName', ticker)
    except: return ticker

@st.cache_data(ttl=300)
def get_tw_hot_sectors():
    url = "https://tw.stock.yahoo.com/_td-stock/api/resource/StockServices.rank;exchange=TAI;limit=10;period=day;rankType=industry"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://tw.stock.yahoo.com/class/industry"}
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
    except: return None

# ==========================================
# 功能 1: 市場大盤戰情
# ==========================================
if menu == "1. 市場大盤戰情 (美/台)":
    
    tab_us, tab_tw = st.tabs(["🇺🇸 美股總結", "🇹🇼 台股總結"])

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
            except: col.metric(label=name, value="N/A")
        
        sox_chg = market_data.get('費半', {}).get('change', 0)
        vix_chg = market_data.get('VIX', {}).get('change', 0)
        st.markdown("#### 🤖 AI 盤後解讀")
        if sox_chg > 1: st.info("🔥 **極度樂觀**：費半強勢，有利台股電子族群開高。")
        elif sox_chg < -1: st.info("❄️ **空方壓力**：半導體回檔，提防外資提款權值股。")
        elif vix_chg > 5: st.warning("⚠️ **避險升溫**：VIX 飆高，市場波動恐加大。")
        else: st.success("⚖️ **區間震盪**：方向未明，個股表現為主。")

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
                            df_sector.style.format({"漲跌幅": "{:.2f}%"}).applymap(lambda v: 'color: red' if v > 0 else 'color: green', subset=['漲跌幅']),
                            use_container_width=True, hide_index=True
                        )
                    else: st.info("暫時無法取得族群資料")
            except: st.error("無法取得台股資料")

# ==========================================
# 功能 2: 個股全方位診斷
# ==========================================
elif menu == "2. 個股全方位診斷":
    st.header("🔎 個股診斷")
    
    ticker_input = st.text_input("股票代號", value="2330.TW") 
    period_input = st.selectbox("週期", ["3個月", "6個月", "1年"], index=1)
        
    if st.button("🚀 開始深度診斷", use_container_width=True):
        with st.spinner(f'AI 正在生成結構化投資報告...'):
            try:
                stock_name = get_stock_name(ticker_input)
                p_map = {"3個月": "3mo", "6個月": "6mo", "1年": "1y"}
                df = yf.Ticker(ticker_input).history(period=p_map[period_input])
                
                if df.empty:
                    st.error("查無資料，台股請加 .TW")
                else:
                    df.ta.sma(length=5, append=True)
                    df.ta.sma(length=20, append=True)
                    df.ta.sma(length=60, append=True)
                    df.ta.rsi(length=14, append=True)
                    df.ta.stoch(append=True) 
                    df.ta.macd(append=True)
                    df.ta.bbands(length=20, std=2, append=True)

                    latest = df.iloc[-1]
                    prev = df.iloc[-2]
                    close = latest['Close']
                    pct_change = calculate_change(close, prev['Close'])
                    high_price = df['High'].max()
                    
                    sma5 = latest.get('SMA_5', None)
                    sma20 = latest.get('SMA_20', None)
                    prev_sma20 = prev.get('SMA_20', 0)
                    sma60 = latest.get('SMA_60', None)
                    bbu = latest.get('BBU_20_2.0', None)
                    bbl = latest.get('BBL_20_2.0', None)
                    
                    resistances, supports = [], []
                    for price, name in [(sma20, "月線"), (sma60, "季線"), (bbu, "布林上"), (bbl, "布林下"), (high_price, "前高")]:
                        if price and not pd.isna(price) and price > 0:
                            if close < price: resistances.append((price, name))
                            elif close > price: supports.append((price, name))
                    
                    resistances.sort(key=lambda x: x[0])
                    supports.sort(key=lambda x: x[0], reverse=True)
                    nearest_res = resistances[0] if resistances else (None, "無")
                    nearest_sup = supports[0] if supports else (None, "無")

                    st.markdown("---")
                    st.subheader(f"{stock_name} ({ticker_input.upper()})")
                    
                    kp1, kp2, kp3 = st.columns(3)
                    with kp1:
                        if nearest_sup[0]: st.metric("📉 下方支撐", f"${nearest_sup[0]:.2f}", nearest_sup[1])
                        else: st.metric("📉 下方支撐", "深淵", "無")
                    with kp2:
                        st.metric("💰 目前股價", f"${close:.2f}", f"{pct_change}%", delta_color="normal")
                    with kp3:
                        if nearest_res[0]: st.metric("📈 上方壓力", f"${nearest_res[0]:.2f}", nearest_res[1], delta_color="inverse")
                        else: st.metric("📈 上方壓力", "天空", "無")

                    # 評分系統 (5分制)
                    score = 0
                    if sma20 and close > sma20: score += 1
                    if sma60 and close > sma60: score += 1
                    if sma20 and prev_sma20 and sma20 > prev_sma20: score += 1
                    if sma5 and sma20 and sma60 and sma5 > sma20 and sma20 > sma60: score += 1
                    macd_hist = latest.get('MACDh_12_26_9', 0)
                    if macd_hist > 0: score += 1
                    
                    # 繪圖
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_width=[0.2, 0.7])
                    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線', increasing_line_color='red', decreasing_line_color='green'), row=1, col=1)
                    if sma5: fig.add_trace(go.Scatter(x=df.index, y=df['SMA_5'], line=dict(color='orange', width=1), name='5MA'), row=1, col=1)
                    if sma20: fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='blue', width=1), name='月線'), row=1, col=1)
                    if sma60: fig.add_trace(go.Scatter(x=df.index, y=df['SMA_60'], line=dict(color='green', width=1), name='季線'), row=1, col=1)
                    if bbu:
                        fig.add_trace(go.Scatter(x=df.index, y=df['BBU_20_2.0'], line=dict(color='gray', width=1, dash='dot'), name='布林上'), row=1, col=1)
                        fig.add_trace(go.Scatter(x=df.index, y=df['BBL_20_2.0'], line=dict(color='gray', width=1, dash='dot'), fill='tonexty', fillcolor='rgba(200,200,200,0.1)', name='布林下'), row=1, col=1)
                    colors = ['red' if row['Close'] >= row['Open'] else 'green' for index, row in df.iterrows()]
                    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='量'), row=2, col=1)
                    fig.update_layout(xaxis_rangeslider_visible=False, height=450, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

                    # 詳細分析區塊
                    k = latest.get('STOCHk_14_3_3', 50)
                    d = latest.get('STOCHd_14_3_3', 50)
                    prev_k = prev.get('STOCHk_14_3_3', 50)
                    prev_d = prev.get('STOCHd_14_3_3', 50)
                    rsi = latest.get('RSI_14', 50)
                    vol_avg = df['Volume'].rolling(5).mean().iloc[-1]
                    vol_today = latest['Volume']
                    if vol_today < 100: vol_today = prev['Volume']
                    vol_ratio = vol_today / vol_avg if vol_avg > 0 else 0
                    
                    trend_msgs, mom_msgs, vol_msgs = [], [], []
                    if sma20 and close > sma20: trend_msgs.append("✅ 股價 > 月線 (20MA)")
                    else: trend_msgs.append("🔻 股價 < 月線 (20MA)")
                    if sma20 and prev_sma20 and sma20 > prev_sma20: trend_msgs.append("✅ 月線翻揚向上")
                    else: trend_msgs.append("🔻 月線下彎或持平")
                    if sma60 and close > sma60: trend_msgs.append("✅ 股價 > 季線 (60MA)")
                    else: trend_msgs.append("🔻 股價 < 季線 (長線弱)")
                    if macd_hist > 0: trend_msgs.append("✅ MACD 紅柱")
                    else: trend_msgs.append("🔻 MACD 綠柱")

                    if k > d and prev_k < prev_d: mom_msgs.append("🔥 KD 黃金交叉")
                    elif k < d and prev_k > prev_d: mom_msgs.append("❄️ KD 死亡交叉")
                    else: mom_msgs.append("⚪ KD 無明顯訊號")
                    
                    if vol_ratio > 1.5: vol_msgs.append(f"🔥 爆量 ({vol_ratio:.1f}x)")
                    elif vol_ratio < 0.6: vol_msgs.append(f"💤 量縮 ({vol_ratio:.1f}x)")
                    else: vol_msgs.append(f"⚪ 溫和 ({vol_ratio:.1f}x)")

                    st.markdown("#### 📝 詳細技術分析")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown("**📈 趨勢面**")
                        st.write(f"• 趨勢分: **{score}/5**")
                        for m in trend_msgs: st.write(m)
                    with c2:
                        st.markdown("**🔄 轉折面**")
                        st.write(f"• K{k:.0f} / D{d:.0f}")
                        for m in mom_msgs: st.write(m)
                    with c3:
                        st.markdown("**💰 資金面**")
                        st.write(f"• 量能比: {vol_ratio:.1f}倍")
                        for m in vol_msgs: st.write(m)

                    # ===============================================
                    # V2.6 核心升級: 結構化 AI 投資建議 (仿截圖風格)
                    # ===============================================
                    st.markdown("---")
                    st.subheader("3. 綜合投資建議 (AI 戰情室)")

                    # 1. 定義變數
                    strategy_title = ""
                    aggressive_advice = ""
                    conservative_advice = ""
                    summary_one_liner = ""
                    res_price = nearest_res[0] if nearest_res[0] else None
                    res_name = nearest_res[1]
                    sup_price = nearest_sup[0] if nearest_sup[0] else None
                    sup_name = nearest_sup[1]

                    # 2. 邏輯分支
                    
                    # 情境 A: 強勢多頭 (Score >= 4)
                    if score >= 4:
                        strategy_title = "【操作策略】：多頭排列，順勢操作，沿 5日線/月線 續抱"
                        
                        aggressive_advice = f"""
                        - **進場理由**：均線多頭排列，且 MACD 紅柱，動能強勁。
                        - **目標價**：上方無明顯均線壓力，可參考布林上緣或波段前高 **${high_price:.2f}**。
                        - **防守點**：以 **5日線 (${sma5:.2f})** 為短線防守，跌破減碼。
                        """
                        
                        conservative_advice = f"""
                        - **建議續抱**：長線趨勢向上，持股續抱。
                        - **進場時機**：若空手，建議等待股價回測 **月線 (${sma20:.2f})** 不破後再佈局，切勿追高。
                        """
                        
                        summary_one_liner = f"這是一波**「強勢回升」**行情。上方空間大，下方有月線支撐，預期將沿均線震盪走高。建議**「拉回找買點」**。"

                    # 情境 B: 技術性反彈 (站上月線 但 跌破季線) -> 這就是您截圖的情境
                    elif sma20 and sma60 and close > sma20 and close < sma60:
                        strategy_title = "【操作策略】：短線區間操作，嚴設停損，不宜過度樂觀長抱"
                        
                        aggressive_advice = f"""
                        - **進場理由**：利用目前「股價 > 月線」且 MACD/KD 轉強的短多訊號進場搶反彈。
                        - **目標價**：以前方 **季線 (${sma60:.2f})** 位置或前波高點跌下來的壓力區為第一獲利了結點。
                        - **防守點**：以 **月線 (${sma20:.2f})** 作為防守。如果股價再次跌破月線，代表反彈失敗，應立即停損出場。
                        """
                        
                        conservative_advice = f"""
                        - **建議觀望**：目前長線趨勢仍弱 (在季線下)，且月線可能尚未明顯翻揚。
                        - **進場時機**：建議等待股價 **帶量突破季線**，或者等待月線明顯轉為上彎助漲，確認趨勢由空翻多後再進場佈局，安全性較高。
                        """
                        
                        summary_one_liner = f"這是一波**「技術性反彈」**，而非回升行情。上方有季線壓力 (${sma60:.2f})，下方有月線支撐，預期短期內會在均線之間震盪整理。建議**「買黑不買紅」** (回測支撐不破時買進)，並隨時注意量能是否放大以突破僵局。"

                    # 情境 C: 震盪整理 (分數 2-3，且非反彈格局)
                    elif score >= 2:
                        strategy_title = "【操作策略】：箱型區間操作，高出低進"
                        
                        aggressive_advice = f"""
                        - **進場理由**：指標位於低檔 (如 KD 金叉) 或回測支撐有守。
                        - **目標價**：區間上緣或 **{res_name} (${res_price:.2f})**。
                        - **防守點**：區間下緣或 **{sup_name} (${sup_price:.2f})**。
                        """
                        
                        conservative_advice = f"""
                        - **建議觀望**：趨勢不明確，均線糾結。
                        - **進場時機**：等待帶量突破區間上緣後再追價。
                        """
                        
                        summary_one_liner = "目前處於**「多空拉鋸」**階段。方向尚未明確，操作難度高，建議**「多看少做」**。"

                    # 情境 D: 空頭弱勢 (Score <= 1)
                    else:
                        strategy_title = "【操作策略】：趨勢偏空，反彈站在賣方，空手者勿接刀"
                        
                        aggressive_advice = f"""
                        - **操作建議**：不建議做多。若有期貨/融券資格，可於反彈至 **月線 (${sma20:.2f})** 附近不過時嘗試放空。
                        - **防守點**：站回月線即停損。
                        """
                        
                        conservative_advice = f"""
                        - **建議觀望**：全均線蓋頭反壓，跌勢未止。
                        - **進場時機**：**完全不建議進場**。需等待底部型態 (如 W底) 出現且站上頸線。
                        """
                        
                        summary_one_liner = "目前呈現**「空頭修正」**格局。上方層層套牢賣壓，反彈皆視為逃命波。建議**「保留現金」**，等待落底訊號。"

                    # 3. 顯示 UI (仿截圖排版)
                    st.info(f"#### {strategy_title}")
                    
                    st.markdown(f"""
                    - **積累型投資者 (做短線)**：
                        {aggressive_advice}
                    - **保守型投資者 (做波段/長線)**：
                        {conservative_advice}
                    """)
                    
                    st.markdown("---")
                    st.markdown(f"**💡 總結一句話：**\n{summary_one_liner}")

            except Exception as e:
                st.error(f"分析錯誤: {e}")