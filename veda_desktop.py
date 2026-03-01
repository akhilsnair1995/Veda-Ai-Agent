# veda_desktop.py
import streamlit as st
import os
import time
from pathlib import Path
from datetime import datetime
from PIL import Image
import re

# Veda Core Imports
from brain import VedaBrain
from memory.history import init_database, save_message, get_recent_messages
from memory.semantic import SemanticMemory

# Page Configuration
st.set_page_config(
    page_title="Veda🧠Hub",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INITIALIZATION ---
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    init_database()

if "workspace_path" not in st.session_state:
    st.session_state.workspace_path = str(Path("workspace").resolve())

if "brain" not in st.session_state:
    with st.spinner("Initializing Veda Brain..."):
        st.session_state.brain = VedaBrain(model="qwen2.5:7b")

if "messages" not in st.session_state:
    history = get_recent_messages(limit=20)
    st.session_state.messages = history if history else []

if "artifact" not in st.session_state:
    st.session_state.artifact = {"type": None, "content": None, "title": "Cowork Space"}

# --- SIDEBAR: Universal Browser & Control Panel ---
with st.sidebar:
    st.title("Veda🧠Hub")
    st.caption("INDUSTRIALIZING ENGINEERING DESIGN")
    st.divider()
    
    # 1. Universal Browser
    st.subheader("📂 Universal Browser")
    if os.name == 'nt':
        import ctypes
        drives = []
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if bitmask & 1:
                drives.append(f"{letter}:\\")
            bitmask >>= 1
        selected_drive = st.selectbox("Switch Drive:", drives, index=drives.index(st.session_state.workspace_path[:3]) if st.session_state.workspace_path[:3] in drives else 0)
        if selected_drive != st.session_state.workspace_path[:3] and st.button("Jump to Drive"):
            st.session_state.workspace_path = selected_drive
            st.rerun()

    new_path = st.text_input("Active Path:", st.session_state.workspace_path)
    if new_path != st.session_state.workspace_path and os.path.isdir(new_path):
        st.session_state.workspace_path = str(Path(new_path).resolve())
        st.rerun()

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬆️ Up Level", use_container_width=True):
            p = str(Path(st.session_state.workspace_path).parent)
            if p != st.session_state.workspace_path:
                st.session_state.workspace_path = p
                st.rerun()
    with col2:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.workspace_path = str(Path("workspace").resolve())
            st.rerun()

    try:
        dirs = [d for d in os.listdir(st.session_state.workspace_path) if os.path.isdir(os.path.join(st.session_state.workspace_path, d))]
        for d in sorted(dirs)[:15]:
            if st.button(f"📁 {d}", key=f"nav_{d}", use_container_width=True):
                st.session_state.workspace_path = str(Path(st.session_state.workspace_path) / d)
                st.rerun()
    except:
        st.error("Access Denied")

    st.divider()
    
    # 2. Model Configuration
    st.subheader("Model")
    try:
        models_resp = st.session_state.brain.client.list()
        models = models_resp.get('models', []) if isinstance(models_resp, dict) else models_resp.models
        names = [m.get('name') if isinstance(m, dict) else m.model for m in models]
        new_model = st.selectbox("Active Brain:", names, index=names.index(st.session_state.brain.model) if st.session_state.brain.model in names else 0)
        if new_model != st.session_state.brain.model:
            st.session_state.brain.model = new_model
            st.success(f"Switched to {new_model}")
    except:
        st.caption("Ollama offline.")

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.artifact = {"type": None, "content": None, "title": "Cowork Space"}
        st.rerun()

# --- MAIN LAYOUT: Split Screen Coworking ---
chat_col, cowork_col = st.columns([1, 1])

with chat_col:
    st.subheader("Chat")
    # Container for messages to allow scrolling
    chat_container = st.container(height=600)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat Input at bottom of chat column
    if prompt := st.chat_input("Command Veda..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        
        save_message("user", prompt, st.session_state.session_id)

        with chat_container:
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                with st.status("Veda is thinking...", expanded=False) as status:
                    for chunk in st.session_state.brain.stream_think(prompt):
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
                    
                    if "TOOL:" in full_response:
                        status.update(label="Executing Agentic Tools...", state="running", expanded=True)
                        final_answer = st.session_state.brain._handle_tool_calls(full_response, prompt)
                        full_response = final_answer
                        response_placeholder.markdown(full_response)
                    
                    status.update(label="Done", state="complete", expanded=False)

                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                # Update Artifact if detected
                # 1. Look for Python Code
                code_match = re.search(r'```python\n(.*?)\n```', full_response, re.DOTALL)
                if code_match:
                    st.session_state.artifact = {"type": "code", "content": code_match.group(1), "title": "Generated Script"}
                
                # 2. Look for Images
                img_match = re.search(r'([A-Za-z0-9_/\\]+\.(?:png|jpg))', full_response)
                if img_match:
                    path = img_match.group(1)
                    actual_path = path if os.path.isabs(path) else os.path.join(st.session_state.workspace_path, path)
                    if os.path.exists(actual_path):
                        st.session_state.artifact = {"type": "image", "content": actual_path, "title": f"Visual: {path}"}
                
                st.rerun()

with cowork_col:
    st.subheader(st.session_state.artifact["title"])
    artifact_container = st.container(border=True, height=650)
    with artifact_container:
        if st.session_state.artifact["type"] == "code":
            st.code(st.session_state.artifact["content"], language="python")
        elif st.session_state.artifact["type"] == "image":
            st.image(st.session_state.artifact["content"], use_container_width=True)
        elif st.session_state.artifact["type"] is None:
            st.info("Artifacts, charts, and code will appear here as Veda works.")
            st.write("Current Authorized Workspace:")
            st.code(st.session_state.workspace_path)
            
            # Quick Tool Logic Check
            if st.button("Test: Generate Random Plot"):
                import matplotlib.pyplot as plt
                import numpy as np
                x = np.linspace(0, 10, 100)
                y = np.sin(x)
                plt.plot(x, y)
                plt.title("Workspace Connectivity Test")
                path = os.path.join(st.session_state.workspace_path, "test_plot.png")
                plt.savefig(path)
                plt.close()
                st.session_state.artifact = {"type": "image", "content": path, "title": "Cowork Test Plot"}
                st.rerun()
