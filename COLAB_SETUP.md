# Veda Agent: Google Colab Setup (Gradio Method)

The most reliable way to host Ollama on Colab for Veda is using **Gradio**.

## 1. Run this in a Colab Cell
```python
# 1. Install Ollama and Gradio
!curl -fsSL https://ollama.com/install.sh | sh
!pip install gradio ollama

# 2. Start Ollama in the background
import subprocess
import os
import time

os.environ["OLLAMA_HOST"] = "0.0.0.0"
os.environ["OLLAMA_ORIGINS"] = "*"
subprocess.Popen(["ollama", "serve"])

time.sleep(10)
!ollama pull qwen2.5:32b

# 3. Create a Gradio Bridge
import gradio as gr
def proxy(): return "Ollama Active"
demo = gr.Interface(fn=proxy, inputs=None, outputs="text")
demo.launch(share=True)
```

## 2. Update .env
Copy the `xxxx.gradio.live` URL and paste it into your `.env`:
```env
OLLAMA_HOST=https://[YOUR-URL].gradio.live
```
