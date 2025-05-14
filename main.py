from src.analyzer import CodeAnalyzer
import json

# Example usage
if __name__ == "__main__":
    # Assuming you have a git repository you want to analyze
    repo_path = "/home/glenn/Data/repos/ai/code-parser/code-parser"
    analyzer = CodeAnalyzer(repo_path, provider="ollama")
    
    # First analyze project structure
    project_structure = analyzer.analyze_project_structure()
    
    # Set the project structure in the LLM manager for context
    analyzer.llm_manager.set_project_structure(project_structure)
    
    # Get a high-level project overview
    project_overview = analyzer.llm_manager.get_project_overview()
    print("Project Overview:")
    print(project_overview)
    print("\n" + "-"*80 + "\n")
    
    # Analyze code
    result = analyzer.analyze()
    
    # Write analysis results to a file
    with open("analysis.txt", "w") as f:
        # Write project structure first
        f.write("# Project Structure Analysis\n\n")
        f.write(project_overview + "\n\n")
        f.write("## Structure Details\n")
        f.write(json.dumps(project_structure, indent=2) + "\n\n")
        
        # Write code analysis
        f.write("# Code Analysis\n\n")
        for key in result:
            f.write(f"## {key}\n")
            f.write(f"{result[key]}\n\n")
    
    print("Analysis results written to analysis.txt")