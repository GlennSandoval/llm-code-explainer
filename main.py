from src.analyzer import CodeAnalyzer

# Example usage
if __name__ == "__main__":
    # Assuming you have a git repository you want to analyze
    repo_path = "/home/glenn/Data/repos/ai/Prompt-Enhancer"
    analyzer = CodeAnalyzer(repo_path,provider="ollama")
    result = analyzer.analyze()
    for key in result:
        print(key,result[key])