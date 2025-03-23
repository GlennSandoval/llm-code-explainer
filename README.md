# Code Parser

A Python-based tool for analyzing and understanding code structure using tree-sitter and LLM capabilities.

## Features

- Code structure analysis using tree-sitter
- LLM-powered code insights
- Support for multiple programming languages
- Extensible architecture

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/code-parser.git
cd code-parser
```

2. Install dependencies:
```bash
make install
```

## Usage

Check out the examples directory for usage examples. Here's a basic example:

```python
from src.analyzer import CodeAnalyzer
from src.llm_manager import LLMManager

analyzer = CodeAnalyzer()
llm_manager = LLMManager()

# Analyze some code
analysis = analyzer.analyze(your_code)
insights = llm_manager.get_code_insights(analysis)
```

## Development

- Run tests: `make test`
- Lint code: `make lint`
- Format code: `make format`
- Clean up: `make clean`

## Project Structure

```
code-parser/
├── src/              # Source code
├── tests/            # Test files
├── config/           # Configuration files
├── docs/             # Documentation
├── examples/         # Usage examples
└── scripts/          # Development scripts
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the [MIT License](LICENSE).
