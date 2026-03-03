# Veda: Universal Autonomous MEP Engineering Agent

Veda is a high-performance, multimodal AI agent designed to **"Industrialize Engineering Design."** It leverages the **Qwen 2.5-VL** model for advanced vision and reasoning, hosted on **Google Colab GPUs** for rapid inference, while maintaining a local agentic core for secure file system operations and tool execution.

---

## 🧠 Core Philosophy
Veda follows the **"Digital Senior Engineer"** analogy:
1.  **Operations/Email**: Handling communication and task management.
2.  **Engineering Logic (The Brain)**: Deep understanding of engineering codes (IBC, IMC, NFPA, ASHRAE).
3.  **Automated Production (The Hands)**: Generating Revit/CAD logic and technical reports.

---

## 🚀 Key Features

### 1. Multimodal Vision (Qwen 2.5-VL)
Veda "sees" your engineering world. 
- **Drawing Analysis**: Attach screenshots of CAD/Revit layouts for instant logic checks.
- **Math & Graphs**: Solve complex hydraulic or psychrometric problems directly from visual data.
- **Document Intelligence**: Deep analysis of technical PDFs and tables.

### 2. Cloud-GPU Hybrid Architecture
- **Remote Brain**: Connects to Google Colab (T4/L4/A100) via Cloudflare tunnels for 10x faster response times.
- **Local Hands**: Executes Python scripts, manages files, and runs MCP servers on your local machine.

### 3. Agentic Protocol (NO SHORTCUTS)
Veda operates in a continuous loop: **EXPLORE -> PLAN -> ACT -> OBSERVE**.
- **Mandatory Tool Use**: Veda is forbidden from just "talking"—if a file needs to be created or code run, she uses her physical tools.
- **MCP Integration**: Extensible Model Context Protocol (MCP) servers for Filesystem, Web Search, Code Execution, and more.

### 4. Dual Interfaces
- **Veda Terminal**: A high-fidelity ANSI dashboard for rapid, low-latency engineering tasks.
- **Veda Hub (Web UI)**: A professional Streamlit workspace with:
    - Multi-file staging and previews.
    - Side-by-side artifact viewer (Code/Images).
    - Session management and persistence.

---

## 🛠️ Quick Start

### 1. Host the Brain (Google Colab)
Open the `VEDA_COLAB_HOST.py` file, paste it into a Google Colab GPU cell, and run it. Copy the generated `setcolab` command.

### 2. Connect Locally
Run the `setcolab` command in your terminal to link your local Veda to the cloud brain.

### 3. Launch Veda
**Terminal Interface:**
```powershell
.\venv_win\Scripts\python.exe chat.py
```

**Web Interface:**
```powershell
.\venv_win\Scripts\streamlit.exe run veda_desktop.py
```

---

## 📂 Repository Structure
- `brain.py`: The autonomous core and Ollama client logic.
- `chat.py`: Terminal-based interactive agent.
- `veda_desktop.py`: Streamlit-based Web Hub.
- `mcp/`: Model Context Protocol servers and management.
- `knowledge/`: Modelfiles and engineering code data.
- `skills/`: Expert-level Python skills for Veda.

---

## 🛡️ Security & Privacy
Veda is built for privacy. While the LLM inference can be offloaded to your private Colab instance, all project data, codebases, and notes remain **strictly on your local machine**.
