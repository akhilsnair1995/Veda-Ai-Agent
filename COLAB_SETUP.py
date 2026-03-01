# veda_colab_server.py
# FINAL VERSION: Using Pinggy on Port 443 (The most reliable Colab tunnel)

import subprocess
import os
import time

def setup_veda_server():
    print("--- 1. Installing Ollama ---")
    subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True)

    print("\n--- 2. Starting Ollama Service ---")
    os.environ["OLLAMA_HOST"] = "0.0.0.0"
    os.environ["OLLAMA_ORIGINS"] = "*"
    subprocess.Popen(["ollama", "serve"], env=os.environ)
    time.sleep(10)

    print("\n--- 3. Pulling Qwen 2.5 32B ---")
    subprocess.run("ollama pull qwen2.5:32b", shell=True)

    print("\n--- 4. Launching Transparent Tunnel (Pinggy) ---")
    print("COPY THE URL BELOW (Starts with https://...)")
    
    # We use Port 443 because Colab blocks Port 22. 
    # This creates a direct bridge to Ollama's API.
    try:
        subprocess.run("ssh -o StrictHostKeyChecking=no -p 443 -R 80:localhost:11434 a.pinggy.io", shell=True)
    except KeyboardInterrupt:
        print("\nTunnel stopped.")

if __name__ == "__main__":
    setup_veda_server()
