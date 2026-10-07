# veda_desktop.py
import streamlit as st
import os
import time
import uuid
import re
import sys
try:
    import tkinter as tk
    from tkinter import filedialog
except (ImportError, ModuleNotFoundError):
    tk = None
    filedialog = None

from pathlib import Path
from datetime import datetime
from PIL import Image

# Ensure project root is in path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

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

def select_folder():
    """Trigger a native OS folder selection dialog."""
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
st.set_page_config(
    page_title="Veda Hub",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INITIALIZATION ---
if "init" not in st.session_state:
    init_database()
    st.session_state.init = True

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "workspace_path" not in st.session_state:
    st.session_state.workspace_path = str(Path("workspace").resolve())

if "brain" not in st.session_state:
    with st.spinner("Initializing Veda Brain..."):
        st.session_state.brain = VedaBrain(model="google/gemma-4-12b-qat", workspace=st.session_state.workspace_path)

if "artifact" not in st.session_state:
    st.session_state.artifact = {"type": None, "content": None, "title": "Cowork Space"}

# --- SIDEBAR: Session Management & Hub Controls ---
with st.sidebar:
    st.title("Veda🧠Hub")
    st.caption("INDUSTRIALIZING ENGINEERING DESIGN")
    st.divider()
    
    # 1. New Chat Button
    if st.button("➕ New Chat Session", use_container_width=True, type="primary"):
        st.session_state.current_session_id = "NEW"
        st.session_state.artifact = {"type": None, "content": None, "title": "Cowork Space"}
        st.rerun()

    st.divider()
    
    # 2. Recent Sessions
    st.subheader("💬 Recent Sessions")
    try:
        sessions = get_all_sessions()
        for s in sessions:
            cols = st.columns([0.7, 0.15, 0.15])
            title = s['title'] or f"Chat {s['session_id'][:8]}"
            if s['is_pinned']:
                title = f"📌 {title}"
                
            with cols[0]:
                is_active = s['session_id'] == st.session_state.current_session_id
                if st.button(title, key=f"session_{s['session_id']}", use_container_width=True, 
                             type="primary" if is_active else "secondary"):
                    st.session_state.current_session_id = s['session_id']
                    st.session_state.workspace_path = s['workspace_path']
                    st.session_state.artifact = {"type": None, "content": None, "title": "Cowork Space"}
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
    
    # 3. Model Configuration
    st.subheader("Engine Settings")
    current_model = st.text_input("Active Model:", value=st.session_state.brain.model)
    if current_model != st.session_state.brain.model:
        st.session_state.brain.model = current_model
        st.success(f"Switched to {current_model}")
    
    host_url = st.session_state.brain._get_host()
    st.caption(f"Endpoint: `{host_url}`")

# --- MAIN CONTENT AREA ---

if st.session_state.current_session_id == "NEW" or st.session_state.current_session_id is None:
    st.subheader("Initialize New Workspace Session")
    with st.container(border=True):
        session_title = st.text_input("Project/Session Title:", placeholder="e.g., Hospital HVAC Load Study")
        st.write("#### Select Working Directory")
        if st.button("📁 Browse System Folders...", use_container_width=True):
            native_path = select_folder()
            if native_path:
                st.session_state.workspace_path = str(Path(native_path).resolve())
                st.rerun()
        selected_path = st.text_input("Active Path:", st.session_state.workspace_path)
        if selected_path != st.session_state.workspace_path:
            if os.path.isdir(selected_path):
                st.session_state.workspace_path = str(Path(selected_path).resolve())
                st.rerun()
        if st.button("🚀 Launch Veda Agent", type="primary", use_container_width=True):
            new_id = str(uuid.uuid4())
            create_session(new_id, session_title, st.session_state.workspace_path)
            st.session_state.current_session_id = new_id
            st.rerun()

else:
    # Synchronize Brain Workspace with active session
    st.session_state.brain.set_workspace(st.session_state.workspace_path)

    show_artifact = st.session_state.artifact.get("content") is not None
    if show_artifact:
        chat_col, cowork_col = st.columns([0.6, 0.4])
    else:
        chat_col = st.container()
        cowork_col = None

    with chat_col:
        st.header(f"💬 Session Active")
        st.caption(f"Working Directory: `{st.session_state.workspace_path}`")
        
        chat_container = st.container(height=500)
        messages = get_session_messages(st.session_state.current_session_id)
        
        with chat_container:
            for message in messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # --- MULTIMODAL UPLOADER ---
        uploaded_file = st.file_uploader("Attach Image or PDF", type=["png", "jpg", "jpeg", "webp", "pdf"], label_visibility="collapsed")
        
        if prompt := st.chat_input("Command Veda..."):
            images = None
            if uploaded_file:
                # Save uploaded file to workspace
                file_path = os.path.join(st.session_state.workspace_path, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                if uploaded_file.type.startswith("image/"):
                    images = [file_path]
                    st.info(f"Image attached: {uploaded_file.name}")
                elif uploaded_file.type == "application/pdf":
                    prompt = f"Analyze this PDF: {file_path}. {prompt}"
                    st.info(f"PDF recognized: {uploaded_file.name}")

            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
            
            save_message("user", prompt, st.session_state.current_session_id)
            messages.append({"role": "user", "content": prompt})

            # --- THE RECURSIVE AGENTIC LOOP ---
            MAX_TURNS = 10
            current_turn = 0
            
            while current_turn < MAX_TURNS:
                current_turn += 1
                with chat_container:
                    with st.chat_message("assistant"):
                        response_placeholder = st.empty()
                        full_response = ""
                        
                        # Step 1: Brain Thinking
                        with st.status(f"Veda Turn {current_turn}...", expanded=False) as status:
                            for chunk in st.session_state.brain.stream_think(prompt, history=messages, images=images):
                                full_response += chunk
                                response_placeholder.markdown(full_response + "▌")
                            
                            # Images are only sent on the first turn of the prompt
                            images = None 
                            
                            # Step 2: Tool Check
                            if not full_response:
                                full_response = st.session_state.brain.think(prompt, history=messages)
                                response_placeholder.markdown(full_response)

                            if "TOOL:" in full_response:
                                status.update(label="Executing Tool...", state="running", expanded=True)
                                result = st.session_state.brain.call_tool_sync(full_response)
                                obs_text = result[:4000] if len(str(result)) > 4000 else str(result)
                                observation = f"[Tool Observation (Step {current_turn})]:\n{obs_text}"
                                status.update(label=f"Observation Received", state="complete")
                                
                                # Record turn in history
                                save_message("assistant", full_response, st.session_state.current_session_id)
                                messages.append({"role": "assistant", "content": full_response})
                                
                                save_message("user", observation, st.session_state.current_session_id)
                                messages.append({"role": "user", "content": observation})
                                
                                # Update artifacts
                                code_match = re.search(r'```python\n(.*?)\n```', full_response, re.DOTALL)
                                if code_match: st.session_state.artifact = {"type": "code", "content": code_match.group(1), "title": "Logic"}
                                img_match = re.search(r'([A-Za-z0-9_/\\]+\.(?:png|jpg))', full_response)
                                if img_match:
                                    path = img_match.group(1)
                                    actual_path = path if os.path.isabs(path) else os.path.join(st.session_state.workspace_path, path)
                                    if os.path.exists(actual_path):
                                        st.session_state.artifact = {"type": "image", "content": actual_path, "title": f"Visual: {path}"}
                                
                                # CONTINUE LOOP
                                continue
                            else:
                                # No more tools! Final answer reached.
                                status.update(label="Task Complete", state="complete")
                                save_message("assistant", full_response, st.session_state.current_session_id)
                                st.rerun()
                                break
            
            if current_turn >= MAX_TURNS:
                st.warning("Maximum autonomous turns reached.")

    if cowork_col and show_artifact:
        with cowork_col:
            st.subheader(st.session_state.artifact["title"])
            with st.container(border=True):
                if st.session_state.artifact["type"] == "code":
                    st.code(st.session_state.artifact["content"], language="python")
                elif st.session_state.artifact["type"] == "image":
                    st.image(st.session_state.artifact["content"], use_container_width=True)
                if st.button("Close Cowork Pane", use_container_width=True):
                    st.session_state.artifact = {"type": None, "content": None, "title": "Cowork Space"}
                    st.rerun()
