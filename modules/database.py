import streamlit as st
from supabase import create_client
import random
import string
from datetime import datetime, date
from .auth import get_current_user_id

@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- 積分與個人檔案 ---
def get_user_profile(supabase, user_id=None):
    if not user_id: user_id = get_current_user_id()
    if not user_id: return None
    try:
        res = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
        if res.data: return res.data[0]
        else:
            # 初始化
            data = {"user_id": user_id, "xp": 0, "energy": 30, "tier": "basic", "last_interaction_date": str(date.today())}
            supabase.table("profiles").insert(data).execute()
            return data
    except: return {"xp": 0, "energy": 30, "tier": "basic"}

def update_profile_stats(supabase, user_id, xp_delta=0, energy_delta=0, log_reason=""):
    try:
        # 使用 RPC 或直接更新 (這裡簡化為直接更新，高併發建議用 RPC)
        profile = get_user_profile(supabase, user_id)
        new_xp = max(0, profile.get('xp', 0) + xp_delta)
        new_energy = max(0, profile.get('energy', 0) + energy_delta)
        
        supabase.table("profiles").update({"xp": new_xp, "energy": new_energy}).eq("user_id", user_id).execute()
        
        if log_reason:
            supabase.table("transaction_logs").insert({
                "user_id": user_id, "amount": xp_delta if xp_delta != 0 else energy_delta, "reason": log_reason
            }).execute()
        return True
    except: return False

def check_daily_interaction(supabase, user_id):
    """電子雞邏輯：親友登入時觸發"""
    try:
        profile = get_user_profile(supabase, user_id)
        last_str = profile.get('last_interaction_date', str(date.today()))
        last_date = datetime.strptime(last_str, "%Y-%m-%d").date()
        today = date.today()
        
        if last_date < today:
            days_diff = (today - last_date).days
            penalty = max(0, days_diff - 1) # 沒來的日子才扣
            
            # 扣除缺席點數 + 今日簽到獎勵(+1)
            net_change = 1 - penalty
            update_profile_stats(supabase, user_id, energy_delta=net_change, log_reason=f"每日結算(缺席{penalty}天)")
            
            supabase.table("profiles").update({"last_interaction_date": str(today)}).eq("user_id", user_id).execute()
            return f"日安！今日能量 +1" + (f" (已扣除缺席 {penalty} 點)" if penalty > 0 else "")
    except: return None

def upgrade_tier(supabase, user_id, new_tier, energy_bonus=0, xp_bonus=0):
    try:
        update_profile_stats(supabase, user_id, xp_delta=xp_bonus, energy_delta=energy_bonus, log_reason=f"付費升級 {new_tier}")
        supabase.table("profiles").update({"tier": new_tier}).eq("user_id", user_id).execute()
        return True
    except: return False

# --- 記憶與人設 (RAG) ---
def save_memory_fragment(supabase, role, question, answer):
    user_id = get_current_user_id()
    full = f"【關於{question}】：{answer}"
    # Google 方案不一定需要 embedding，但為了相容性我們先存文字
    data = {"user_id": user_id, "role": role, "content": full} 
    # 這裡省略 embedding，因為 Gemini Flash 可以直接讀大量文字，或是之後再補
    # 若 table constraint 必填 embedding，可塞個空 list 或 0
    supabase.table("memories").insert(data).execute() 
    return True

def get_all_memories_text(supabase, role):
    """SaaS 升級版：直接撈出該角色所有記憶文本 (給 Gemini 讀)"""
    user_id = get_current_user_id()
    try:
        res = supabase.table("memories").select("content").eq("user_id", user_id).eq("role", role).execute()
        return "\n".join([m['content'] for m in res.data])
    except: return ""

def save_persona_summary(supabase, role, content):
    user_id = get_current_user_id()
    try:
        # Upsert logic
        current = supabase.table("personas").select("id").eq("user_id", user_id).eq("role", role).execute()
        if current.data:
            supabase.table("personas").update({"content": content}).eq("id", current.data[0]['id']).execute()
        else:
            supabase.table("personas").insert({"user_id": user_id, "role": role, "content": content}).execute()
    except: pass

def load_persona(supabase, role):
    # 取得當前目標ID (若是訪客則取 owner)
    target_id = get_current_user_id()
    try:
        res = supabase.table("personas").select("content").eq("user_id", target_id).eq("role", role).execute()
        return res.data[0]['content'] if res.data else None
    except: return None

# --- 分享 ---
def create_share_token(supabase, role):
    user_id = get_current_user_id()
    token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    supabase.table("share_tokens").insert({"user_id": user_id, "role": role, "token": token}).execute()
    return token

def validate_token(supabase, token):
    try:
        res = supabase.table("share_tokens").select("*").eq("token", token).execute()
        if res.data: return res.data[0]
    except: return None
