import os
from openai import OpenAI
from packages.core.ports.llm import LLMPort

class OpenAILLM(LLMPort):
    def __init__(self, model: str | None = None, system_message: str | None = None, temperature: float = 0.7):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5")
        self.system_message = system_message
        self.temperature = temperature

    def complete(self, prompt: str, system_message: str | None = None, 
                 temperature: float | None = None) -> str:
        system = system_message or self.system_message
        temp = temperature if temperature is not None else self.temperature
        
        # Monta as mensagens
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        r = self.client.chat.completions.create(
            model=self.model, 
            messages=messages, 
            temperature=temp
        )
        return r.choices[0].message.content.strip()

    def complete_with_messages(self, messages: list[dict], temperature: float | None = None) -> str:
        """
        Método para conversas mais complexas com múltiplas mensagens
        messages: [{"role": "system/user/assistant", "content": "..."}]
        """
        temp = temperature if temperature is not None else self.temperature
        
        r = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temp
        )
        return r.choices[0].message.content.strip()

    def set_temperature(self, temperature: float):
        """Altera a temperatura padrão da instância"""
        self.temperature = temperature

    def complete_with_options(self, prompt: str, system_message: str | None = None, **options) -> str:
        """Versão flexível que aceita opções específicas da OpenAI"""
        system = system_message or self.system_message
        
        # Monta as mensagens
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        # Parâmetros padrão
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature
        }
        
        # Sobrescreve com opções fornecidas
        params.update(options)
        
        r = self.client.chat.completions.create(**params)
        return r.choices[0].message.content.strip()