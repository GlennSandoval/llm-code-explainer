"""
Basic usage example for the code-parser library.

This example demonstrates how to use the code-parser to analyze:
1. An entire git repository
2. A single code snippet

Requirements:
- tree_sitter and language-specific tree-sitter packages
- openai, anthropic, llama_cpp, or ollama (depending on the provider you choose)
- dotenv for environment variable management
- A valid .env file with API keys (see config/.env.example)
"""

import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Now we can import from src
from src.analyzer import CodeAnalyzer
from src.tree_sitter_parser import TreeSitterParser
from src.llm_manager import LLMManager, CodeElement

def analyze_repository():
    """Analyze all parseable files in a git repository."""
    # Get the current directory as the repository path
    # In a real scenario, you would specify the path to your git repository
    repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Initialize the analyzer with a repository path and LLM provider
    # Available providers: "openai", "anthropic", "openllama", "ollama"
    analyzer = CodeAnalyzer(repo_path, provider="ollama")
    
    # Analyze all parseable files in the repository
    results = analyzer.analyze()
    
    # Print analysis results
    print("Repository Analysis Results:")
    for file_path, analysis in results.items():
        print(f"\n--- {file_path} ---")
        print(analysis)
    
    # Optionally, write results to a file
    with open("analysis_results.txt", "w") as f:
        for file_path, analysis in results.items():
            f.write(f"\n--- {file_path} ---\n")
            f.write(analysis)
            f.write("\n")
    
    print("\nAnalysis results written to analysis_results.txt")

def analyze_code_snippet():
    """Analyze a single code snippet."""
    # Example code to analyze
    code = """
    def calculate_sum(a: int, b: int) -> int:
        \"\"\"Calculate the sum of two integers.\"\"\"
        return a + b
        
    def calculate_product(a: int, b: int) -> int:
        \"\"\"Calculate the product of two integers.\"\"\"
        return a * b
    """
    
    # Initialize the LLM manager directly
    llm_manager = LLMManager(provider="ollama")
    
    # Parse the code using TreeSitterParser
    parser = TreeSitterParser(code, language="python")
    
    # Get function nodes
    function_nodes = parser.get_nodes_by_type("function_definition")
    
    # Analyze each function
    print("\nCode Snippet Analysis Results:")
    for node in function_nodes:
        # Extract function details
        func_name = parser.get_node_text(node.child_by_field_name("name"))
        func_source = parser.get_node_text(node)
        docstring = parser.get_node_docstring(node) or ""
        params = parser.get_method_parameters(node)
        
        # Create a CodeElement
        func_element = CodeElement(
            name=func_name,
            type="method",
            docstring=docstring,
            source_code=func_source,
            parameters=params
        )
        
        # Get description from LLM
        description = llm_manager.get_code_description(func_element)
        
        # Print results
        print(f"\nFunction: {func_name}")
        print(f"Description: {description}")
        print(f"Parameters: {', '.join(params)}")

def main():
    """
    Main function to demonstrate different analysis methods.
    
    Uncomment the analysis method you want to use:
    - analyze_repository(): Analyzes all parseable files in a git repository
      (requires a valid git repository and may take some time for large repos)
    - analyze_code_snippet(): Analyzes a single code snippet
      (faster and doesn't require a git repository)
    """
    
    # Option 1: Analyze a git repository
    # analyze_repository()
    
    # Option 2: Analyze a code snippet (default)
    analyze_code_snippet()

if __name__ == "__main__":
    main()