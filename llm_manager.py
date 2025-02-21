import openai
from dataclasses import dataclass
from typing import List
import os
from dotenv import load_dotenv

@dataclass
class CodeElement:
    """Represents a code element with its context."""
    name: str
    type: str  # 'class' or 'method'
    docstring: str
    source_code: str
    parameters: List[str] = None

class LLMManager:
    """Manages all interactions with the Language Learning Model (LLM)."""
    
    def __init__(self, openai_api_key: str = None):
        # Load API key from .env file if not provided
        load_dotenv()
        openai.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API key must be provided either through .env file or constructor")

    def get_code_description(self, element: CodeElement) -> str:
        """Generates a semantic description of a code element using LLM."""
        if element.type == 'class':
            prompt = f"""Given this Python class:

{element.source_code}

Provide a concise description of what this class does. Focus on its purpose and main functionality. Docstring: {element.docstring}
"""
        else:  # method
            prompt = f"""Given this Python method:

{element.source_code}

Provide a concise description of what this method does. Include its purpose, parameters, and return value. Docstring: {element.docstring}
"""
        
        return self._get_llm_response(prompt, max_tokens=150)

    def get_module_description(self, module_doc: str) -> str:
        """Generates a module-level description using LLM."""
        prompt = f"""Given this Python module docstring:

{module_doc}

Provide a concise description of what this module does."""
        
        response = self._get_llm_response(prompt, max_tokens=100)
        return f"Module Purpose: {response}\n"

    def _get_llm_response(self, prompt: str, max_tokens: int = 150, temperature: float = 0.2) -> str:
        """Makes the API call to the LLM and returns the response."""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a code analysis assistant. Provide clear, concise descriptions of Python code."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating description: {str(e)}" 