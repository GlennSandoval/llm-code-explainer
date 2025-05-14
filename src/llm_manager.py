from ollama import Client as Ollama 
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import os
import json

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
        self.project_structure: Optional[Dict[str, Any]] = None

        if self.provider == "openai":
            openai.api_key = os.getenv("OPENAI_API_KEY")
            if not openai.api_key:
                raise ValueError("OpenAI API key must be provided in .env file")
        elif self.provider == "anthropic":
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            if not self.client.api_key:
                raise ValueError("Anthropic API key must be provided in .env file")
        elif self.provider == "openllama":
            self.model = Llama(
                model_path=os.getenv("OPENLLAMA_MODEL_PATH"), n_ctx=2048, n_threads=4
            )
        elif self.provider == "ollama":
            host = os.getenv("OLLAMA_URL")
            if not host:
                raise ValueError("Ollama host url must be provided in .env file")
            self.client = Ollama(host)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def set_project_structure(self, structure: Dict[str, Any]) -> None:
        """
        Sets the project structure information for context enrichment.
        
        Args:
            structure: Project structure dictionary from analyze_project_structure
        """
        self.project_structure = structure

    def get_code_description(self, element: CodeElement) -> str:
        """Generates a semantic description of a code element using LLM."""
        context = self._get_project_context() if self.project_structure else ""
        
        if element.type == "class":
            prompt = f"""{context}Given this class definition:

{element.source_code}

Provide a concise description of what this class does. Focus on its purpose and main functionality. Docstring: {element.docstring}
"""
        else:  # method
            prompt = f"""{context}Given this function/method:

{element.source_code}

Provide a concise description of what this function/method does. Include its purpose, parameters, and return value. Docstring: {element.docstring}
"""

        return self._get_llm_response(prompt, max_tokens=150)

    def get_module_description(self, module_doc: str) -> str:
        """Generates a module-level description using LLM."""
        context = self._get_project_context() if self.project_structure else ""
        
        prompt = f"""{context}Given this module/file docstring:

{module_doc}

Provide a concise description of what this module/file does."""

        response = self._get_llm_response(prompt, max_tokens=100)
        return f"Module Purpose: {response}\n"
        
    def get_project_overview(self) -> str:
        """
        Generates a high-level overview of the project based on its structure.
        
        Returns:
            A natural language description of the project's purpose and organization
        """
        if not self.project_structure:
            return "Project structure information not available."
            
        # Create a summary of the project structure for the prompt
        structure_summary = json.dumps(self.project_structure, indent=2)
        
        prompt = f"""Analyze this project structure information and provide a concise overview of the project:

{structure_summary}

Your overview should include:
1. The likely purpose of the project based on its structure
2. Key components and their relationships
3. The project's architecture pattern (if identifiable)
4. Technological stack based on files and directories
"""
        
        return self._get_llm_response(prompt, max_tokens=300)
    
    def _get_project_context(self) -> str:
        """
        Creates a context block with project structure information.
        
        Returns:
            String with formatted project context for LLM prompts
        """
        if not self.project_structure:
            return ""
            
        # Extract key information for context
        languages = self.project_structure.get("language_distribution", {})
        stats = self.project_structure.get("statistics", {})
        top_dirs = list(self.project_structure.get("directory_structure", {}).keys())[:5]
            
        context = f"""Project Context:
- Main languages: {", ".join(list(languages.keys())[:3])}
- Structure: {stats.get("source_files", 0)} source files, {stats.get("test_files", 0)} test files
- Key directories: {", ".join(top_dirs)}

"""
        return context

    def _get_llm_response(
        self, prompt: str, max_tokens: int = 150, temperature: float = 0.2
    ) -> str:
        """Makes the API call to the LLM and returns the response."""
        try:
            if self.provider == "openai":
                response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a code analysis assistant. Provide clear, concise descriptions of source code.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.choices[0].message.content.strip()

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system="You are a code analysis assistant. Provide clear, concise descriptions of source code.",
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text.strip()

            elif self.provider == "openllama":
                system_prompt = "You are a code analysis assistant. Provide clear, concise descriptions of source code."
                full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
                response = self.model(
                    full_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=["User:", "\n\n"],
                )
                return response["choices"][0]["text"].strip()

            elif self.provider == "ollama":
                response = self.client.chat(
                    model="qwen2:7B",
                    messages=[
                        {"role": "user", "content": prompt},
                    ],
                )
                return response.message.content.strip()

        except Exception as e:
            raise LLMError(f"Failed to generate description: {str(e)}")
