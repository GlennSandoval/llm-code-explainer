import pytest
from src.analyzer import CodeAnalyzer
from src.llm_manager import LLMManager
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ["OPENAI_API_KEY"] = "sk-proj-1234567890"

@pytest.fixture
def code_analyzer():
    return CodeAnalyzer()

@pytest.fixture
def llm_manager():
    return LLMManager()

@pytest.fixture
def sample_python_code():
    return """
def greet(name: str) -> str:
    return f"Hello, {name}!"
"""

@pytest.fixture
def sample_analysis(code_analyzer, sample_python_code):
    return code_analyzer.analyze(sample_python_code) 