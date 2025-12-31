import streamlit as st

st.set_page_config(page_title="隱私權政策 - MetaVoice", page_icon="🛡️", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    h1, h2, h3 { color: #FAFAFA !important; }
    p, li { font-size: 16px; line-height: 1.6; color: #DDD; }
    .highlight { color: #FF4B4B; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ 隱私權政策 (Privacy Policy)")
st.caption("生效日期：2026年1月1日")

st.markdown("""
### 1. 我們收集的資訊
為了提供數位分身服務，我們需要收集：
*   **帳戶資訊：** Email、加密密碼。
*   **聲紋數據：** 您上傳的錄音檔案及語音特徵值。
*   **個人回憶：** 您輸入的文字腳本與對話紀錄。
*   **互動數據：** 對話紀錄、評分、點數變動。

### 2. 聲紋數據的特殊處理
**这是我們最重視的部分。**
*   **用途限制：** 您的聲音樣本僅用於建立 **您專屬的 AI 語音模型**，絕不用於平台其他通用模型的訓練。
*   **第三方處理：** 您的音訊數據將加密傳輸至我們的 AI 技術合作夥伴（如 ElevenLabs, OpenAI, Google）進行處理，這些夥伴均受嚴格的數據保護協議約束。

### 3. 資訊的使用方式
*   提供語音合成服務。
*   計算會員等級與電量。
*   防止詐欺與濫用。

### 4. 資訊的分享與揭露
除以下情況外，我們不會分享您的資訊：
*   **經您同意：** 當您分享「邀請碼」給親友時，即代表同意親友存取您的 AI 分身。
*   **法律要求：** 若涉及詐騙調查，我們將依法配合執法機關。

### 5. 數據安全
*   我們使用 **RLS (Row Level Security)** 技術，確保只有您能存取您的資料。
*   所有傳輸均採用 **SSL/TLS 加密**。

### 6. 您的權利
您可以隨時請求：
*   匯出您的數據。
*   <span class="highlight">永久刪除</span> 您的帳號及聲紋模型（此動作無法復原）。
""", unsafe_allow_html=True)

if st.button("← 返回首頁"):
    st.switch_page("app.py")
