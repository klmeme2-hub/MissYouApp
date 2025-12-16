import streamlit as st

def login_user(supabase, email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response
    except: return None

def signup_user(supabase, email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        return response
    except: return None

def get_current_user_id():
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user.user.id
    if "guest_data" in st.session_state and st.session_state.guest_data:
        return st.session_state.guest_data['owner_id']
    return None
