# Veda Agent: Kaggle Hosting Setup Guide (Dual-T4 GPUs)

To run **Qwen 2.5 32B** for Veda Agent, follow these steps to host it on Kaggle.

## 1. Create a Kaggle Notebook
1. Go to [Kaggle](https://www.kaggle.com/).
2. Create a new notebook.
3. In the right-hand menu under **Settings**:
   - **Accelerator**: Select **GPU T4 x2**.
   - **Internet**: Ensure it is **On**.

## 2. Copy & Paste this Script into a Cell
This script installs Ollama, pulls the model, and exposes it via a Cloudflare tunnel.

```python
# 1. Install Ollama, Cloudflared, and zstd
!curl -fsSL https://ollama.com/install.sh | sh
!wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
!dpkg -i cloudflared-linux-amd64.deb
!apt-get update && apt-get install -y zstd

# 2. Start Ollama in the background
import subprocess
import os
import time

# Set environment variable for Ollama to use both T4 GPUs
os.environ["OLLAMA_KEEP_ALIVE"] = "24h"
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"

# Start the Ollama server
ollama_proc = subprocess.Popen(["ollama", "serve"], env=os.environ)

# Wait for server to initialize
time.sleep(10)

# 3. Pull Qwen 2.5 32B
print("--- Pulling Qwen 2.5 32B ---")
!ollama pull qwen2.5:32b

# 4. Create the Cloudflare Tunnel
print("--- Starting Cloudflare Tunnel ---")
print("WAIT FOR THE URL (Ending in .trycloudflare.com)")
!cloudflared tunnel --url http://localhost:11434
```

## 3. Launching the Tunnel
1. Run the cell.
2. After a few minutes, look for a line in the output like:
   `https://[some-random-words].trycloudflare.com/`
3. **COPY THIS URL.**

## 4. Update Veda's Brain
Open `veda_agent/brain.py` and update the `host` in the `AIBrain` class:

```python
class AIBrain:
    def __init__(self, model: str = "qwen2.5:32b"):
        self.model = model
        # REPLACE THIS URL with the one from your Kaggle output
        self.client = ollama.Client(host="https://[YOUR-NEW-URL].trycloudflare.com/")
        # ...
```

## 5. Run Veda locally
Run `./launch.sh` in your local terminal.
