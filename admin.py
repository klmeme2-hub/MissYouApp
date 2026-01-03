import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import datetime

# ==========================================
# 企業級後台 (Admin Portal)
# ==========================================

st.set_page_config(page_title="MetaVoice Admin", page_icon="🏢", layout="wide")

# 1. 權限驗證 (簡易防護)
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
    # 使用 Service Role Key 以讀取所有資料
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

# --- 介面開始 ---

# Sidebar 導航
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

# 處理日期格式
if not df_users.empty:
    df_users['created_at'] = pd.to_datetime(df_users['created_at'])
if not df_logs.empty:
    df_logs['created_at'] = pd.to_datetime(df_logs['created_at'])

# ==========================================
# PAGE 1: 儀表板總覽
# ==========================================
if page == "📊 儀表板總覽":
    st.title("📊 營運戰情室")
    
    # 1. 核心指標 (KPI)
    total_users = len(df_users)
    
    # 計算活躍用戶 (7天內有互動)
    active_users = 0
    if not df_users.empty and 'last_interaction_date' in df_users.columns:
        last_7_days = datetime.date.today() - datetime.timedelta(days=7)
        # 轉換 date 格式進行比較
        df_users['last_date_obj'] = pd.to_datetime(df_users['last_interaction_date']).dt.date
        active_users = len(df_users[df_users['last_date_obj'] >= last_7_days])

    # 估算營收 (透過 log 中的付費紀錄)
    # 假設 reason 包含 "付費" 或 "儲值"
    revenue = 0
    # 這裡僅為模擬，實際需從 payment table 撈取
    # revenue = df_logs[df_logs['reason'].str.contains('儲值')]['amount_cash'].sum() 
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("總會員數", total_users, f"+{len(df_users[df_users['created_at'].dt.date == datetime.date.today()])} 今日")
    col2.metric("周活躍 (WAU)", active_users)
    col3.metric("本月預估營收", "$2,450", "+12%") # 範例數據
    col4.metric("AI 成本預估", "$320", "-5%") # 範例數據

    # 2. 趨勢圖表
    st.subheader("📈 成長趨勢")
    c_chart1, c_chart2 = st.columns(2)
    
    with c_chart1:
        if not df_users.empty:
            df_daily_users = df_users.groupby(df_users['created_at'].dt.date).size().reset_index(name='count')
            fig_user = px.line(df_daily_users, x='created_at', y='count', title="每日新增會員", markers=True)
            st.plotly_chart(fig_user, use_container_width=True)
            
    with c_chart2:
        if not df_logs.empty:
            # 統計每日 Token/電量 消耗量 (代表使用強度)
            df_usage = df_logs[df_logs['amount'] < 0].copy()
            df_usage['abs_amount'] = df_usage['amount'].abs()
            df_daily_usage = df_usage.groupby(df_usage['created_at'].dt.date)['abs_amount'].sum().reset_index()
            fig_usage = px.bar(df_daily_usage, x='created_at', y='abs_amount', title="每日電量消耗 (使用量)", color_discrete_sequence=['#FF4B4B'])
            st.plotly_chart(fig_usage, use_container_width=True)

# ==========================================
# PAGE 2: 會員管理 (CRM)
# ==========================================
elif page == "👥 會員管理 (CRM)":
    st.title("👥 會員管理系統")
    
    # 篩選器
    c_fil1, c_fil2 = st.columns(2)
    with c_fil1:
        search = st.text_input("🔍 搜尋 Email 或 User ID")
    with c_fil2:
        filter_tier = st.multiselect("等級篩選", ["basic", "intermediate", "advanced", "eternal"])
    
    # 資料處理
    display_df = df_users.copy()
    if filter_tier:
        display_df = display_df[display_df['tier'].isin(filter_tier)]
    if search:
        display_df = display_df[display_df['email'].str.contains(search, na=False) | display_df['user_id'].astype(str).str.contains(search)]

    # 顯示表格
    st.dataframe(
        display_df[['email', 'tier', 'xp', 'energy', 'created_at', 'last_interaction_date']],
        use_container_width=True,
        column_config={
            "energy": st.column_config.ProgressColumn("電量", min_value=0, max_value=100, format="%d"),
            "created_at": st.column_config.DatetimeColumn("註冊時間", format="Y-M-D"),
        }
    )
    
    st.divider()
    
    # 管理員操作區
    st.subheader("✏️ 會員操作")
    c_edit1, c_edit2 = st.columns(2)
    
    with c_edit1:
        target_uid = st.text_input("請輸入 User ID 進行操作")
        
    with c_edit2:
        action = st.selectbox("執行動作", ["贈送電量", "贈送 XP", "升級會員", "停權封鎖"])
        
    if target_uid:
        # 顯示該會員當前狀態
        target_user = df_users[df_users['user_id'] == target_uid]
        if not target_user.empty:
            st.info(f"當前選中: {target_user.iloc[0]['email']} (Tier: {target_user.iloc[0]['tier']})")
            
            with st.form("admin_action"):
                val = 0
                if action in ["贈送電量", "贈送 XP"]:
                    val = st.number_input("數量", min_value=1, value=10)
                elif action == "升級會員":
                    new_tier = st.selectbox("選擇等級", ["intermediate", "advanced", "eternal"])
                
                if st.form_submit_button("確認執行"):
                    if action == "贈送電量":
                        current = target_user.iloc[0]['energy']
                        supabase.table("profiles").update({"energy": current + val}).eq("user_id", target_uid).execute()
                        # 寫入 Log
                        supabase.table("transaction_logs").insert({"user_id": target_uid, "amount": val, "reason": "客服贈送"}).execute()
                        st.success(f"已贈送 {val} 電量")
                        
                    elif action == "升級會員":
                        supabase.table("profiles").update({"tier": new_tier}).eq("user_id", target_uid).execute()
                        st.success(f"已升級為 {new_tier}")
        else:
            st.warning("找不到此 User ID")

# ==========================================
# PAGE 3: 成長與裂變
# ==========================================
elif page == "📈 成長與裂變":
    st.title("📈 病毒擴散分析")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🏆 超級推廣員 (Top Referrers)")
        # 這裡需要從 logs 分析誰帶來最多新用戶 (假設 reason='friend_register')
        # 這裡暫時模擬數據
        referral_data = {
            "User": ["klmeme2@gmail.com", "user_002", "user_003"],
            "Invited": [12, 8, 5],
            "Bonus XP": [60, 40, 25]
        }
        st.dataframe(referral_data, use_container_width=True)
        
    with c2:
        st.subheader("🗣️ 朋友評價回饋")
        df_feed = get_all_feedbacks()
        if not df_feed.empty:
            st.dataframe(df_feed[['score', 'comment', 'created_at']], use_container_width=True)
        else:
            st.info("尚無評價數據")

    st.subheader("🌪️ 轉換漏斗 (Funnel)")
    # 模擬數據，實際上需埋點追蹤
    funnel_data = dict(
        number=[1000, 600, 300, 50],
        stage=["點擊邀請連結", "進入訪客模式", "完成評分互動", "成功註冊會員"]
    )
    fig_funnel = px.funnel(funnel_data, x='number', y='stage')
    st.plotly_chart(fig_funnel, use_container_width=True)

# ==========================================
# PAGE 4: 財務與日誌
# ==========================================
elif page == "💰 財務與日誌":
    st.title("💰 系統日誌")
    
    st.subheader("📝 交易流水帳")
    st.dataframe(
        df_logs, 
        use_container_width=True,
        column_config={
            "created_at": st.column_config.DatetimeColumn("時間", format="MM-DD HH:mm"),
            "amount": st.column_config.NumberColumn("變動數值", format="%d")
        }
    )
    
    st.divider()
    st.subheader("⚠️ 異常監控")
    # 簡單分析是否有單日消耗過高的用戶
    if not df_logs.empty:
        high_usage = df_logs[df_logs['amount'] < -50] # 單次扣超過 50 點
        if not high_usage.empty:
            st.error("偵測到異常大量消耗：")
            st.dataframe(high_usage)
        else:
            st.success("目前無異常消耗紀錄。")
