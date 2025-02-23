from dataclasses import dataclass
from typing import List
import os

from anthropic import Anthropic
from dotenv import load_dotenv
from llama_cpp import Llama
import openai

@dataclass
class CodeElement:
    """Represents a code element with its context."""
    name: str
    type: str  # 'class' or 'method'
    docstring: str
    source_code: str
    parameters: List[str] = None

class LLMError(Exception):
    """Custom exception for LLM-related errors."""
    pass

class LLMManager:
    """Manages all interactions with the Language Learning Model (LLM)."""
    
    def __init__(self, provider: str = "openai") -> None:
        """Initialize the LLM manager with specified provider."""
        load_dotenv()
        self.provider = provider.lower()
        
        if self.provider == "openai":
            openai.api_key = os.getenv('OPENAI_API_KEY')
            if not openai.api_key:
                raise ValueError("OpenAI API key must be provided in .env file")
        elif self.provider == "anthropic":
            self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            if not self.client.api_key:
                raise ValueError("Anthropic API key must be provided in .env file")
        elif self.provider == "openllama":
            self.model = Llama(
                model_path=os.getenv('OPENLLAMA_MODEL_PATH'),
                n_ctx=2048,
                n_threads=4
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def get_code_description(self, element: CodeElement) -> str:
        """Generates a semantic description of a code element using LLM."""
        if element.type == 'class':
            prompt = f"""Given this class definition:

{element.source_code}

Provide a concise description of what this class does. Focus on its purpose and main functionality. Docstring: {element.docstring}
"""
        else:  # method
            prompt = f"""Given this function/method:

{element.source_code}

Provide a concise description of what this function/method does. Include its purpose, parameters, and return value. Docstring: {element.docstring}
"""
        
        return self._get_llm_response(prompt, max_tokens=150)

    def get_module_description(self, module_doc: str) -> str:
        """Generates a module-level description using LLM."""
        prompt = f"""Given this module/file docstring:

{module_doc}

Provide a concise description of what this module/file does."""
        
        response = self._get_llm_response(prompt, max_tokens=100)
        return f"Module Purpose: {response}\n"

    def _get_llm_response(self, prompt: str, max_tokens: int = 150, temperature: float = 0.2) -> str:
        """Makes the API call to the LLM and returns the response."""
        try:
            if self.provider == "openai":
                response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a code analysis assistant. Provide clear, concise descriptions of source code."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content.strip()
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system="You are a code analysis assistant. Provide clear, concise descriptions of source code.",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
            
            elif self.provider == "openllama":
                system_prompt = "You are a code analysis assistant. Provide clear, concise descriptions of source code."
                full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
                response = self.model(
                    full_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=["User:", "\n\n"]
                )
                return response['choices'][0]['text'].strip()
            
        except Exception as e:
            raise LLMError(f"Failed to generate description: {str(e)}") 