"""
LLM factory for v5 — local models via Ollama.

Two model roles:
  text_model   — for planning, coding, critic, repair (must support tool calling)
                 Recommended: qwen2.5-coder:7b, llama3.2:3b, mistral-nemo
  vision_model — for image analysis tasks (dimension extractor, reviewer, validator)
                 Recommended: llava:7b, llama3.2-vision:11b, bakllava:7b

Ollama must be running:  ollama serve
Pull models first:       ollama pull qwen2.5-coder:7b
                         ollama pull llava:7b
"""

import requests

from langchain_ollama import ChatOllama


def get_text_llm(ollama_url: str, text_model: str,
                 temperature: float = 0.1) -> ChatOllama:
    """
    LLM for text-only tasks.
    Must support tool calling for ReAct agents (Planner, Coder).
    Supported models: qwen2.5-coder, llama3.2, mistral-nemo, qwen2.5
    """
    return ChatOllama(
        base_url=ollama_url,
        model=text_model,
        temperature=temperature,
    )


def get_vision_llm(ollama_url: str, vision_model: str,
                   temperature: float = 0.0) -> ChatOllama:
    """
    LLM for vision tasks — receives base64 images.
    Tool calling NOT required.
    Supported models: llava:7b, llama3.2-vision:11b, bakllava:7b, moondream
    """
    return ChatOllama(
        base_url=ollama_url,
        model=vision_model,
        temperature=temperature,
    )


def check_ollama(ollama_url: str) -> tuple:
    """
    Ping Ollama server.
    Returns (is_running: bool, models: list[str], error: str)
    """
    try:
        resp = requests.get(f"{ollama_url.rstrip('/')}/api/tags", timeout=3)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            return True, models, ""
        return False, [], f"HTTP {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return False, [], "Ollama not running — start with: ollama serve"
    except Exception as e:
        return False, [], str(e)
