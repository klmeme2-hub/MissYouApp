import streamlit as st
from modules import ui, database

def render(supabase, user_id, xp):
    st.subheader("💎 會員權益與積分規則")
    
    # 這裡移除 expanded=True 以保持版面整潔，並簡化標題
    with st.expander("ℹ️ 查看積分獲取方式 (點擊展開)"):
        st.write("- 🎤 **錄製口頭禪/完成腳本**：各 +1 點 (每步驟限一次)")
        st.write("- 🤝 **分享給朋友** (使用邀請碼登入)：+1 點/人")
        st.write("- ⭐ **朋友評分**：+1 點/人")
        st.write("- 👤 **成功邀請註冊**：**+10 點/人** (最強攻略！)")

    st.divider()
    # ... (下方解鎖方案邏輯維持不變) ...
    st.subheader("🚀 解鎖方案")

    c1, c2, c3 = st.columns(3)
    with c1:
        ui.render_dashboard_card("免費解鎖", "20 XP")
        st.write("累積滿 20 點 XP，即可免費解鎖「家人角色」權限。")
        if st.button("檢查資格", key="check_xp"):
            if xp >= 20: st.success("✅ 您已符合資格！")
            else: st.error(f"還差 {20-xp} 點 XP")

    with c2:
        ui.render_dashboard_card("中級守護者", "$99")
        st.write("- **免拉人直接解鎖**")
        st.write("- **贈送 99 點電量**")
        st.write("- **7天 高級語音試用**")
        if st.button("💰 付費解鎖中級", key="pay_mid"):
            result = database.upgrade_tier(supabase, user_id, "intermediate", energy_bonus=99, xp_bonus=20)
            if result == "success":
                st.balloons()
                st.success("🎉 升級成功！")
                st.rerun()
            elif result == "already_upgraded":
                st.warning("您已經是中級或更高級會員。")
            else: st.error("升級失敗。")

    with c3:
        ui.render_dashboard_card("高級刻錄師", "$599")
        st.write("- **解鎖 擬真版 (ElevenLabs)**")
        st.write("- **贈送 599 點電量**")
        st.write("- **優先體驗新功能**")
        if st.button("💰 付費解鎖高級", key="pay_high"):
            result = database.upgrade_tier(supabase, user_id, "advanced", energy_bonus=599, xp_bonus=20)
            if result == "success":
                st.balloons()
                st.success("🎉 尊榮升級成功！")
                st.rerun()
            elif result == "already_upgraded":
                st.warning("您已經是高級會員。")
            else: st.error("升級失敗。")

    st.divider()
    st.error("♾️ **永恆上鏈 ($2599)**：區塊鏈永久存證 (請洽客服)")
