import streamlit as st
from supabase import create_client
from openai import OpenAI
import random
import string
from datetime import datetime, date
# 使用相對路徑引用 auth 模組
from .auth import get_current_user_id

@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ==========================================
# 1. 使用者檔案與積分系統 (SaaS 核心)
# ==========================================

def get_user_profile(supabase, user_id=None):
    if not user_id:
        user_id = get_current_user_id()
    if not user_id: return None
    
    try:
        res = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]
        else:
            # 初始化新用戶
            data = {
                "user_id": user_id, 
                "xp": 0, 
                "energy": 30, 
                "tier": "basic",
                "last_interaction_date": str(date.today())
            }
            supabase.table("profiles").insert(data).execute()
            return data
    except Exception as e:
        print(f"Profile Error: {e}")
        return {"xp": 0, "energy": 30, "tier": "basic"}

def update_profile_stats(supabase, user_id, xp_delta=0, energy_delta=0, log_reason=""):
    """更新 XP 或 電量，並寫入 Log"""
    try:
        profile = get_user_profile(supabase, user_id)
        # 確保數值不低於 0
        new_xp = max(0, profile.get('xp', 0) + xp_delta)
        new_energy = max(0, profile.get('energy', 30) + energy_delta)
        
        supabase.table("profiles").update({
            "xp": new_xp,
            "energy": new_energy
        }).eq("user_id", user_id).execute()
        
        if log_reason:
            supabase.table("transaction_logs").insert({
                "user_id": user_id,
                "amount": xp_delta if xp_delta != 0 else energy_delta,
                "reason": log_reason
            }).execute()
        return True
    except: return False

def check_daily_interaction(supabase, user_id):
    """電子雞邏輯：每日扣點與簽到"""
    try:
        profile = get_user_profile(supabase, user_id)
        last_str = profile.get('last_interaction_date', str(date.today()))
        last_date = datetime.strptime(last_str, "%Y-%m-%d").date()
        today = date.today()
        
        if last_date < today:
            days_diff = (today - last_date).days
            penalty = max(0, days_diff - 1)
            
            # 扣除缺席 + 今日簽到獎勵(+1)
            net_change = 1 - penalty
            update_profile_stats(supabase, user_id, energy_delta=net_change, log_reason=f"每日結算(缺席{penalty}天)")
            
            supabase.table("profiles").update({"last_interaction_date": str(today)}).eq("user_id", user_id).execute()
            return f"日安！今日能量 +1" + (f" (已扣除缺席 {penalty} 點)" if penalty > 0 else "")
    except: return None

def upgrade_tier(supabase, user_id, new_tier, energy_bonus=0, xp_bonus=0):
    try:
        update_profile_stats(supabase, user_id, xp_delta=xp_bonus, energy_delta=energy_bonus, log_reason=f"升級 {new_tier}")
        supabase.table("profiles").update({"tier": new_tier}).eq("user_id", user_id).execute()
        return True
    except: return False

def submit_feedback(supabase, to_user_id, score, comment):
    try:
        data = {"to_user_id": to_user_id, "score": score, "comment": comment}
        supabase.table("feedbacks").insert(data).execute()
        update_profile_stats(supabase, to_user_id, xp_delta=1, log_reason="朋友評分獎勵")
        return True
    except: return False

def get_feedbacks(supabase):
    user_id = get_current_user_id()
    try:
        res = supabase.table("feedbacks").select("*").eq("to_user_id", user_id).order('created_at', desc=True).execute()
        return res.data
    except: return []

# ==========================================
# 2. 記憶與 RAG 系統 (包含被遺漏的函數)
# ==========================================

def get_embedding(text):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def get_memories_by_role(supabase, role):
    """
    【關鍵修復】取得該角色所有的回憶列表
    用於 Tab 4 右側的「回憶存摺」顯示
    """
    user_id = get_current_user_id()
    try:
        # 使用 user_id 過濾，並按時間倒序排列
        res = supabase.table("memories").select("*").eq("user_id", user_id).eq("role", role).order('id', desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Get Memories Error: {e}")
        return []

def get_all_memories_text(supabase, role):
    """SaaS 升級版：直接撈出該角色所有記憶文本 (給 Gemini 讀)"""
    user_id = get_current_user_id()
    try:
        res = supabase.table("memories").select("content").eq("user_id", user_id).eq("role", role).execute()
        return "\n".join([m['content'] for m in res.data])
    except: return ""

def save_memory_fragment(supabase, role, question, answer):
    user_id = get_current_user_id()
    if not user_id: return False
    
    full_content = f"【關於{question}】：{answer}"
    try:
        # 刪除舊的 (避免重複題目)
        existing = get_memories_by_role(supabase, role)
        for mem in existing:
            if mem['content'].startswith(f"【關於{question}】"):
                supabase.table("memories").delete().eq("id", mem['id']).execute()
    except: pass
    
    # 插入新的
    embedding = get_embedding(full_content)
    data = {"user_id": user_id, "role": role, "content": full_content, "embedding": embedding}
    supabase.table("memories").insert(data).execute()
    return True

def search_relevant_memories(supabase, role, query_text):
    try:
        query_vec = get_embedding(query_text)
        res = supabase.rpc("match_memories", {"query_embedding": query_vec, "match_threshold": 0.5, "match_count": 3, "search_role": role}).execute()
        return "\n".join([item['content'] for item in res.data])
    except: return ""

# ==========================================
# 3. 人設與分享
# ==========================================

def save_persona_summary(supabase, role, content):
    user_id = get_current_user_id()
    if not user_id: return
    try:
        res = supabase.table("personas").select("id").eq("user_id", user_id).eq("role", role).execute()
        if res.data:
            supabase.table("personas").update({"content": content}).eq("id", res.data[0]['id']).execute()
        else:
            data = {"user_id": user_id, "role": role, "content": content}
            supabase.table("personas").insert(data).execute()
    except: pass

def load_persona(supabase, role):
    target_id = get_current_user_id()
    if not target_id: return None
    try:
        res = supabase.table("personas").select("content").eq("user_id", target_id).eq("role", role).execute()
        return res.data[0]['content'] if res.data else None
    except: return None

def create_share_token(supabase, role):
    user_id = get_current_user_id()
    try:
        exist = supabase.table("share_tokens").select("token").eq("user_id", user_id).eq("role", role).execute()
        if exist.data: return exist.data[0]['token']
        token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        supabase.table("share_tokens").insert({"user_id": user_id, "role": role, "token": token}).execute()
        return token
    except: return None

def validate_token(supabase, token):
    try:
        res = supabase.table("share_tokens").select("*").eq("token", token).execute()
        if res.data: return res.data[0]
        return None
    except: return None
