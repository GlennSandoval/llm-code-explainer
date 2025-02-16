import openai
from typing import Dict, List
from dataclasses import dataclass
from dotenv import load_dotenv
import os
from tree_sitter_parser import TreeSitterParser

@dataclass
class CodeElement:
    """Represents a code element with its context."""
    name: str
    type: str  # 'class' or 'method'
    docstring: str
    source_code: str
    parameters: List[str] = None

class CodeAnalyzer:
    """Analyzes Python source code and generates natural language descriptions using LLM."""
    
    def __init__(self, source_code: str, file_path: str = None, openai_api_key: str = None):
        self.language = self._detect_language(file_path) if file_path else 'python'
        self.parser = TreeSitterParser(source_code, language=self.language)
        self.source_code = source_code
        
        # Load API key from .env file if not provided
        load_dotenv()
        openai.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API key must be provided either through .env file or constructor")
    
    def _detect_language(self, file_path: str) -> str:
        """Detects programming language based on file extension."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php'
        }
        ext = os.path.splitext(file_path)[1].lower()
        return extension_map.get(ext, 'python')  # Default to Python if extension not found
    
    def analyze(self) -> str:
        """Analyzes the code and returns a natural language description."""
        description = []
        
        # Get module docstring (first string literal in module)
        module_doc = self.parser.get_module_docstring()
        if module_doc:
            description.append(self._generate_module_description(module_doc))
            
        # Analyze classes
        class_nodes = self.parser.get_nodes_by_type('class_definition')
        for node in class_nodes:
            description.append(self._analyze_class(node))
                
        return "\n".join(description)
    
    def _analyze_class(self, class_node) -> str:
        """Analyzes a class and returns its description."""
        # Extract class name and source code
        class_name = self.parser.get_node_text(class_node.child_by_field_name('name'))
        class_source = self.parser.get_node_text(class_node)
        
        # Get class docstring
        docstring = self.parser.get_node_docstring(class_node)
        
        # Create CodeElement for the class
        class_element = CodeElement(
            name=class_name,
            type='class',
            docstring=docstring or "",
            source_code=class_source
        )
        
        # Get LLM description for the class
        class_desc = [f"\nClass '{class_name}':",
                     self._get_llm_description(class_element)]
        
        # Analyze methods
        methods = []
        method_nodes = self.parser.get_nodes_by_type('function_definition')
        for node in method_nodes:
            methods.append(self._analyze_method(node))
                
        if methods:
            class_desc.append("\nMethods:")
            class_desc.extend(methods)
            
        return "\n".join(class_desc)
    
    def _analyze_method(self, method_node) -> str:
        """Analyzes a method and returns its description."""
        # Extract method name and source code
        method_name = self.parser.get_node_text(method_node.child_by_field_name('name'))
        method_source = self.parser.get_node_text(method_node)
        
        # Get parameters
        params = self.parser.get_method_parameters(method_node)
        
        # Get method docstring
        docstring = self.parser.get_node_docstring(method_node)
        
        # Create CodeElement for the method
        method_element = CodeElement(
            name=method_name,
            type='method',
            docstring=docstring or "",
            source_code=method_source,
            parameters=params
        )
        
        # Get LLM description
        method_desc = [f"\n- {method_name}()",
                      f"  {self._get_llm_description(method_element)}"]
        
        if params:
            method_desc.append(f"  Parameters: {', '.join(params)}")
            
        return "\n".join(method_desc)
    
    def _get_llm_description(self, element: CodeElement) -> str:
        """Generates a semantic description using LLM."""
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
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a code analysis assistant. Provide clear, concise descriptions of Python code."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating description: {str(e)}"
    
    def _generate_module_description(self, module_doc: str) -> str:
        """Generates a module-level description using LLM."""
        prompt = f"""Given this Python module docstring:

{module_doc}

Provide a concise description of what this module does."""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a code analysis assistant. Provide clear, concise descriptions of Python code."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.2
            )
            return f"Module Purpose: {response.choices[0].message.content.strip()}\n"
        except Exception as e:
            return f"Module Purpose: {module_doc}\n"

# Example usage
if __name__ == "__main__":
    sample_code = """
    class Calculator:
        \"\"\"A simple calculator class for basic arithmetic operations.\"\"\"
        
        def add(self, a: float, b: float) -> float:
            \"\"\"Adds two numbers and returns the result.\"\"\"
            return a + b
            
        def subtract(self, a: float, b: float) -> float:
            \"\"\"Subtracts b from a and returns the result.\"\"\"
            return a - b
            
        def multiply(self, a: float, b: float) -> float:
            \"\"\"Multiplies two numbers and returns the result.\"\"\"
            return a * b
    """
    
    # API key will be loaded from .env file
    analyzer = CodeAnalyzer(sample_code, file_path="example.py")
    print(analyzer.analyze())
