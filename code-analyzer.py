from typing import Dict, List
from dataclasses import dataclass
from tree_sitter_parser import TreeSitterParser
from language_config import get_language_from_extension
from llm_manager import LLMManager, CodeElement

class CodeAnalyzer:
    """Analyzes Python source code and generates natural language descriptions using LLM."""
    
    def __init__(self, source_code: str, file_path: str = None, openai_api_key: str = None):
        self.language = get_language_from_extension(file_path)
        self.parser = TreeSitterParser(source_code, language=self.language)
        self.source_code = source_code
        self.llm_manager = LLMManager(provider="openai", api_key=openai_api_key)
    
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
                
        # Analyze top-level functions
        function_nodes = self.parser.get_nodes_by_type('function_definition')
        top_level_functions = [node for node in function_nodes 
                              if node.parent.type == 'module']
        
        if top_level_functions:
            description.append("\nTop-level functions:")
            for node in top_level_functions:
                description.append(self._analyze_method(node))
            
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
        method_nodes = [node for node in class_node.children 
                       if node.type == 'function_definition']
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
        return self.llm_manager.get_code_description(element)
    
    def _generate_module_description(self, module_doc: str) -> str:
        """Generates a module-level description using LLM."""
        return self.llm_manager.get_module_description(module_doc)

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
