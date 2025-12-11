# modules/database.py
import streamlit as st
from supabase import create_client
from openai import OpenAI
import random
import string
from modules.auth import get_current_user_id

# 初始化 Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

# 初始化 OpenAI (用於 Embedding)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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
    
    # 刪除舊的
    try:
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
    user_id = get_current_user_id()
    try:
        res = supabase.table("personas").select("content").eq("user_id", user_id).eq("role", role).execute()
        return res.data[0]['content'] if res.data else None
    except: return None

def load_all_roles(supabase):
    try:
        res = supabase.table("personas").select("role").execute()
        return [i['role'] for i in res.data]
    except: return []

# --- 分享功能 ---
def create_share_token(supabase, role):
    user_id = get_current_user_id()
    try:
        # 檢查是否已存在
        exist = supabase.table("share_tokens").select("token").eq("user_id", user_id).eq("role", role).execute()
        if exist.data: return exist.data[0]['token']
        
        # 生成新 Token
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
