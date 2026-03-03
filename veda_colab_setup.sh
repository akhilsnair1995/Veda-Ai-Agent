#!/bin/bash
# veda_colab_setup.sh
# One-click installer for Veda's Brain on Google Colab

echo "--- 1. Installing zstd and Cloudflared ---"
apt-get update -y && apt-get install zstd -y
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared
chmod +x cloudflared

echo "--- 2. Installing Ollama ---"
curl -fsSL https://ollama.com/install.sh | sh

echo "--- 3. Starting Ollama ---"
OLLAMA_HOST=0.0.0.0 OLLAMA_ORIGINS="*" ollama serve > /dev/null 2>&1 &
sleep 10

echo "--- 4. Pulling Vision Model ---"
ollama pull qwen2.5vl:7b

echo "--- 5. Configuring Veda Brain ---"
cat <<EOF > Modelfile
FROM qwen2.5vl:7b
SYSTEM "You are Veda, an autonomous Universal AI Agent. You run on Google Colab. Use your vision capabilities to analyze any images the user provides."
PARAMETER temperature 0.1
PARAMETER num_ctx 8192
EOF
ollama create veda -f Modelfile

echo "--- 6. Launching Tunnel ---"
./cloudflared tunnel --url http://localhost:11434
