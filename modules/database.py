import streamlit as st
from supabase import create_client
from openai import OpenAI
import random
import string
# 確保引用路徑正確
from .auth import get_current_user_id 

# 初始化 Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

# 初始化 OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ==========================================
# 新增功能區：積分與個人檔案系統
# ==========================================

def get_user_profile(supabase):
    """取得會員的積分與等級"""
    user_id = get_current_user_id()
    if not user_id: return None
    try:
        res = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]
        else:
            # 如果沒有檔案，初始化一個
            data = {"user_id": user_id, "resonance_score": 0, "current_tier": "trainee"}
            supabase.table("profiles").insert(data).execute()
            return data
    except Exception as e:
        print(f"Profile error: {e}")
        return {"resonance_score": 0, "current_tier": "trainee"}

def add_resonance_score(supabase, user_id, points):
    """增加共鳴值"""
    try:
        # 先取得目前分數
        res = supabase.table("profiles").select("resonance_score").eq("user_id", user_id).execute()
        current = res.data[0]['resonance_score'] if res.data else 0
        new_score = current + points
        
        # 更新分數
        supabase.table("profiles").update({"resonance_score": new_score}).eq("user_id", user_id).execute()
        return new_score
    except Exception as e:
        print(f"Score update error: {e}")
        return 0

def submit_feedback(supabase, to_user_id, score, comment):
    """提交朋友的評價"""
    try:
        data = {
            "to_user_id": to_user_id,
            "score": score,
            "comment": comment
        }
        supabase.table("feedbacks").insert(data).execute()
        
        # 同步增加積分
        add_resonance_score(supabase, to_user_id, score)
        return True
    except Exception as e: 
        print(f"Feedback error: {e}")
        return False

def get_feedbacks(supabase):
    """取得給自己的評價"""
    user_id = get_current_user_id()
    try:
        res = supabase.table("feedbacks").select("*").eq("to_user_id", user_id).order('created_at', desc=True).execute()
        return res.data
    except: return []

# ==========================================
# 原有功能區：RAG 與記憶
# ==========================================

def get_embedding(text):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def get_memories_by_role(supabase, role):
    user_id = get_current_user_id()
    try:
        response = supabase.table("memories").select("*").eq("user_id", user_id).eq("role", role).order('id', desc=True).execute()
        return response.data
    except: return []

def save_memory_fragment(supabase, role, question, answer):
    user_id = get_current_user_id()
    if not user_id: return False
    
    full_content = f"【關於{question}】：{answer}"
    try:
        existing = get_memories_by_role(supabase, role)
        for mem in existing:
            if mem['content'].startswith(f"【關於{question}】"):
                supabase.table("memories").delete().eq("id", mem['id']).execute()
    except: pass
    
    embedding = get_embedding(full_content)
    data = {"user_id": user_id, "role": role, "content": full_content, "embedding": embedding}
    supabase.table("memories").insert(data).execute()
    return True

def search_relevant_memories(supabase, role, query_text):
    try:
        query_vec = get_embedding(query_text)
        response = supabase.rpc(
            "match_memories",
            {"query_embedding": query_vec, "match_threshold": 0.5, "match_count": 3, "search_role": role}
        ).execute()
        return "\n".join([item['content'] for item in response.data])
    except: return ""

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
    except Exception as e: print(e)

def load_persona(supabase, role):
    # 這裡需要修改：
    # 如果是訪客模式，讀取的是 owner_id 的資料，而不是當前登入者 (因為訪客沒登入)
    # 但 get_current_user_id() 在 auth.py 已經處理好這個邏輯了 (會回傳 owner_id)
    # 所以直接呼叫即可
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
        data = {"user_id": user_id, "role": role, "token": token}
        supabase.table("share_tokens").insert(data).execute()
        return token
    except: return None

def validate_token(supabase, token):
    try:
        res = supabase.table("share_tokens").select("*").eq("token", token).execute()
        if res.data: return res.data[0]
        return None
    except: return None
