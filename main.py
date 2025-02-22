from src.analyzer import CodeAnalyzer

# Example usage
if __name__ == "__main__":
    # Assuming you have a git repository you want to analyze
    repo_path = "path/to/your/repo"
    analyzer = CodeAnalyzer(repo_path)
    print(analyzer.analyze())