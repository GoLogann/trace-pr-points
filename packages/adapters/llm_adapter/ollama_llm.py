import os, requests
from packages.core.ports.llm import LLMPort

class OllamaLLM(LLMPort):
    def __init__(self, model: str | None = None, host: str = "http://localhost:11434", 
                 system_message: str | None = None, temperature: float = 0.8):
        self.model = model or os.getenv("OLLAMA_MODEL","llama3.1:8b")
        self.host = host
        self.system_message = system_message
        self.temperature = temperature

    def complete(self, prompt: str, system_message: str | None = None, 
                 temperature: float | None = None) -> str:
        system = system_message or self.system_message
        temp = temperature if temperature is not None else self.temperature
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temp
            }
        }
        
        # Adiciona system message se fornecido
        if system:
            payload["system"] = system
            
        r = requests.post(f"{self.host}/api/generate", json=payload, timeout=600)
        r.raise_for_status()
        print(f"LLM response: {r.json()}")
        return r.json().get("response","").strip()

    def complete_with_messages(self, messages: list[dict], temperature: float | None = None) -> str:
        """
        Alternativa usando o endpoint /api/chat para conversas mais complexas
        messages: [{"role": "system/user/assistant", "content": "..."}]
        """
        temp = temperature if temperature is not None else self.temperature
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temp
            }
        }
        
        r = requests.post(f"{self.host}/api/chat", json=payload, timeout=600)
        r.raise_for_status()
        print(f"LLM response: {r.json()}")
        return r.json().get("message", {}).get("content", "").strip()

    def set_temperature(self, temperature: float):
        """Altera a temperatura padrão da instância"""
        self.temperature = temperature

    def complete_with_options(self, prompt: str, system_message: str | None = None, **options) -> str:
        """Versão mais flexível que aceita qualquer opção do Ollama"""
        system = system_message or self.system_message
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": options
        }
        
        # Adiciona system message se fornecido
        if system:
            payload["system"] = system
            
        r = requests.post(f"{self.host}/api/generate", json=payload, timeout=600)
        r.raise_for_status()
        print(f"LLM response: {r.json()}")
        return r.json().get("response","").strip()