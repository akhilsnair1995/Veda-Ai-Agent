# VEDA COLAB VISION HOST (CLEAN COPY)
# ==============================================================================
# INSTRUCTIONS:
# 1. Open a Google Colab Notebook (https://colab.new).
# 2. Select a GPU Runtime: Runtime -> Change runtime type -> Hardware accelerator (T4, L4, or A100).
# 3. Paste this entire file into a single code cell and run it.
# 4. Copy the "setcolab" command it generates and run it in your local terminal.
# ==============================================================================

import os
import time
import subprocess
import re

def start_veda():
    # 1. Install ZSTD (Required for model compression)
    print("--- [1/6] Installing ZSTD ---")
    os.system("apt-get update -y && apt-get install zstd -y")
    
    # 2. Install Ollama
    print("--- [2/6] Installing Ollama ---")
    os.system("curl -fsSL https://ollama.com/install.sh | sh")
    
    # 3. Start Service
    print("--- [3/6] Starting Ollama Service ---")
    os.environ["OLLAMA_HOST"] = "0.0.0.0"
    os.environ["OLLAMA_ORIGINS"] = "*"
    # Use the absolute path where the installer puts the binary
    ollama_bin = "/usr/local/bin/ollama"
    
    # Start Ollama as a background process
    subprocess.Popen([ollama_bin, "serve"], env=os.environ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(12)
    
    # 4. Pull Vision Model (Qwen 2.5-VL 7B)
    print("--- [4/6] Pulling Qwen 2.5-VL ---")
    os.system(ollama_bin + " pull qwen2.5vl:7b")
    
    # 5. Create Veda Profile
    print("--- [5/6] Creating Veda Alias ---")
    mfile_content = "FROM qwen2.5vl:7b\nPARAMETER num_ctx 8192\nSYSTEM 'You are Veda, an autonomous Universal AI Agent.'"
    with open("Modelfile", "w") as f:
        f.write(mfile_content)
    os.system(ollama_bin + " create veda -f Modelfile")
    
    # 6. Launch Secure Cloudflare Tunnel
    print("--- [6/6] Launching Cloudflare Tunnel ---")
    if not os.path.exists("cf"):
        os.system("wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cf && chmod +x cf")
    
    # Start the tunnel and capture the output to get the URL
    tunnel = subprocess.Popen(["./cf", "tunnel", "--url", "http://localhost:11434"], 
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    print("Waiting for Tunnel URL...")
    url_found = False
    for _ in range(30):
        line = tunnel.stdout.readline()
        match = re.search(r'https://[a-z0-9\-]+\.trycloudflare\.com', line)
        if match:
            url = match.group(0)
            print("\n" + "="*60)
            print("✓ SUCCESS! VEDA BRAIN IS ONLINE.")
            print("RUN THIS COMMAND LOCALLY TO CONNECT:")
            print("setcolab \"" + url + "\"")
            print("="*60 + "\n")
            url_found = True
            break
        time.sleep(1)

    if not url_found:
        print("✗ Error: Could not generate tunnel URL. Check your internet connection.")
        return

    print("Veda is monitoring the connection. Keep this Colab cell running.")
    try:
        while True:
            time.sleep(60)
            print(".", end="", flush=True)
    except KeyboardInterrupt:
        print("\nShutdown requested. Closing Veda.")

if __name__ == "__main__":
    start_veda()
