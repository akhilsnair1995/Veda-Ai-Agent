# veda_desktop.py
import streamlit as st
import os
import time
import uuid
import re
import sys
import tkinter as tk
from tkinter import filedialog
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
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        path = filedialog.askdirectory(master=root)
        root.destroy()
        return path
    except:
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
        st.session_state.brain = VedaBrain(model="qwen2.5:7b")

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
    
    # 2. Recent Chats (Sessions)
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
    try:
        models_resp = st.session_state.brain.client.list()
        models = models_resp.get('models', []) if isinstance(models_resp, dict) else models_resp.models
        names = [m.get('name') if isinstance(m, dict) else m.model for m in models]
        
        try:
            current_model_idx = names.index(st.session_state.brain.model)
        except ValueError:
            current_model_idx = 0
            
        new_model = st.selectbox("Active Brain:", names, index=current_model_idx)
        if new_model != st.session_state.brain.model:
            st.session_state.brain.model = new_model
            st.success(f"Switched to {new_model}")
    except:
        st.caption("Ollama offline.")

# --- MAIN CONTENT AREA ---

# A. Setup Screen for New Session
if st.session_state.current_session_id == "NEW" or st.session_state.current_session_id is None:
    st.subheader("Initialize New Workspace Session")
    with st.container(border=True):
        session_title = st.text_input("Project/Session Title:", placeholder="e.g., Hospital HVAC Load Study")
        
        # Native Browser for Path Selection
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

# B. Active Chat Interface
else:
    # Synchronize Brain Workspace
    # We use a marker to find the line and replace it entirely to avoid regex escape issues with Windows paths
    marker = "AUTHORIZED WORKSPACE: Your primary working directory is '"
    lines = st.session_state.brain.system_prompt.split('\n')
    for i, line in enumerate(lines):
        if marker in line:
            lines[i] = f"- AUTHORIZED WORKSPACE: Your primary working directory is '{st.session_state.workspace_path}'. Use this folder for all project files, scripts, and reports."
            break
    st.session_state.brain.system_prompt = '\n'.join(lines)

    # Determine layout: Split screen ONLY if artifact exists
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

        if prompt := st.chat_input("Command Veda..."):
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
            
            save_message("user", prompt, st.session_state.current_session_id)

            with chat_container:
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    with st.status("Veda is operating...", expanded=False) as status:
                        for chunk in st.session_state.brain.stream_think(prompt):
                            full_response += chunk
                            response_placeholder.markdown(full_response + "▌")
                        
                        if "TOOL:" in full_response:
                            status.update(label="Executing Agentic Tools...", state="running", expanded=True)
                            final_answer = st.session_state.brain._handle_tool_calls(full_response, prompt)
                            full_response = final_answer
                            response_placeholder.markdown(full_response)
                        
                        status.update(label="Task Verified", state="complete", expanded=False)

                    # Update Artifacts from response
                    code_match = re.search(r'```python\n(.*?)\n```', full_response, re.DOTALL)
                    if code_match:
                        st.session_state.artifact = {"type": "code", "content": code_match.group(1), "title": "Generated Logic"}
                    
                    img_match = re.search(r'([A-Za-z0-9_/\\]+\.(?:png|jpg))', full_response)
                    if img_match:
                        path = img_match.group(1)
                        actual_path = path if os.path.isabs(path) else os.path.join(st.session_state.workspace_path, path)
                        if os.path.exists(actual_path):
                            st.session_state.artifact = {"type": "image", "content": actual_path, "title": f"Rendered Output: {path}"}
                    
                    st.rerun()

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
