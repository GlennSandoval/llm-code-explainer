from src.analyzer import CodeAnalyzer
from src.llm_manager import LLMManager

def main():
    # Initialize the analyzer
    analyzer = CodeAnalyzer()
    llm_manager = LLMManager()

    # Example code to analyze
    code = """
    def calculate_sum(a: int, b: int) -> int:
        return a + b
    """

    # Analyze the code
    analysis = analyzer.analyze(code)
    
    # Get LLM insights
    insights = llm_manager.get_code_insights(analysis)
    
    print("Code Analysis Results:")
    print(insights)

if __name__ == "__main__":
    main() 