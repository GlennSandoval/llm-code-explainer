from typing import Dict, Any

# Add module docstring
"""
Configuration module for programming language support and file extension mapping.
Provides utilities for language detection and parsing capability verification.
"""

# Import language modules
from tree_sitter_python import language as python_language
from tree_sitter_javascript import language as javascript_language
from tree_sitter_typescript import language_typescript as typescript_language
from tree_sitter_ruby import language as ruby_language
from tree_sitter_go import language as go_language
from tree_sitter_java import language as java_language
from tree_sitter_cpp import language as cpp_language
from tree_sitter_c import language as c_language
from tree_sitter_rust import language as rust_language
from tree_sitter_php import language_php as php_language

# Mapping of language names to their tree-sitter language modules
LANGUAGE_CONFIGS: Dict[str, Any] = {
    "python": python_language,
    "javascript": javascript_language,
    "typescript": typescript_language,
    "ruby": ruby_language,
    "go": go_language,
    "java": java_language,
    "cpp": cpp_language,
    "c": c_language,
    "rust": rust_language,
    "php": php_language,
}

# Mapping of file extensions to language names
EXTENSION_MAP: Dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".rb": "ruby",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
}


def get_language_from_extension(file_path: str) -> str | None:
    """Detects programming language based on file extension."""
    if not file_path:
        return None

    # Use os.path for more reliable extension extraction
    import os

    ext = os.path.splitext(file_path.lower())[1]
    return EXTENSION_MAP.get(ext)


def is_parseable(file_path: str) -> bool:
    """
    Checks if a file can be parsed based on its extension.

    Args:
        file_path: Path to the source code file

    Returns:
        bool: True if the file's language is supported for parsing, False otherwise
    """
    language = get_language_from_extension(file_path)
    return language in LANGUAGE_CONFIGS
