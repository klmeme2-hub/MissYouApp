import streamlit as st
from modules import audio, database

def calculate_similarity(supabase, user_id, role):
    """
    計算聲音相似度
    回傳: (current_score, next_hint, next_gain)
    """
    score = 50 # 基礎分
    next_hint = "已達目前等級上限"
    next_gain = 0
    
    # 1. 檢查 Step 1 (權重 10%)
    has_step1 = audio.get_audio_bytes(supabase, role, "opening") is not None
    if has_step1:
        score += 10
    else:
        return score, "完成「Step 1 口頭禪/喚名」訓練", 10

    # 2. 檢查 Step 2 (權重 5%)
    has_step2 = audio.get_audio_bytes(supabase, role, "tone_comfort") is not None
    if has_step2:
        score += 5
    else:
        return score, "完成「Step 2 安慰語氣」訓練", 5

    # 3. 檢查 Step 3 (權重 5%)
    has_step3 = audio.get_audio_bytes(supabase, role, "tone_encourage") is not None
    if has_step3:
        score += 5
    else:
        return score, "完成「Step 3 鼓勵語氣」訓練", 5
        
    # 4. 檢查 Step 4 (權重 5%)
    has_step4 = audio.get_audio_bytes(supabase, role, "tone_humor") is not None
    if has_step4:
        score += 5
    else:
        return score, "完成「Step 4 詼諧語氣」訓練", 5
    
    # 5. 檢查回憶補完 (每題 3%，上限 5 題 = 15%)
    memories = database.get_memories_by_role(supabase, role)
    # 簡單過濾掉標記為 "已略過" 的項目
    valid_mems = [m for m in memories if "(已略過)" not in m['content']]
    mem_count = len(valid_mems)
    
    mem_score = min(15, mem_count * 3)
    score += mem_score
    
    if mem_count < 5:
        return score, f"前往「回憶補完」再回答 {5 - mem_count} 題", 3
        
    # 6. 滿分狀態 (90%)
    return score, "已達目前等級上限 (請期待專業版)", 0
