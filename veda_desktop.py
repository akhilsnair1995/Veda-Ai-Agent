# veda_desktop.py
# Veda — Autonomous Engineering Intelligence Hub
# Redesigned with ChatGPT / OpenAI Codex modern interface aesthetics & Veda Persona Avatar

import streamlit as st
import os
import time
import uuid
import re
import sys
import base64
from pathlib import Path
from datetime import datetime
from PIL import Image

try:
    import tkinter as tk
    from tkinter import filedialog
except (ImportError, ModuleNotFoundError):
    tk = None
    filedialog = None

# Ensure project root is in path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Avatar path
AVATAR_PATH = BASE_DIR / "assets" / "veda_avatar.jpg"
AVATAR_THUMB = BASE_DIR / "assets" / "veda_avatar_thumb.jpg"
ACTIVE_AVATAR = AVATAR_THUMB if AVATAR_THUMB.exists() else (AVATAR_PATH if AVATAR_PATH.exists() else None)

# Veda Core Imports
from brain import VedaBrain
from memory.history import (
    init_database, 
    save_message, 
    get_session_messages, 
    create_session, 
    get_all_sessions, 
    delete_session, 
    toggle_pin_session
)
from memory.semantic import SemanticMemory

def get_base64_image(image_path: Path) -> str:
    """Encode an image file to base64 for inline rendering."""
    if image_path and image_path.exists():
        try:
            return base64.b64encode(image_path.read_bytes()).decode("utf-8")
        except Exception:
            return ""
    return ""

def select_folder():
    """Trigger a native OS folder selection dialog with headless fallback."""
    if not tk or not filedialog:
        return None
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        path = filedialog.askdirectory(master=root)
        root.destroy()
        return path
    except Exception:
        return None

# Page Configuration
page_icon_img = Image.open(ACTIVE_AVATAR) if ACTIVE_AVATAR and ACTIVE_AVATAR.exists() else "🧠"
st.set_page_config(
    page_title="Veda — Engineering Intelligence",
    page_icon=page_icon_img,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN CHATGPT & CODEX CSS THEME ---
avatar_b64 = get_base64_image(ACTIVE_AVATAR)
avatar_src = f"data:image/jpeg;base64,{avatar_b64}" if avatar_b64 else ""

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Base Styles */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

/* Backgrounds */
.stApp {
    background-color: #0d0f12 !important;
    color: #e5e7eb !important;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #0d0f12;
}
::-webkit-scrollbar-thumb {
    background: #232732;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #3b82f6;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #101216 !important;
    border-right: 1px solid #1e222a !important;
}
[data-testid="stSidebarContent"] {
    padding-top: 1.25rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

/* Sidebar Profile Card */
.veda-profile-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 14px;
    background: linear-gradient(135deg, rgba(26, 30, 40, 0.7), rgba(16, 18, 22, 0.9));
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    margin-bottom: 1rem;
    backdrop-filter: blur(10px);
}
.veda-avatar-frame {
    position: relative;
    width: 48px;
    height: 48px;
    flex-shrink: 0;
}
.veda-avatar-img {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid #3b82f6;
    box-shadow: 0 0 14px rgba(59, 130, 246, 0.35);
}
.veda-status-dot {
    position: absolute;
    bottom: 2px;
    right: 2px;
    width: 10px;
    height: 10px;
    background: #10b981;
    border: 2px solid #101216;
    border-radius: 50%;
}
.veda-profile-meta {
    display: flex;
    flex-direction: column;
}
.veda-name {
    font-size: 1.05rem;
    font-weight: 700;
    color: #f9fafb;
    letter-spacing: -0.01em;
}
.veda-tagline {
    font-size: 0.72rem;
    color: #9ca3af;
    font-weight: 500;
}

/* Chat Messages */
[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    padding: 1rem 0.5rem !important;
    max-width: 900px;
    margin: 0 auto;
}

/* User Message bubble - ChatGPT style */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: #191c24 !important;
    border: 1px solid #272c38 !important;
    border-radius: 18px !important;
    padding: 0.9rem 1.25rem !important;
    margin-bottom: 0.75rem !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
}

/* Chat Input Bar */
[data-testid="stChatInput"] {
    border-radius: 26px !important;
    background-color: #14171e !important;
    border: 1px solid #282d3b !important;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.45) !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #3b82f6 !important;
    box-shadow: 0 8px 32px rgba(59, 130, 246, 0.22) !important;
    background-color: #171a23 !important;
}

/* Code & Markdown Pre */
pre, code {
    font-family: 'JetBrains Mono', Consolas, Monaco, monospace !important;
}
pre {
    background-color: #12141a !important;
    border: 1px solid #222632 !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}

/* Modern Pill Buttons */
.stButton > button {
    border-radius: 12px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
    border: 1px solid #262a35 !important;
    background-color: #151820 !important;
    color: #d1d5db !important;
}
.stButton > button:hover {
    border-color: #3b82f6 !important;
    background-color: #1c202b !important;
    color: #ffffff !important;
    transform: translateY(-1px);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    border: 1px solid #3b82f6 !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5) !important;
}

/* Status Widget / Thinking Box */
[data-testid="stStatusWidget"] {
    background-color: #12151c !important;
    border: 1px solid #232733 !important;
    border-radius: 12px !important;
    margin-bottom: 0.75rem !important;
}

/* Hero Welcome Screen */
.veda-hero-container {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem 1rem;
    max-width: 800px;
    margin: 0 auto;
}
.veda-hero-avatar-frame {
    width: 108px;
    height: 108px;
    margin: 0 auto 1.25rem auto;
    border-radius: 50%;
    padding: 3px;
    background: linear-gradient(135deg, #3b82f6, #ec4899, #8b5cf6);
    box-shadow: 0 0 35px rgba(59, 130, 246, 0.35);
}
.veda-hero-avatar-img {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    object-fit: cover;
    display: block;
}
.veda-hero-title {
    font-size: 2rem;
    font-weight: 700;
    color: #f9fafb;
    margin-bottom: 0.35rem;
    letter-spacing: -0.02em;
}
.veda-hero-subtitle {
    font-size: 1rem;
    color: #9ca3af;
    margin-bottom: 2rem;
    font-weight: 400;
}

/* Codex / Canvas Split Pane */
.codex-canvas-card {
    background: #11141a;
    border: 1px solid #232734;
    border-radius: 16px;
    padding: 1.25rem;
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
}
</style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
if "init" not in st.session_state:
    init_database()
    st.session_state.init = True

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "workspace_path" not in st.session_state:
    st.session_state.workspace_path = str(Path("workspace").resolve())

if "brain" not in st.session_state:
    with st.spinner("Connecting Veda Neural Core..."):
        st.session_state.brain = VedaBrain(workspace=st.session_state.workspace_path)

if "artifact" not in st.session_state:
    st.session_state.artifact = {"type": None, "content": None, "title": "Codex Canvas"}

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# --- SIDEBAR: Session Management & Model Settings ---
with st.sidebar:
    # 1. Veda Persona Profile Header
    if avatar_src:
        st.markdown(f"""
        <div class="veda-profile-card">
            <div class="veda-avatar-frame">
                <img src="{avatar_src}" class="veda-avatar-img" alt="Veda Avatar">
                <span class="veda-status-dot"></span>
            </div>
            <div class="veda-profile-meta">
                <span class="veda-name">Veda</span>
                <span class="veda-tagline">Autonomous Engineering AI</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.title("🧠 Veda")
        st.caption("AUTONOMOUS ENGINEERING INTELLIGENCE")

    # 2. New Chat Pill Button (ChatGPT Style)
    if st.button("➕ New Session", use_container_width=True, type="primary"):
        st.session_state.current_session_id = "NEW"
        st.session_state.artifact = {"type": None, "content": None, "title": "Codex Canvas"}
        st.session_state.pending_prompt = None
        st.rerun()

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # 3. Workspace Folder Indicator
    ws_display = Path(st.session_state.workspace_path).name or st.session_state.workspace_path
    with st.expander(f"📁 Workspace: `{ws_display}`", expanded=False):
        st.caption(f"Full Path: `{st.session_state.workspace_path}`")
        if st.button("Browse Folder...", use_container_width=True):
            n_path = select_folder()
            if n_path:
                st.session_state.workspace_path = str(Path(n_path).resolve())
                st.session_state.brain.set_workspace(st.session_state.workspace_path)
                st.rerun()
        manual_path = st.text_input("Change Directory:", value=st.session_state.workspace_path, label_visibility="collapsed")
        if manual_path != st.session_state.workspace_path and os.path.isdir(manual_path):
            st.session_state.workspace_path = str(Path(manual_path).resolve())
            st.session_state.brain.set_workspace(st.session_state.workspace_path)
            st.rerun()

    st.divider()

    # 4. Recent Chats List
    st.markdown("<p style='font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: #6b7280; font-weight: 600; margin-bottom: 8px;'>Conversations</p>", unsafe_allow_html=True)
    try:
        sessions = get_all_sessions()
        if not sessions:
            st.caption("No chat history yet.")
        for s in sessions:
            cols = st.columns([0.72, 0.14, 0.14])
            title = s['title'] or f"Chat {s['session_id'][:8]}"
            if s['is_pinned']:
                title = f"📌 {title}"
                
            with cols[0]:
                is_active = s['session_id'] == st.session_state.current_session_id
                btn_type = "primary" if is_active else "secondary"
                if st.button(title, key=f"session_{s['session_id']}", use_container_width=True, type=btn_type):
                    st.session_state.current_session_id = s['session_id']
                    st.session_state.workspace_path = s['workspace_path']
                    st.session_state.artifact = {"type": None, "content": None, "title": "Codex Canvas"}
                    st.session_state.pending_prompt = None
                    st.rerun()
            
            with cols[1]:
                if st.button("📍", key=f"pin_{s['session_id']}", help="Toggle Pin"):
                    toggle_pin_session(s['session_id'])
                    st.rerun()
            
            with cols[2]:
                if st.button("🗑️", key=f"del_{s['session_id']}", help="Delete Session"):
                    delete_session(s['session_id'])
                    if st.session_state.current_session_id == s['session_id']:
                        st.session_state.current_session_id = None
                    st.rerun()
    except Exception as e:
        st.error(f"Session Error: {e}")

    st.divider()

    # 5. Engine Settings Footer
    with st.expander("⚙️ Engine Settings", expanded=False):
        current_model = st.text_input("Model ID:", value=st.session_state.brain.model)
        if current_model != st.session_state.brain.model:
            st.session_state.brain.model = current_model
            st.success(f"Switched to {current_model}")
        
        host_url = st.session_state.brain._get_host()
        st.caption(f"Endpoint: `{host_url}`")
        if st.button("Test Reconnect", use_container_width=True):
            if st.session_state.brain._health_check():
                st.success("✓ Connection Healthy")
            else:
                st.error("✗ Failed to reach LLM endpoint")

    st.caption("Veda v2.5 • Google Deepmind AGY Edition")


# --- MAIN CHAT & CODEX CANVAS AREA ---

# Check if we should display the Hero Welcome Screen
is_welcome = (st.session_state.current_session_id == "NEW" or st.session_state.current_session_id is None) and (not st.session_state.pending_prompt)

if is_welcome:
    # ── HERO WELCOME SCREEN (ChatGPT / Codex App Style) ──
    st.markdown(f"""
    <div class="veda-hero-container">
        <div class="veda-hero-avatar-frame">
            <img src="{avatar_src}" class="veda-hero-avatar-img" alt="Veda Avatar">
        </div>
        <div class="veda-hero-title">I'm Veda.</div>
        <div class="veda-hero-subtitle">What engineering challenge or code shall we solve today?</div>
    </div>
    """, unsafe_allow_html=True)

    # 4 Quick Action Starter Cards (ChatGPT Style)
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("#### 🏗️ MEP Riser & Duct Sizing")
            st.caption("Calculate airflow CFM, static pressure loss, and duct velocity across multi-story risers.")
            if st.button("Start HVAC Calculation ➜", key="card_mep", use_container_width=True):
                st.session_state.pending_prompt = "Perform a complete MEP design calculation for a multi-story building exhaust riser, including CFM airflow, duct sizing via equal friction method, and static pressure drop analysis."
                new_id = str(uuid.uuid4())
                create_session(new_id, "MEP Exhaust Riser Study", st.session_state.workspace_path)
                st.session_state.current_session_id = new_id
                st.rerun()

        with st.container(border=True):
            st.markdown("#### 📐 ASHRAE / Code Compliance")
            st.caption("Audit outdoor air ventilation requirements and safety standards per ASHRAE 62.1 & IMC.")
            if st.button("Verify Code Compliance ➜", key="card_code", use_container_width=True):
                st.session_state.pending_prompt = "Review ventilation air requirements and compliance guidelines under ASHRAE Standard 62.1 and International Mechanical Code (IMC) for a commercial facility."
                new_id = str(uuid.uuid4())
                create_session(new_id, "ASHRAE 62.1 Ventilation Audit", st.session_state.workspace_path)
                st.session_state.current_session_id = new_id
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown("#### 💻 Code Audit & System Tools")
            st.caption("Inspect python algorithms, run static analysis, and execute automated benchmark tests.")
            if st.button("Audit Code & Tools ➜", key="card_audit", use_container_width=True):
                st.session_state.pending_prompt = "Inspect my current workspace, list all Python files, and perform a comprehensive code review focusing on performance, cleanliness, and security."
                new_id = str(uuid.uuid4())
                create_session(new_id, "Workspace Code Review", st.session_state.workspace_path)
                st.session_state.current_session_id = new_id
                st.rerun()

        with st.container(border=True):
            st.markdown("#### 🌐 Autonomous Research & Synthesis")
            st.caption("Multi-turn autonomous web search, scientific paper synthesis, and technical brief generation.")
            if st.button("Begin Deep Research ➜", key="card_res", use_container_width=True):
                st.session_state.pending_prompt = "Conduct in-depth research on recent innovations in building energy simulation and AI-assisted HVAC automation, summarizing key methodologies and data."
                new_id = str(uuid.uuid4())
                create_session(new_id, "HVAC AI Automation Research", st.session_state.workspace_path)
                st.session_state.current_session_id = new_id
                st.rerun()

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    # Prompt Input on Welcome Screen
    if initial_prompt := st.chat_input("Command Veda or describe your project..."):
        new_id = str(uuid.uuid4())
        session_title = initial_prompt[:35] + "..." if len(initial_prompt) > 35 else initial_prompt
        create_session(new_id, session_title, st.session_state.workspace_path)
        st.session_state.current_session_id = new_id
        st.session_state.pending_prompt = initial_prompt
        st.rerun()

else:
    # ── ACTIVE SESSION SCREEN (ChatGPT / Codex Canvas Split View) ──
    st.session_state.brain.set_workspace(st.session_state.workspace_path)

    show_artifact = st.session_state.artifact.get("content") is not None
    if show_artifact:
        chat_col, canvas_col = st.columns([0.58, 0.42])
    else:
        chat_col = st.container()
        canvas_col = None

    with chat_col:
        # Header Bar
        hdr_c1, hdr_c2 = st.columns([0.75, 0.25])
        with hdr_c1:
            st.markdown(f"### 💬 Session Active")
            st.caption(f"📁 `{st.session_state.workspace_path}` • ⚡ `{st.session_state.brain.model}`")
        with hdr_c2:
            if show_artifact:
                if st.button("✕ Close Canvas", key="close_cvs_top", use_container_width=True):
                    st.session_state.artifact = {"type": None, "content": None, "title": "Codex Canvas"}
                    st.rerun()

        # Chat Message Container
        chat_container = st.container(height=540)
        messages = get_session_messages(st.session_state.current_session_id)
        
        with chat_container:
            for message in messages:
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.markdown(message["content"])
                else:
                    avatar_arg = str(ACTIVE_AVATAR) if ACTIVE_AVATAR and ACTIVE_AVATAR.exists() else "🧠"
                    with st.chat_message("assistant", avatar=avatar_arg):
                        st.markdown(message["content"])

        # Multimodal Attachment Bar (Expandable)
        with st.expander("📎 Attach PDF Drawing / Image Document", expanded=False):
            uploaded_file = st.file_uploader("Upload attachment", type=["png", "jpg", "jpeg", "webp", "pdf"], label_visibility="collapsed")
            if uploaded_file:
                st.caption(f"✓ Ready: `{uploaded_file.name}` ({uploaded_file.size // 1024} KB)")

        # Handle pending prompt from welcome cards or input bar
        prompt = None
        if st.session_state.pending_prompt:
            prompt = st.session_state.pending_prompt
            st.session_state.pending_prompt = None
        else:
            prompt = st.chat_input("Message Veda...")

        if prompt:
            images = None
            if 'uploaded_file' in locals() and uploaded_file:
                file_path = os.path.join(st.session_state.workspace_path, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                if uploaded_file.type.startswith("image/"):
                    images = [file_path]
                    st.toast(f"📷 Attached Image: {uploaded_file.name}")
                elif uploaded_file.type == "application/pdf":
                    prompt = f"Analyze this PDF document: {file_path}. {prompt}"
                    st.toast(f"📄 Attached PDF: {uploaded_file.name}")

            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
            
            save_message("user", prompt, st.session_state.current_session_id)
            messages.append({"role": "user", "content": prompt})

            # --- THE RECURSIVE AGENTIC LOOP ---
            MAX_TURNS = 10
            current_turn = 0
            avatar_arg = str(ACTIVE_AVATAR) if ACTIVE_AVATAR and ACTIVE_AVATAR.exists() else "🧠"

            while current_turn < MAX_TURNS:
                current_turn += 1
                with chat_container:
                    with st.chat_message("assistant", avatar=avatar_arg):
                        response_placeholder = st.empty()
                        full_response = ""
                        
                        # Step 1: Brain Reasoning & Streaming
                        with st.status(f"⚡ Veda Reasoning (Turn {current_turn})...", expanded=False) as status:
                            for chunk in st.session_state.brain.stream_think(prompt, history=messages, images=images):
                                full_response += chunk
                                response_placeholder.markdown(full_response + "▌")
                            
                            images = None 
                            
                            if not full_response:
                                full_response = st.session_state.brain.think(prompt, history=messages)
                            
                            response_placeholder.markdown(full_response)

                            # Step 2: Tool Execution Check
                            if "TOOL:" in full_response:
                                status.update(label="⚙️ Executing Engineering Tool...", state="running", expanded=True)
                                result = st.session_state.brain.call_tool_sync(full_response)
                                obs_text = result[:4000] if len(str(result)) > 4000 else str(result)
                                observation = f"[Tool Observation (Step {current_turn})]:\n{obs_text}"
                                status.update(label="✓ Tool Execution Complete", state="complete")
                                
                                # Record turn in history
                                save_message("assistant", full_response, st.session_state.current_session_id)
                                messages.append({"role": "assistant", "content": full_response})
                                
                                save_message("user", observation, st.session_state.current_session_id)
                                messages.append({"role": "user", "content": observation})
                                
                                # Codex Canvas Artifact Detection
                                code_match = re.search(r'```python\n(.*?)\n```', full_response, re.DOTALL)
                                if code_match:
                                    st.session_state.artifact = {
                                        "type": "code", 
                                        "content": code_match.group(1), 
                                        "title": "Python Implementation"
                                    }
                                
                                img_match = re.search(r'([A-Za-z0-9_/\\]+\.(?:png|jpg))', full_response)
                                if img_match:
                                    img_p = img_match.group(1)
                                    actual_p = img_p if os.path.isabs(img_p) else os.path.join(st.session_state.workspace_path, img_p)
                                    if os.path.exists(actual_p):
                                        st.session_state.artifact = {
                                            "type": "image", 
                                            "content": actual_p, 
                                            "title": f"Rendered Visual: {img_p}"
                                        }
                                
                                continue
                            else:
                                # Final Answer reached
                                status.update(label="✓ Completed", state="complete")
                                save_message("assistant", full_response, st.session_state.current_session_id)
                                st.rerun()
                                break
            
            if current_turn >= MAX_TURNS:
                st.warning("Maximum autonomous turns reached.")

    # ── CODEX CANVAS / ARTIFACTS PANEL ──
    if canvas_col and show_artifact:
        with canvas_col:
            st.markdown(f"#### 📐 {st.session_state.artifact['title']}")
            with st.container(border=True):
                art_type = st.session_state.artifact.get("type")
                art_content = st.session_state.artifact.get("content")

                if art_type == "code":
                    st.code(art_content, language="python", line_numbers=True)
                    st.download_button(
                        label="💾 Download Script (.py)",
                        data=art_content,
                        file_name="veda_generated_script.py",
                        mime="text/x-python",
                        use_container_width=True
                    )
                elif art_type == "image":
                    st.image(art_content, use_container_width=True)

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                if st.button("✕ Close Canvas", key="close_cvs_btn", use_container_width=True):
                    st.session_state.artifact = {"type": None, "content": None, "title": "Codex Canvas"}
                    st.rerun()
