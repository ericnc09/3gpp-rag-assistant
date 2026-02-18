"""
LLM integration via Ollama for RAG responses
"""
import json
import logging
import urllib.request
import urllib.error
from typing import List, Dict, Iterator

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"


def _check_ollama() -> bool:
    """Check if Ollama server is reachable"""
    try:
        with urllib.request.urlopen(f"{OLLAMA_BASE_URL}/api/tags", timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


class OllamaLLM:
    """Interact with a local Ollama model"""

    def __init__(self, model: str = "llama3.2"):
        self.model = model
        if not _check_ollama():
            raise RuntimeError(
                "Ollama server not running. Start it with: ollama serve"
            )
        logger.info(f"OllamaLLM ready (model={model})")

    def generate(self, prompt: str, stream: bool = False) -> str:
        """Generate a response (non-streaming)"""
        payload = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode()
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                return data.get("response", "")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama request failed: {e}") from e

    def stream(self, prompt: str) -> Iterator[str]:
        """Stream tokens as they are generated"""
        payload = json.dumps({"model": self.model, "prompt": prompt, "stream": True}).encode()
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                for line in resp:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done"):
                        break
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama stream failed: {e}") from e


RAG_PROMPT_TEMPLATE = """\
You are an expert on 3GPP technical specifications for 5G/LTE networks.
Answer the user's question using ONLY the context provided below.
If the context does not contain enough information, say so clearly.
Always cite the source documents in your answer.

Context:
{context}

Question: {question}

Answer:"""


def build_rag_prompt(question: str, context: str) -> str:
    return RAG_PROMPT_TEMPLATE.format(context=context, question=question)
