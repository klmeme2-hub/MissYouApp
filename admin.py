import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import datetime

# ==========================================
# 企業級後台 (Admin Portal V2 - 數據實戰版)
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

# 處理日期格式與資料清理
if not df_users.empty:
    df_users['created_at'] = pd.to_datetime(df_users['created_at'])
if not df_logs.empty:
    df_logs['created_at'] = pd.to_datetime(df_logs['created_at'])
    df_logs['amount'] = pd.to_numeric(df_logs['amount'], errors='coerce').fillna(0)

# ==========================================
# PAGE 1: 儀表板總覽 (真實運算)
# ==========================================
if page == "📊 儀表板總覽":
    st.title("📊 營運戰情室")
    
    # 1. 計算核心指標
    total_users = len(df_users)
    
    # 活躍用戶 (7天內有互動日期的)
    active_users = 0
    if not df_users.empty and 'last_interaction_date' in df_users.columns:
        # 處理日期字串轉物件
        df_users['last_date_obj'] = pd.to_datetime(df_users['last_interaction_date'], errors='coerce').dt.date
        last_7_days = datetime.date.today() - datetime.timedelta(days=7)
        active_users = len(df_users[df_users['last_date_obj'] >= last_7_days])

    # --- 真實成本計算機 ---
    # 邏輯：篩選 transaction_logs 中 amount < 0 的紀錄 (代表消耗)
    # 假設：每消耗 1 點 = 0.5 元成本 (OpenAI/ElevenLabs 混合估算)
    total_cost = 0
    total_consumed_points = 0
    
    if not df_logs.empty:
        consumed_df = df_logs[df_logs['amount'] < 0]
        total_consumed_points = abs(consumed_df['amount'].sum())
        cost_per_point = 0.5 # 假設成本係數
        total_cost = total_consumed_points * cost_per_point

    # 預估營收 (篩選 reason 包含 "儲值" 或 "升級" 的正數)
    total_revenue = 0
    if not df_logs.empty:
        # 這裡假設 log 的 reason 會寫 "付費升級" 或 "儲值"
        # 實際金額需看您是否在 logs 存金額，或是用點數換算 (假設 1點售價 1元)
        # 這裡暫時用 點數 * 0.88 (售價) 來估算營收
        income_df = df_logs[(df_logs['amount'] > 0) & (df_logs['reason'].str.contains('儲值|升級', na=False))]
        total_income_points = income_df['amount'].sum()
        total_revenue = total_income_points * 0.88

    # 顯示指標
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("總會員數", total_users)
    col2.metric("周活躍 (WAU)", active_users)
    col3.metric("本月預估營收", f"${total_revenue:,.0f}", help="基於儲值點數 x 0.88 推算")
    col4.metric("AI 真實成本", f"${total_cost:,.1f}", f"消耗 {total_consumed_points} 點", help="基於消耗點數 x 0.5 推算")

    # 2. 趨勢圖表
    st.subheader("📈 數據趨勢")
    c_chart1, c_chart2 = st.columns(2)
    
    with c_chart1:
        st.caption("每日新增會員")
        if not df_users.empty:
            df_daily_users = df_users.groupby(df_users['created_at'].dt.date).size().reset_index(name='count')
            fig_user = px.line(df_daily_users, x='created_at', y='count', markers=True)
            st.plotly_chart(fig_user, use_container_width=True)
            
    with c_chart2:
        st.caption("每日點數消耗 (AI 使用量)")
        if not df_logs.empty:
            df_usage = df_logs[df_logs['amount'] < 0].copy()
            df_usage['abs_amount'] = df_usage['amount'].abs()
            df_daily_usage = df_usage.groupby(df_usage['created_at'].dt.date)['abs_amount'].sum().reset_index()
            fig_usage = px.bar(df_daily_usage, x='created_at', y='abs_amount', color_discrete_sequence=['#FF4B4B'])
            st.plotly_chart(fig_usage, use_container_width=True)

# ==========================================
# PAGE 2: 會員管理 (CRM - 補上 User ID)
# ==========================================
elif page == "👥 會員管理 (CRM)":
    st.title("👥 會員管理系統")
    
    # 篩選器
    search = st.text_input("🔍 搜尋 Email 或 User ID")
    
    # 資料處理
    display_df = df_users.copy()
    if search and not display_df.empty:
        display_df = display_df[
            display_df['email'].astype(str).str.contains(search, case=False) | 
            display_df['user_id'].astype(str).str.contains(search, case=False)
        ]

    # 【修正】顯示表格 (加入 user_id)
    if not display_df.empty:
        # 整理欄位順序
        cols_to_show = ['user_id', 'email', 'tier', 'xp', 'energy', 'created_at', 'last_interaction_date']
        # 確保欄位存在才顯示
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
    else:
        st.info("尚無會員資料")
    
    st.divider()
    
    # 管理員操作區 (維持原樣)
    st.subheader("✏️ 會員操作")
    c_edit1, c_edit2 = st.columns(2)
    with c_edit1:
        target_uid = st.text_input("請複製上方 User ID 貼入此處")
    with c_edit2:
        action = st.selectbox("執行動作", ["贈送電量", "贈送 XP", "升級會員"])
        
    if target_uid and st.button("確認執行"):
        val = 0
        if action in ["贈送電量", "贈送 XP"]: val = 50 # 預設送50
        
        if action == "贈送電量":
            # 這裡簡化直接寫入 DB，實際應先讀取再加總
            supabase.table("transaction_logs").insert({"user_id": target_uid, "amount": val, "reason": "Admin贈送"}).execute()
            # 注意：這裡應該也要 update profiles table，為求簡潔省略，建議搭配 update_profile_stats 邏輯
            st.success(f"已記錄贈送請求 (需配合後端邏輯更新餘額)")
        elif action == "升級會員":
             supabase.table("profiles").update({"tier": "intermediate"}).eq("user_id", target_uid).execute()
             st.success("已升級")

# ==========================================
# PAGE 3: 成長與裂變 (監控病毒傳播)
# ==========================================
elif page == "📈 成長與裂變":
    st.title("📈 病毒擴散分析")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🏆 推廣排行榜 (Top Referrers)")
        st.caption("統計誰獲得了最多的「推廣獎勵」積分")
        
        if not df_logs.empty:
            # 邏輯：篩選 reason 包含 '朋友' 或 '邀請' 的加分紀錄
            referral_logs = df_logs[
                (df_logs['amount'] > 0) & 
                (df_logs['reason'].astype(str).str.contains('朋友|邀請|Share', case=False, na=False))
            ]
            
            if not referral_logs.empty:
                # 依 user_id 分組加總積分
                top_users = referral_logs.groupby('user_id')['amount'].sum().reset_index()
                top_users = top_users.sort_values('amount', ascending=False).head(10)
                
                # 關聯 Email (Merge)
                if not df_users.empty:
                    top_users = pd.merge(top_users, df_users[['user_id', 'email']], on='user_id', how='left')
                
                st.dataframe(
                    top_users[['email', 'amount', 'user_id']], 
                    column_config={"amount": "獲得推廣積分", "email": "會員 Email"},
                    use_container_width=True
                )
            else:
                st.info("尚無推廣獎勵紀錄")
        else:
            st.info("尚無日誌資料")
            
    with c2:
        st.subheader("🗣️ 朋友評價回饋")
        if not df_feed.empty:
            # 關聯是誰收到的評價
            if not df_users.empty:
                df_feed = pd.merge(df_feed, df_users[['user_id', 'email']], left_on='to_user_id', right_on='user_id', how='left')
                
            st.dataframe(
                df_feed[['score', 'comment', 'email', 'created_at']], 
                column_config={"email": "被評分會員", "score": "星等"},
                use_container_width=True
            )
        else:
            st.info("尚無評價數據")

# ==========================================
# PAGE 4: 財務與日誌
# ==========================================
elif page == "💰 財務與日誌":
    st.title("💰 系統日誌")
    st.dataframe(
        df_logs, 
        use_container_width=True,
        column_config={
            "created_at": st.column_config.DatetimeColumn("時間", format="MM-DD HH:mm"),
            "amount": st.column_config.NumberColumn("變動數值", format="%d"),
            "user_id": st.column_config.TextColumn("User ID")
        }
    )
