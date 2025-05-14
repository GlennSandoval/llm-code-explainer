"""
Project structure analysis example for the code-parser library.

This example demonstrates how to use the code-parser to:
1. Analyze the structure of a git repository
2. Get a high-level project overview from an LLM
3. Use structure information to enhance code analysis

Requirements:
- tree_sitter and language-specific tree-sitter packages
- openai, anthropic, llama_cpp, or ollama (depending on the provider you choose)
- dotenv for environment variable management
- A valid .env file with API keys (see config/.env.example)
"""

import os
import sys
import json

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Now we can import from src
from src.analyzer import CodeAnalyzer
from src.llm_manager import LLMManager

def analyze_project_structure():
    """Analyze the structure of a git repository."""
    # Get the current directory as the repository path
    # In a real scenario, you would specify the path to your git repository
    repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Initialize the analyzer with a repository path and LLM provider
    analyzer = CodeAnalyzer(repo_path, provider="ollama")
    
    # Analyze project structure
    structure = analyzer.analyze_project_structure()
    
    # Print structure information
    print("Project Structure Analysis:")
    print(json.dumps(structure, indent=2))
    
    # Optionally, write structure to a file
    with open("project_structure.json", "w") as f:
        json.dump(structure, indent=2, fp=f)
    
    print("\nProject structure written to project_structure.json")
    
    return structure, analyzer

def get_project_overview(structure, analyzer):
    """Get a high-level project overview from the LLM."""
    # Set the project structure in the LLM manager
    analyzer.llm_manager.set_project_structure(structure)
    
    # Get project overview
    overview = analyzer.llm_manager.get_project_overview()
    
    # Print overview
    print("\nProject Overview:")
    print(overview)
    
    return overview

def analyze_code_with_context(structure, analyzer):
    """Use project structure to enhance code analysis."""
    # Set the project structure in the LLM manager
    analyzer.llm_manager.set_project_structure(structure)
    
    # Analyze a specific file
    # First, locate the analyzer.py file in the repository
    repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    analyzer_file = os.path.join(repo_path, "src", "analyzer.py")
    
    # Read the file
    with open(analyzer_file, "r") as f:
        content = f.read()
    
    # Create a parser for the file
    from src.tree_sitter_parser import TreeSitterParser
    parser = TreeSitterParser(content, language="python")
    
    # Get the CodeAnalyzer class node
    class_nodes = parser.get_nodes_by_type("class_definition")
    code_analyzer_node = None
    for node in class_nodes:
        name = parser.get_node_text(node.child_by_field_name("name"))
        if name == "CodeAnalyzer":
            code_analyzer_node = node
            break
    
    if code_analyzer_node:
        # Create a CodeElement for the class
        from src.llm_manager import CodeElement
        
        class_name = parser.get_node_text(code_analyzer_node.child_by_field_name("name"))
        class_source = parser.get_node_text(code_analyzer_node)
        docstring = parser.get_node_docstring(code_analyzer_node) or ""
        
        class_element = CodeElement(
            name=class_name,
            type="class",
            docstring=docstring,
            source_code=class_source,
        )
        
        # Get description from LLM with project context
        description = analyzer.llm_manager.get_code_description(class_element)
        
        # Print results
        print("\nCodeAnalyzer Class Description (with project context):")
        print(description)

def main():
    """Main function that demonstrates project structure analysis."""
    # Step 1: Analyze project structure
    structure, analyzer = analyze_project_structure()
    
    # Step 2: Get project overview
    overview = get_project_overview(structure, analyzer)
    
    # Step 3: Analyze code with context
    analyze_code_with_context(structure, analyzer)
    
    # Write results to a file
    with open("project_analysis.txt", "w") as f:
        f.write("# Project Structure Analysis\n\n")
        f.write(overview + "\n\n")
        f.write("## Structure Details\n")
        f.write(json.dumps(structure, indent=2) + "\n")
    
    print("\nComplete analysis written to project_analysis.txt")

if __name__ == "__main__":
    main()