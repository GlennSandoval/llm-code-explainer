import tree_sitter
from typing import List, Dict
from .language_config import LANGUAGE_CONFIGS

class TreeSitterParser:
    """Handles parsing code using tree-sitter for multiple languages."""
    
    def __init__(self, source_code: str, language: str = 'python'):
        """
        Initialize parser with source code and language.
        
        Args:
            source_code: The source code to parse
            language: Programming language of the source code (default: 'python')
        """
        # Initialize tree-sitter
        self.parser = tree_sitter.Parser()
        
        # Validate language
        language = language.lower()
        if language not in LANGUAGE_CONFIGS:
            raise ValueError(f"Unsupported language: {language}. Supported languages: {', '.join(LANGUAGE_CONFIGS.keys())}")
            
        # Use the language module directly
        try:
            self.parser.set_language(LANGUAGE_CONFIGS[language])
        except Exception as e:
            raise RuntimeError(f"Failed to load {language} grammar: {str(e)}")
        
        self.source_code = source_code
        self.tree = self.parser.parse(bytes(source_code, "utf8"))
        self.language = language
    
    def get_node_text(self, node) -> str:
        """Gets the source text for a given node."""
        start_byte = node.start_byte
        end_byte = node.end_byte
        return self.source_code[start_byte:end_byte]
    
    def get_nodes_by_type(self, type_name: str):
        """Gets all nodes of a specific type from the syntax tree."""
        nodes = []
        
        def traverse(cursor):
            if cursor.node.type == type_name:
                nodes.append(cursor.node)
            
            if cursor.goto_first_child():
                while True:
                    traverse(cursor)
                    if not cursor.goto_next_sibling():
                        break
                cursor.goto_parent()
            
        cursor = self.tree.walk()
        traverse(cursor)
        return nodes
    
    def get_node_docstring(self, node) -> str | None:
        """Extracts docstring from a node.
        
        Returns:
            str | None: The docstring if found, None otherwise
        """
        # Look for the first string literal in the node's body
        for child in node.children:
            if child.type == 'expression_statement':
                string_node = child.child_by_field_name('expression')
                if string_node and string_node.type == 'string':
                    return self.get_node_text(string_node).strip('\"\'')
        return None
    
    def get_method_parameters(self, method_node) -> List[str]:
        """Extracts parameter names from a method node."""
        params = []
        parameters_node = method_node.child_by_field_name('parameters')
        if parameters_node:
            for child in parameters_node.children:
                if child.type == 'identifier':
                    param_name = self.get_node_text(child)
                    if param_name != 'self':
                        params.append(param_name)
        return params
    
    def get_module_docstring(self) -> str:
        """Gets the module-level docstring."""
        # Look for the first string literal in the module
        for node in self.tree.root_node.children:
            if node.type == 'expression_statement':
                string_node = node.child_by_field_name('expression')
                if string_node and string_node.type == 'string':
                    return self.get_node_text(string_node).strip('\"\'')
        return None 