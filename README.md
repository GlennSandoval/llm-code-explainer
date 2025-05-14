# Code Parser

A Python-based tool for analyzing and understanding code structure using tree-sitter and LLM capabilities.

## Features

- Code structure analysis using tree-sitter
- LLM-powered code insights
- Support for multiple programming languages
- Extensible architecture
- Project structure analysis for enhanced context

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

Check out the examples directory for usage examples.

### Code Analysis

```python
from src.analyzer import CodeAnalyzer

# Initialize with repository path
repo_path = "/path/to/your/repo"
analyzer = CodeAnalyzer(repo_path, provider="ollama")

# Analyze code in the repository
results = analyzer.analyze()

# Write results to a file
with open("analysis.txt", "w") as f:
    for file_path, analysis in results.items():
        f.write(f"\n--- {file_path} ---\n")
        f.write(analysis)
```

### Project Structure Analysis

```python
from src.analyzer import CodeAnalyzer

# Initialize with repository path
repo_path = "/path/to/your/repo"
analyzer = CodeAnalyzer(repo_path, provider="ollama")

# Analyze project structure
structure = analyzer.analyze_project_structure()

# Get project overview using LLM
analyzer.llm_manager.set_project_structure(structure)
overview = analyzer.llm_manager.get_project_overview()

print(overview)
```

## Development

- Run tests: `make test`
- Lint code: `make lint`
- Format code: `make format`
- Clean up: `make clean`

## Project Structure

```
code-parser/
├── src/                          # Source code
│   ├── analyzer.py               # Core code analysis functionality
│   ├── tree_sitter_parser.py     # Tree-sitter integration
│   ├── llm_manager.py            # LLM provider integrations
│   └── language_config.py        # Language support configuration
├── tests/                        # Test files
├── config/                       # Configuration files
├── docs/                         # Documentation
├── examples/                     # Usage examples
│   ├── basic_usage.py            # Basic code analysis example
│   └── project_structure_analysis.py # Project structure analysis example
└── main.py                       # Command-line interface
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the [MIT License](LICENSE).
