import streamlit as st
import requests
from openai import OpenAI
from supabase import create_client, Client
import numpy as np
import os
import json
import io
from pydub import AudioSegment # 引入 pydub
from pydub.playback import play # 引入播放功能 (如果需要)
from pydub.exceptions import CouldntDecodeError # 錯誤處理

# --- 引入模組 ---
from .auth import get_current_user_id
from .config import ROLE_MAPPING

def get_tts_engine_type(profile):
    """決定語音引擎"""
    if not profile: return "openai"
    tier = profile.get('tier', 'basic')
    if tier in ['advanced', 'eternal', 'intermediate']:
        return "elevenlabs"
    return "openai"

def generate_speech(text, tier):
    """生成語音 (雙引擎)"""
    engine = get_tts_engine_type(tier) # 根據 tier 決定引擎
    
    if engine == "elevenlabs":
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{st.secrets['VOICE_ID']}"
            headers = {"xi-api-key": st.secrets['ELEVENLABS_API_KEY'], "Content-Type": "application/json"}
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.4, "similarity_boost": 0.7}
            }
            res = requests.post(url, json=data, headers=headers)
            if res.status_code == 200:
                return res.content
            else:
                print(f"ElevenLabs Error: {res.text}")
        except Exception as e:
            print(f"ElevenLabs Connection Error: {e}")
    
    # Fallback to OpenAI TTS
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        return response.content
    except Exception as e:
        print(f"OpenAI TTS Error: {e}")
        return None

# --- 音訊處理 ---

def upload_audio_file(supabase, role, audio_bytes, file_type="nickname"):
    """通用上傳函數"""
    user_id = get_current_user_id()
    if not user_id: return False
    try:
        safe_role = ROLE_MAPPING.get(role, "others")
        file_path = f"{user_id}/{file_type}_{safe_role}.mp3"
        
        # 處理上傳的 BytesIO 物件
        supabase.storage.from_("audio_clips").upload(
            file_path, 
            io.BytesIO(audio_bytes), # 確保傳入 BytesIO
            file_options={"content-type": "audio/mpeg", "upsert": "true"}
        )
        return True
    except Exception as e:
        print(f"Upload Error: {e}")
        return False

def get_audio_bytes(supabase, role, file_type="nickname"):
    """通用下載函數"""
    user_id = get_current_user_id()
    if not user_id: return None
    try:
        safe_role = ROLE_MAPPING.get(role, "others")
        file_path = f"{user_id}/{file_type}_{safe_role}.mp3"
        return supabase.storage.from_("audio_clips").download(file_path)
    except Exception as e:
        print(f"Download Error: {e}")
        return None

def train_voice_sample(audio_bytes):
    """上傳訓練樣本至 ElevenLabs"""
    try:
        voice_id = st.secrets["VOICE_ID"]
        api_key = st.secrets["ELEVENLABS_API_KEY"]
        url = f"https://api.elevenlabs.io/v1/voices/{voice_id}/edit"
        
        # 確保 audio_bytes 是 BytesIO 物件
        files = {'files': ('training_sample.mp3', io.BytesIO(audio_bytes), 'audio/mpeg')}
        requests.post(url, headers={"xi-api-key": api_key}, data={'name': 'Clone'}, files=files)
        return True
    except Exception as e: 
        print(f"Train Upload Error: {e}")
        return False

def merge_audio_clips(intro_bytes, main_bytes):
    """合併音訊"""
    try:
        if not intro_bytes or len(intro_bytes) < 100: return main_bytes
        
        # 確保讀取 BytesIO
        intro = AudioSegment.from_file(io.BytesIO(intro_bytes))
        main = AudioSegment.from_file(io.BytesIO(main_bytes))
        
        silence = AudioSegment.silent(duration=200) # 0.2秒靜音
        combined = intro + silence + main
        
        buffer = io.BytesIO()
        combined.export(buffer, format="mp3")
        return buffer.getvalue()
    except Exception as e:
        print(f"Merge Error: {e}")
        return main_bytes
