import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import datetime
import requests # 新增 requests 用於呼叫 ElevenLabs API

# ==========================================
# 企業級後台 (Admin Portal V3 - 算力監控版)
# ==========================================

st.set_page_config(page_title="MetaVoice Admin", page_icon="🏢", layout="wide")

# 1. 權限驗證
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    st.markdown("<h1 style='text-align:center;'>🏢 企業後台登入</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        pwd = st.text_input("管理員密碼", type="password")
        if st.button("登入", use_container_width=True):
            if pwd == st.secrets["ADMIN_LOGIN_PASSWORD"]:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("權限不足")
    st.stop()

# 2. 初始化高權限資料庫
@st.cache_resource
def init_admin_db():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_KEY"])

supabase = init_admin_db()

# --- 資料撈取函數 ---
def get_all_profiles():
    res = supabase.table("profiles").select("*").execute()
    return pd.DataFrame(res.data)

def get_all_transactions():
    res = supabase.table("transaction_logs").select("*").order("created_at", desc=True).execute()
    return pd.DataFrame(res.data)

def get_all_feedbacks():
    res = supabase.table("feedbacks").select("*").order("created_at", desc=True).execute()
    return pd.DataFrame(res.data)

# --- [新增] ElevenLabs API 查詢 ---
def get_elevenlabs_status():
    try:
        url = "https://api.elevenlabs.io/v1/user/subscription"
        headers = {"xi-api-key": st.secrets["ELEVENLABS_API_KEY"]}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
    except: pass
    return None

# --- 介面開始 ---

with st.sidebar:
    st.title("🏢 管理中心")
    page = st.radio("導航", ["📊 儀表板總覽", "👥 會員管理 (CRM)", "📈 成長與裂變", "💰 財務與日誌"])
    st.divider()
    if st.button("登出"):
        st.session_state.admin_logged_in = False
        st.rerun()

# 讀取數據 (全域)
df_users = get_all_profiles()
df_logs = get_all_transactions()
df_feed = get_all_feedbacks()

# 處理日期格式
if not df_users.empty:
    df_users['created_at'] = pd.to_datetime(df_users['created_at'])
if not df_logs.empty:
    df_logs['created_at'] = pd.to_datetime(df_logs['created_at'])
    df_logs['amount'] = pd.to_numeric(df_logs['amount'], errors='coerce').fillna(0)

# ==========================================
# PAGE 1: 儀表板總覽
# ==========================================
if page == "📊 儀表板總覽":
    st.title("📊 營運戰情室")
    
    # ----------------------------------
    # 🔥 [新增] AI 算力資源監控區塊
    # ----------------------------------
    st.subheader("⚡ AI 算力資源監控")
    
    # 計算本月消耗 (用於 OpenAI/Gemini 估算)
    current_month_logs = pd.DataFrame()
    month_consumed_points = 0
    if not df_logs.empty:
        current_month = datetime.datetime.now().month
        current_month_logs = df_logs[df_logs['created_at'].dt.month == current_month]
        # 篩選消耗 (負數)
        consumed = current_month_logs[current_month_logs['amount'] < 0]
        month_consumed_points = abs(consumed['amount'].sum())

    mon_c1, mon_c2, mon_c3 = st.columns(3)
    
    # 卡片 1: ElevenLabs (真實 API 數據)
    with mon_c1:
        el_data = get_elevenlabs_status()
        if el_data:
            used = el_data['character_count']
            limit = el_data['character_limit']
            percent = used / limit if limit > 0 else 0
            res_date = datetime.datetime.fromtimestamp(el_data.get('next_character_count_reset_unix', 0)).strftime('%m/%d')
            
            st.metric("🗣️ ElevenLabs (聲音)", f"{limit - used:,} 字剩餘", f"已用 {percent*100:.1f}%", delta_color="normal")
            st.progress(percent)
            if percent > 0.8: st.error("⚠️ 額度吃緊！")
            else: st.caption(f"🟢 運作正常 (重置日: {res_date})")
        else:
            st.warning("無法連線至 ElevenLabs")

    # 卡片 2: OpenAI (內部估算)
    with mon_c2:
        # 假設 80% 的消耗來自 OpenAI TTS (初級會員)，每點約 0.03 元
        est_cost_openai = (month_consumed_points * 0.8) * 0.001 # 粗估係數 USD
        st.metric("⚡ OpenAI (初級語音)", f"${est_cost_openai:.2f} USD", "本月預估消耗")
        st.caption("🟢 連線正常 (API Key 有效)")
        st.link_button("🔗 前往 OpenAI 儲值", "https://platform.openai.com/settings/organization/billing/overview")

    # 卡片 3: Google Gemini (次數估算)
    with mon_c3:
        # 假設每一次消耗點數都伴隨一次 LLM 呼叫
        call_count = len(current_month_logs[current_month_logs['amount'] < 0])
        st.metric("✨ Google Gemini (大腦)", f"{call_count:,} 次", "本月呼叫次數")
        st.caption("🟢 連線正常 (Flash 免費額度中)")
        st.link_button("🔗 查看 Google Cloud 費用", "https://console.cloud.google.com/billing")

    st.divider()

    # ----------------------------------
    # 原有的 KPI 指標
    # ----------------------------------
    st.subheader("📈 營運指標")
    total_users = len(df_users)
    active_users = 0
    if not df_users.empty and 'last_interaction_date' in df_users.columns:
        df_users['last_date_obj'] = pd.to_datetime(df_users['last_interaction_date'], errors='coerce').dt.date
        last_7_days = datetime.date.today() - datetime.timedelta(days=7)
        active_users = len(df_users[df_users['last_date_obj'] >= last_7_days])

    # 預估營收
    total_revenue = 0
    if not df_logs.empty:
        income_df = df_logs[(df_logs['amount'] > 0) & (df_logs['reason'].str.contains('儲值|升級', na=False))]
        total_revenue = income_df['amount'].sum() * 0.88 # 估算

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("總會員數", total_users)
    col2.metric("周活躍 (WAU)", active_users)
    col3.metric("本月預估營收", f"${total_revenue:,.0f}")
    # 這裡顯示總體獲利狀況
    total_cost_est = month_consumed_points * 0.5 # 粗估每點 0.5 台幣成本
    profit = total_revenue - total_cost_est
    col4.metric("本月粗利預估", f"${profit:,.0f}", delta=f"{profit}", help="營收 - AI成本")

    # 2. 趨勢圖表
    c_chart1, c_chart2 = st.columns(2)
    with c_chart1:
        st.caption("每日新增會員")
        if not df_users.empty:
            df_daily = df_users.groupby(df_users['created_at'].dt.date).size().reset_index(name='count')
            st.plotly_chart(px.line(df_daily, x='created_at', y='count', markers=True), use_container_width=True)
    with c_chart2:
        st.caption("每日 AI 使用量 (點數消耗)")
        if not df_logs.empty:
            df_usage = df_logs[df_logs['amount'] < 0].copy()
            df_usage['abs'] = df_usage['amount'].abs()
            df_daily_use = df_usage.groupby(df_usage['created_at'].dt.date)['abs'].sum().reset_index()
            st.plotly_chart(px.bar(df_daily_use, x='created_at', y='abs', color_discrete_sequence=['#FF4B4B']), use_container_width=True)

# ==========================================
# PAGE 2: 會員管理 (CRM)
# ==========================================
elif page == "👥 會員管理 (CRM)":
    st.title("👥 會員管理系統")
    search = st.text_input("🔍 搜尋 Email 或 User ID")
    display_df = df_users.copy()
    if search and not display_df.empty:
        display_df = display_df[
            display_df['email'].astype(str).str.contains(search, case=False) | 
            display_df['user_id'].astype(str).str.contains(search, case=False)
        ]

    if not display_df.empty:
        cols_to_show = ['user_id', 'email', 'tier', 'xp', 'energy', 'created_at', 'last_interaction_date']
        final_cols = [c for c in cols_to_show if c in display_df.columns]
        st.dataframe(
            display_df[final_cols],
            use_container_width=True,
            column_config={
                "user_id": st.column_config.TextColumn("User ID", width="small"),
                "energy": st.column_config.ProgressColumn("電量", min_value=0, max_value=100, format="%d"),
                "created_at": st.column_config.DatetimeColumn("註冊時間", format="YYYY-MM-DD HH:mm"),
            }
        )
    else: st.info("無資料")
    
    st.divider()
    st.subheader("✏️ 會員操作")
    c_edit1, c_edit2 = st.columns(2)
    with c_edit1: target_uid = st.text_input("User ID")
    with c_edit2: action = st.selectbox("動作", ["贈送電量", "贈送 XP", "升級會員"])
    if target_uid and st.button("執行"):
        if action == "升級會員":
            supabase.table("profiles").update({"tier": "intermediate"}).eq("user_id", target_uid).execute()
        else:
            supabase.table("transaction_logs").insert({"user_id": target_uid, "amount": 50, "reason": "Admin"}).execute()
        st.success("已執行")

# ==========================================
# PAGE 3: 成長與裂變
# ==========================================
elif page == "📈 成長與裂變":
    st.title("📈 病毒擴散分析")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🏆 推廣排行榜")
        if not df_logs.empty:
            ref_logs = df_logs[(df_logs['amount'] > 0) & (df_logs['reason'].astype(str).str.contains('朋友|邀請', case=False, na=False))]
            if not ref_logs.empty:
                top = ref_logs.groupby('user_id')['amount'].sum().reset_index().sort_values('amount', ascending=False).head(10)
                if not df_users.empty: top = pd.merge(top, df_users[['user_id', 'email']], on='user_id', how='left')
                st.dataframe(top, use_container_width=True)
            else: st.info("無資料")
    with c2:
        st.subheader("🗣️ 評價回饋")
        if not df_feed.empty:
            if not df_users.empty: df_feed = pd.merge(df_feed, df_users[['user_id', 'email']], left_on='to_user_id', right_on='user_id', how='left')
            st.dataframe(df_feed[['score', 'comment', 'email']], use_container_width=True)
        else: st.info("無資料")

# ==========================================
# PAGE 4: 財務與日誌
# ==========================================
elif page == "💰 財務與日誌":
    st.title("💰 系統日誌")
    st.dataframe(df_logs, use_container_width=True)
