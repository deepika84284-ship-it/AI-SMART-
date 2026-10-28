import os
import time
import uuid
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

# 1. Load environment variables
load_dotenv()

# 2. Page Configuration
st.set_page_config(
    page_title="AI Smart Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 3. High-End Modern UI/UX CSS (Luxury Dark Glassmorphism)
st.markdown("""
<style>
    /* Google Fonts import */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Overall Dark Luxury Palette */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #151b28 0%, #090d14 100%);
        color: #f1f5f9;
    }

    /* Clean Sleek Header */
    .hero-container {
        text-align: center;
        padding: 1.2rem 1rem 0.8rem 1rem;
        margin-bottom: 1rem;
    }
    .hero-title {
        font-size: 2.3rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #818cf8 0%, #38bdf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        color: #94a3b8;
        font-weight: 400;
    }
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(99, 102, 241, 0.12);
        color: #a5b4fc;
        border: 1px solid rgba(99, 102, 241, 0.28);
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0b0f17 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    /* New Chat Button */
    div[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.55rem 1rem !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45) !important;
    }

    /* Chat History Items */
    div[data-testid="stSidebar"] .stButton > button:not([kind="primary"]) {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.07) !important;
        color: #cbd5e1 !important;
        border-radius: 8px !important;
        text-align: left !important;
        font-size: 0.84rem !important;
        padding: 0.45rem 0.75rem !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stSidebar"] .stButton > button:not([kind="primary"]):hover {
        background: rgba(255, 255, 255, 0.08) !important;
        border-color: rgba(99, 102, 241, 0.4) !important;
        color: #ffffff !important;
    }

    /* Media Tray Glass Box */
    .media-tray {
        background: rgba(17, 24, 39, 0.65);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 1rem;
    }

    /* Starter Prompt Cards */
    .starter-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 14px;
        transition: all 0.2s ease;
    }

    /* Hide Streamlit Footer & Header space */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def clean_api_key(raw_key: str) -> str:
    if not raw_key:
        return ""
    k = str(raw_key).strip()
    if "=" in k:
        k = k.split("=", 1)[1].strip()
    return k.strip("\"'` \t\r\n")

# 4. Cache Gemini Client
@st.cache_resource
def get_client(api_key: str):
    cleaned = clean_api_key(api_key)
    return genai.Client(api_key=cleaned)

# Fetch API Key from Environment or Streamlit Secrets (for Streamlit Cloud)
raw_key = os.getenv("GEMINI_API_KEY", "")
if not raw_key:
    try:
        raw_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        raw_key = ""
api_key = clean_api_key(raw_key)

# 5. Session State for Multi-Conversation Management
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "active_chat_id" not in st.session_state or not st.session_state.chats:
    first_id = str(uuid.uuid4())[:8]
    st.session_state.chats[first_id] = {
        "title": "New Chat",
        "messages": []
    }
    st.session_state.active_chat_id = first_id

if st.session_state.active_chat_id not in st.session_state.chats:
    st.session_state.active_chat_id = list(st.session_state.chats.keys())[0]

current_chat = st.session_state.chats[st.session_state.active_chat_id]

# 6. Sidebar (Neat, Modern & Organized)
with st.sidebar:
    st.markdown("### 🤖 **AI Smart Assistant**")
    
    # New Chat Action
    if st.button("➕  New Chat", use_container_width=True, type="primary"):
        new_id = str(uuid.uuid4())[:8]
        st.session_state.chats[new_id] = {
            "title": "New Chat",
            "messages": []
        }
        st.session_state.active_chat_id = new_id
        st.rerun()

    st.markdown("---")
    st.markdown("<p style='font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; font-weight: 700;'>Conversations</p>", unsafe_allow_html=True)

    # Chat History List
    chat_keys = list(st.session_state.chats.keys())
    for cid in reversed(chat_keys):
        item = st.session_state.chats[cid]
        is_selected = (cid == st.session_state.active_chat_id)
        icon = "✦ " if is_selected else "💬 "
        
        c_btn, c_del = st.columns([5, 1])
        with c_btn:
            if st.button(f"{icon}{item['title']}", key=f"c_{cid}", use_container_width=True):
                st.session_state.active_chat_id = cid
                st.rerun()
        with c_del:
            if st.button("✕", key=f"d_{cid}", help="Delete chat"):
                del st.session_state.chats[cid]
                if not st.session_state.chats:
                    fresh_id = str(uuid.uuid4())[:8]
                    st.session_state.chats[fresh_id] = {"title": "New Chat", "messages": []}
                    st.session_state.active_chat_id = fresh_id
                else:
                    st.session_state.active_chat_id = list(st.session_state.chats.keys())[0]
                st.rerun()

    # API Key Settings & Status
    st.markdown("---")
    with st.expander("🔑 **API Key Settings**", expanded=not bool(api_key)):
        input_key = st.text_input(
            "Gemini API Key",
            value=api_key if api_key else "",
            type="password",
            placeholder="Paste API key here...",
            help="Enter your key without quotes. Get one at https://aistudio.google.com/app/apikey"
        )
        if input_key:
            api_key = clean_api_key(input_key)

    # Status Footnote
    if api_key:
        st.markdown("<div style='font-size:0.75rem; color:#10b981;'>● Gemini Connected</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-size:0.75rem; color:#ef4444;'>● API Key Missing in Secrets/.env</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.75rem; color:#64748b;'>Modes: Text • Vision • Voice</div>", unsafe_allow_html=True)

# 7. Main Hero Header
st.markdown("""
<div class="hero-container">
    <div class="hero-title">AI Smart Assistant</div>
    <div class="hero-subtitle">Next-Generation AI Companion • Text, Vision & Voice Enabled</div>
    <div class="status-badge">⚡ Powered by Google Gemini 3.1 Flash</div>
</div>
""", unsafe_allow_html=True)

# 8. Starter Prompts for Empty Chat
if not current_chat["messages"]:
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💡 Explain Artificial Intelligence in simple terms", use_container_width=True):
            st.session_state.quick_query = "Explain Artificial Intelligence and Machine Learning in simple, intuitive terms."
    with col2:
        if st.button("🐍 Generate Python code for a Web Scraper", use_container_width=True):
            st.session_state.quick_query = "Write clean, commented Python code for a simple web scraper using BeautifulSoup."

# 9. Render Chat Messages
for msg in current_chat["messages"]:
    avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        if "image" in msg and msg["image"]:
            st.image(msg["image"], width=320, caption="Uploaded Image")
        if "audio" in msg and msg["audio"]:
            st.audio(msg["audio"], format="audio/wav")
        if "content" in msg and msg["content"]:
            st.markdown(msg["content"])

# 10. Neat Multimodal Input Bar (Photo & Voice)
with st.expander("📎  Attach Media (📷 Photo Upload / 🎙️ Voice Input)", expanded=False):
    tab_img, tab_mic = st.tabs(["📷 Photo / Image", "🎙️ Voice Audio"])
    with tab_img:
        uploaded_image = st.file_uploader(
            "Upload Image (Diagram, Code screenshot, Handwritten notes, Object...)",
            type=["png", "jpg", "jpeg", "webp"],
            key="img_up"
        )
        if uploaded_image:
            st.image(uploaded_image, width=220, caption="Selected Image")
    with tab_mic:
        recorded_audio = st.audio_input("Record voice question directly from microphone", key="mic_rec")
        if recorded_audio:
            st.audio(recorded_audio)

# 11. Handle Input (Text, Quick Prompt, Photo, or Voice)
user_prompt = st.chat_input("Message AI Smart Assistant... (or attach photo/voice above)")

if "quick_query" in st.session_state and st.session_state.quick_query:
    user_prompt = st.session_state.quick_query
    st.session_state.quick_query = None

trigger_action = False
input_mode = "text"

if user_prompt:
    trigger_action = True
    input_mode = "text"
elif recorded_audio and ("processed_audio" not in st.session_state or st.session_state.processed_audio != recorded_audio):
    trigger_action = True
    input_mode = "voice"
    st.session_state.processed_audio = recorded_audio
    user_prompt = "Listen to my voice audio and answer clearly in detail."

if trigger_action:
    if not api_key or "your_" in api_key.lower() or "gemini_api_key_here" in api_key.lower():
        st.error(
            "⚠️ **Real Gemini API Key is required!**\n\n"
            "You might have pasted the example placeholder `your_gemini_api_key_here` instead of your real key.\n\n"
            "- Please enter your actual key in the left **Sidebar ➔ API Key Settings** box.\n"
            "- Or update **Streamlit Cloud Dashboard ➔ Settings ➔ Secrets** with your real key."
        )
        st.stop()

    # Dynamic Title Generation for First Message
    if not current_chat["messages"]:
        if uploaded_image:
            current_chat["title"] = "📷 " + (user_prompt[:18] if user_prompt else "Photo Analysis")
        elif input_mode == "voice":
            current_chat["title"] = "🎙️ Voice Note"
        else:
            clean_txt = user_prompt.strip().replace("\n", " ")
            current_chat["title"] = clean_txt[:22] + "..." if len(clean_txt) > 22 else clean_txt

    # Save User Record
    user_entry = {
        "role": "user",
        "content": user_prompt if input_mode != "voice" else "🎙️ *Voice Note Sent*",
        "image": uploaded_image.getvalue() if uploaded_image else None,
        "audio": recorded_audio.getvalue() if input_mode == "voice" else None
    }
    current_chat["messages"].append(user_entry)

    with st.chat_message("user", avatar="🧑‍💻"):
        if user_entry["image"]:
            st.image(user_entry["image"], width=320)
        if user_entry["audio"]:
            st.audio(user_entry["audio"], format="audio/wav")
        st.markdown(user_entry["content"])

    # Prepare Multimodal Payload
    parts_list = []
    if uploaded_image:
        parts_list.append(types.Part.from_bytes(
            data=uploaded_image.getvalue(),
            mime_type=uploaded_image.type
        ))
    if input_mode == "voice" and recorded_audio:
        parts_list.append(types.Part.from_bytes(
            data=recorded_audio.getvalue(),
            mime_type="audio/wav"
        ))
    
    text_instruction = user_prompt if user_prompt else "Please analyze this image in detail."
    parts_list.append(types.Part.from_text(text=text_instruction))

    # Build Context History Payload
    history_payload = []
    for m in current_chat["messages"][:-1]:
        role = "user" if m["role"] == "user" else "model"
        history_payload.append(types.Content(
            role=role,
            parts=[types.Part.from_text(text=m["content"])]
        ))

    # Add current multimodal turn
    history_payload.append(types.Content(
        role="user",
        parts=parts_list
    ))

    # Stream Response
    with st.chat_message("assistant", avatar="🤖"):
        try:
            client = get_client(api_key)
            config = types.GenerateContentConfig(
                system_instruction=(
                    "You are AI Smart Assistant, an advanced, highly capable, polite, and intelligent AI companion. "
                    "Provide well-structured answers using clean markdown, bullet points, and code formatting."
                )
            )

            def stream_chunks():
                stream = client.models.generate_content_stream(
                    model="gemini-3.1-flash-lite",
                    contents=history_payload,
                    config=config
                )
                for chunk in stream:
                    if chunk.text:
                        yield chunk.text

            reply_text = st.write_stream(stream_chunks())

            current_chat["messages"].append({
                "role": "assistant",
                "content": reply_text
            })

        except APIError as e:
            err_msg = str(e.message) if hasattr(e, "message") else str(e)
            if "API key not valid" in err_msg:
                st.error("⚠️ **API key not valid!** Please check your Gemini API key in the sidebar or Streamlit Secrets. Ensure there are no quotes (`\"`), extra spaces, or `GEMINI_API_KEY = `.")
            else:
                st.error(f"⚠️ Gemini API Error: {err_msg}")
        except Exception as e:
            st.error(f"⚠️ Error: {str(e)}")
