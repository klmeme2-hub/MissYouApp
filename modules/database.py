# ... (前面的 import 和 init_supabase 維持不變) ...
# ... (get_user_profile 等函數維持不變) ...

# 修改 1: 儲存人設時，多存一個 member_nickname
def save_persona_summary(supabase, role, content, member_nickname=None):
    user_id = get_current_user_id()
    if not user_id: return
    try:
        # 準備要更新的資料
        data = {"user_id": user_id, "role": role, "content": content}
        if member_nickname:
            data["member_nickname"] = member_nickname

        # 檢查是否存在
        res = supabase.table("personas").select("id").eq("user_id", user_id).eq("role", role).execute()
        if res.data:
            supabase.table("personas").update(data).eq("id", res.data[0]['id']).execute()
        else:
            supabase.table("personas").insert(data).execute()
    except Exception as e: print(f"Save Persona Error: {e}")

# 修改 2: 讀取人設時，把 member_nickname 也抓出來
def load_persona(supabase, role):
    # 這裡的邏輯：如果是訪客，get_current_user_id 會抓到 owner_id
    target_id = get_current_user_id()
    if not target_id: return None
    try:
        # 多選取 member_nickname 欄位
        res = supabase.table("personas").select("content, member_nickname").eq("user_id", target_id).eq("role", role).execute()
        if res.data:
            return res.data[0] # 回傳整個字典 {'content': '...', 'member_nickname': '阿強'}
        return None
    except: return None

# ... (其他的 create_share_token 等函數維持不變) ...
