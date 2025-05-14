# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Code Parser is a Python application that analyzes source code from git repositories and generates natural language descriptions. It uses Tree-sitter for code parsing and Large Language Models (LLMs) for description generation.

Key features:
- Parse and analyze source code from git repositories
- Support for multiple programming languages via Tree-sitter
- Generate natural language descriptions of code elements
- Flexible LLM provider support (OpenAI, Anthropic, OpenLLaMA, Ollama)

## Development Commands

```bash
# Install dependencies
make install

# Run tests
make test

# Lint code
make lint

# Format code with ruff and black
make format

# Clean temporary files and caches
make clean
```

## Architecture

The codebase is organized around these core components:

### 1. CodeAnalyzer (src/analyzer.py)
Central component that orchestrates:
- Repository traversal
- File content extraction
- Code parsing
- LLM interaction for description generation
- Caching mechanism for performance

### 2. LLM Manager (src/llm_manager.py)
Handles interactions with various LLM providers:
- OpenAI (GPT-4)
- Anthropic (Claude)
- OpenLLama (local)
- Ollama (local API)
- Formats prompts for different code element types

### 3. Tree-sitter Parser (src/tree_sitter_parser.py)
Manages code parsing using the tree-sitter library:
- Creates language-specific parsers
- Extracts code elements (classes, methods, functions)
- Handles syntax tree traversal

### 4. Language Configuration (src/language_config.py)
Manages language support:
- Maps file extensions to Tree-sitter language modules
- Provides utilities for language detection
- Centralizes language support configuration

### 5. Main Entry Point (main.py)
Demonstrates basic usage for analyzing a git repository.

## Supported Languages

The application currently supports:
- Python (.py)
- JavaScript (.js)
- TypeScript (.ts)
- Ruby (.rb)
- Go (.go)
- Java (.java)
- C++ (.cpp)
- C (.c)
- Rust (.rs)
- PHP (.php)

## Environment Configuration

The application uses environment variables for LLM provider configuration. Supported providers:
- OpenAI
- Anthropic
- OpenLLaMA
- Ollama

## Testing Approach

Tests use pytest and are located in the tests/ directory. The test suite covers:
- Repository file discovery
- File content handling
- Code parsing and analysis
- LLM integration
- Error handling