import streamlit as st
import requests
import io
from openai import OpenAI
from pydub import AudioSegment
from .auth import get_current_user_id
from .config import ROLE_MAPPING

def get_tts_engine_type(profile):
    """
    根據會員等級決定語音引擎
    回傳: 'elevenlabs' 或 'openai'
    """
    if not profile:
        return "openai"
        
    tier = profile.get('tier', 'basic')
    
    # 高級與永恆會員固定使用 ElevenLabs
    if tier in ['advanced', 'eternal']:
        return "elevenlabs"
    
    # 中級會員目前也開放使用 ElevenLabs (或您可以根據試用期邏輯修改)
    if tier == 'intermediate':
        return "elevenlabs"
        
    # 初級會員預設使用 OpenAI (成本控制)
    return "openai"

def generate_speech(text, tier):
    """
    統一語音生成接口
    """
    # 這裡我們直接傳入 tier 來判斷，或是先呼叫上面的 get_tts_engine_type
    engine = "elevenlabs" if tier in ['intermediate', 'advanced', 'eternal'] else "openai"

    if engine == "elevenlabs":
        try:
            voice_id = st.secrets["VOICE_ID"]
            api_key = st.secrets["ELEVENLABS_API_KEY"]
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "xi-api-key": api_key,
                "Content-Type": "application/json"
            }
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.4, "similarity_boost": 0.7}
            }
            res = requests.post(url, json=data, headers=headers)
            if res.status_code == 200:
                return res.content
        except Exception as e:
            print(f"ElevenLabs Error: {e}")
    
    # 基礎版或備用方案：OpenAI TTS
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

def upload_nickname_audio(supabase, role, audio_bytes):
    """上傳真實暱稱錄音"""
    user_id = get_current_user_id()
    if not user_id: return False
    try:
        safe_role = ROLE_MAPPING.get(role, "others")
        file_path = f"{user_id}/nickname_{safe_role}.mp3"
        # 使用 upsert=true 覆蓋舊檔
        supabase.storage.from_("audio_clips").upload(
            file_path, 
            audio_bytes, 
            file_options={"content-type": "audio/mpeg", "upsert": "true"}
        )
        return True
    except:
        return False

def get_nickname_audio_bytes(supabase, role):
    """下載真實暱稱錄音"""
    user_id = get_current_user_id()
    if not user_id: return None
    try:
        safe_role = ROLE_MAPPING.get(role, "others")
        file_path = f"{user_id}/nickname_{safe_role}.mp3"
        return supabase.storage.from_("audio_clips").download(file_path)
    except:
        return None

def train_voice_sample(audio_bytes):
    """上傳訓練樣本至 ElevenLabs"""
    try:
        voice_id = st.secrets["VOICE_ID"]
        api_key = st.secrets["ELEVENLABS_API_KEY"]
        url = f"https://api.elevenlabs.io/v1/voices/{voice_id}/edit"
        files = {'files': ('training_sample.mp3', audio_bytes, 'audio/mpeg')}
        requests.post(url, headers={"xi-api-key": api_key}, data={'name': 'Clone'}, files=files)
        return True
    except:
        return False

def merge_audio_clips(intro_bytes, main_bytes):
    """合併真實錄音與 AI 語音"""
    try:
        if not intro_bytes or len(intro_bytes) < 100:
            return main_bytes
        
        intro = AudioSegment.from_file(io.BytesIO(intro_bytes))
        main = AudioSegment.from_file(io.BytesIO(main_bytes))
        silence = AudioSegment.silent(duration=200)
        
        combined = intro + silence + main
        
        buffer = io.BytesIO()
        combined.export(buffer, format="mp3")
        return buffer.getvalue()
    except Exception as e:
        print(f"Merge Error: {e}")
        return main_bytes
