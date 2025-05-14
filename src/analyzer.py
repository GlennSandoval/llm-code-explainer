from typing import Dict, List, Optional, Any, Tuple, Set, Union, Callable, TypeVar, cast
import subprocess
import os
import traceback
import time
import logging
from functools import lru_cache
from collections import defaultdict
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def node_cache_key(node: Any, parser: 'TreeSitterParser') -> str:
    """Generate a unique cache key for a node based on its text and position"""
    return f"{parser.get_node_text(node)}:{node.start_point}:{node.end_point}"
from .tree_sitter_parser import TreeSitterParser
from .language_config import get_language_from_extension
from .llm_manager import LLMManager, CodeElement


class CodeAnalyzer:
    """
    Analyzes source code in a git repository and generates natural language descriptions using LLM.
    
    This class provides functionality to:
    1. Traverse a git repository and identify tracked files
    2. Parse source code using tree-sitter for supported languages
    3. Extract code elements (classes, methods, docstrings)
    4. Generate natural language descriptions using LLM
    
    Dependencies:
    - Requires a valid git repository
    - Uses tree-sitter for code parsing
    - Relies on an LLM provider (default: OpenAI) for generating descriptions
    """

    def __init__(self, repo_path: str, provider: str = "openai") -> None:
        """
        Initialize the CodeAnalyzer with a repository path and LLM provider.
        
        Args:
            repo_path: Path to the git repository to analyze
            provider: LLM provider to use for generating descriptions (default: "openai")
        """
        self.repo_path: str = os.path.abspath(repo_path)  # Convert to absolute path for consistency
        self.llm_manager: LLMManager = LLMManager(provider)  # Initialize LLM interface
        self._parser_cache: Dict[str, TreeSitterParser] = {}  # Cache for TreeSitterParser instances
        self._node_cache: Dict[str, str] = {}   # Cache for analyzed nodes

    def _get_repository_files(self) -> List[str]:
        """
        Gets list of tracked files in the git repository.
        
        Uses git ls-files command to get only tracked files, excluding:
        - Untracked files
        - Files in .gitignore
        - Git metadata
        
        Returns:
            List of absolute paths to tracked files
            
        Raises:
            ValueError: If git repository access fails or if git commands error
        """
        try:
            try:
                # Execute git ls-files in repo directory
                result: subprocess.CompletedProcess[str] = subprocess.run(
                    ["git", "ls-files"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=True,
                )
            except Exception as e:
                raise ValueError(f"Error accessing git repository: {e}")
            # Convert relative paths to absolute paths
            return [
                os.path.join(self.repo_path, file)
                for file in result.stdout.splitlines()
            ]
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Error accessing git repository: {e}")

    def _read_file_content(self, file_path: str) -> str:
        """
        Reads and returns the content of a file with encoding fallback.
        
        First attempts to read with UTF-8 encoding, then falls back to latin-1
        if UTF-8 fails. This handles most text files including those with
        special characters.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            String containing the file contents
            
        Raises:
            ValueError: If file cannot be read with either encoding
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with a different encoding if UTF-8 fails
            with open(file_path, "r", encoding="latin-1") as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Error reading file {file_path}: {e}")

    def analyze(self) -> Dict[str, str]:
        """
        Analyzes all parseable files in the repository and returns their descriptions.
        
        Process:
        1. Gets list of all tracked files in repository
        2. Filters for files with supported language extensions
        3. For each file:
           - Parses the source code
           - Extracts module docstring
           - Identifies and analyzes classes and methods
           - Generates natural language descriptions
        
        Returns:
            Dictionary mapping relative file paths to their analysis descriptions
            
        Note:
            Skips files that:
            - Have unsupported extensions
            - Cannot be parsed
            - Cause errors during analysis
        """
        results: Dict[str, str] = {}

        for file_path in self._get_repository_files():
            # Skip files we can't parse
            try:
                start_time: float = time.time()
                language: Optional[str] = get_language_from_extension(file_path)
                logger.info(f"Language detection time for {file_path}: {time.time() - start_time:.3f}s")
                if not language:
                    continue
            except ValueError:
                continue

            try:
                # Check parser cache first
                cache_key: str = f"{file_path}:{language}"
                if cache_key in self._parser_cache:
                    parser: TreeSitterParser = self._parser_cache[cache_key]
                    logger.info(f"Using cached parser for {file_path}")
                else:
                    # Parse file and extract code elements
                    source_code: str = self._read_file_content(file_path)
                    
                    start_time = time.time()
                    parser = TreeSitterParser(source_code, language=language)
                    self._parser_cache[cache_key] = parser
                    logger.info(f"Parser initialization for {file_path}: {time.time() - start_time:.3f}s")

                description: List[str] = []
                
                start_time = time.time()

                # Get module docstring
                module_doc: Optional[str] = parser.get_module_docstring()
                if module_doc:
                    description.append(self._generate_module_description(module_doc))

                # Analyze classes
                class_nodes: List[Any] = parser.get_nodes_by_type("class_definition")
                for node in class_nodes:
                    description.append(self._analyze_class(node, parser))

                # Analyze top-level functions
                function_nodes: List[Any] = parser.get_nodes_by_type("function_definition")
                top_level_functions: List[Any] = [
                    node for node in function_nodes if node.parent.type == "module"
                ]

                if top_level_functions:
                    description.append("\nTop-level functions:")
                    for node in top_level_functions:
                        description.append(self._analyze_method(node, parser))

                analysis_time: float = time.time() - start_time
                logger.info(f"Node analysis time for {file_path}: {analysis_time:.3f}s")

                # Store results using relative path from repo root
                rel_path: str = os.path.relpath(file_path, self.repo_path)
                results[rel_path] = "\n".join(description)

            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
                traceback.print_exc()
                continue

        return results

    def _analyze_class(self, class_node: Any, parser: TreeSitterParser) -> str:
        """
        Analyzes a class node and generates a comprehensive description.
        
        Process:
        1. Extracts class name and full source code
        2. Gets class docstring if present
        3. Creates a CodeElement for LLM analysis
        4. Recursively analyzes all methods in the class
        
        Args:
            class_node: Tree-sitter node representing the class
            parser: TreeSitterParser instance for the current file
            
        Returns:
            Formatted string containing:
            - Class name and description
            - List of methods with their descriptions
        """
        # Check cache first
        cache_key: str = node_cache_key(class_node, parser)
        if cache_key in self._node_cache:
            logger.info("Using cached class analysis")
            return self._node_cache[cache_key]

        start_time: float = time.time()
        # Extract class name and source code
        class_name: str = parser.get_node_text(class_node.child_by_field_name("name"))
        class_source: str = parser.get_node_text(class_node)

        # Get class docstring
        docstring: Optional[str] = parser.get_node_docstring(class_node)

        # Create CodeElement for the class
        class_element: CodeElement = CodeElement(
            name=class_name,
            type="class",
            docstring=docstring or "",
            source_code=class_source,
        )

        # Get LLM description for the class
        class_desc: List[str] = [
            f"\nClass '{class_name}':",
            self._get_llm_description(class_element),
        ]

        # Analyze methods
        methods: List[str] = []
        method_nodes: List[Any] = [
            node for node in class_node.children if node.type == "function_definition"
        ]
        for node in method_nodes:
            methods.append(self._analyze_method(node, parser))

        if methods:
            class_desc.append("\nMethods:")
            class_desc.extend(methods)

        result: str = "\n".join(class_desc)
        self._node_cache[cache_key] = result
        logger.info(f"Class analysis time: {time.time() - start_time:.3f}s")
        return result

    def _analyze_method(self, method_node: Any, parser: TreeSitterParser) -> str:
        """
        Analyzes a method/function node and generates a detailed description.
        
        Process:
        1. Extracts method name and full source code
        2. Gets parameter list
        3. Gets method docstring if present
        4. Creates a CodeElement for LLM analysis
        
        Args:
            method_node: Tree-sitter node representing the method
            parser: TreeSitterParser instance for the current file
            
        Returns:
            Formatted string containing:
            - Method name and description
            - Parameter list if present
        """
        # Check cache first
        cache_key: str = node_cache_key(method_node, parser)
        if cache_key in self._node_cache:
            logger.info("Using cached method analysis")
            return self._node_cache[cache_key]

        start_time: float = time.time()
        # Extract method name and source code
        method_name: str = parser.get_node_text(method_node.child_by_field_name("name"))
        method_source: str = parser.get_node_text(method_node)

        # Get parameters
        params: List[str] = parser.get_method_parameters(method_node)

        # Get method docstring
        docstring: Optional[str] = parser.get_node_docstring(method_node)

        # Create CodeElement for the method
        method_element: CodeElement = CodeElement(
            name=method_name,
            type="method",
            docstring=docstring or "",
            source_code=method_source,
            parameters=params,
        )

        # Get LLM description
        method_desc: List[str] = [
            f"\n- {method_name}()",
            f"  {self._get_llm_description(method_element)}",
        ]

        if params:
            method_desc.append(f"  Parameters: {', '.join(params)}")

        result: str = "\n".join(method_desc)
        self._node_cache[cache_key] = result
        logger.info(f"Method analysis time: {time.time() - start_time:.3f}s")
        return result

    def _element_cache_key(self, element: CodeElement) -> str:
        """
        Generate a unique cache key for a CodeElement based on its attributes.
        
        Args:
            element: CodeElement to generate a key for
            
        Returns:
            String that can be used as a dictionary key
        """
        # Create a tuple of the element's attributes
        params_str: str = ",".join(element.parameters) if element.parameters else ""
        return f"{element.type}:{element.name}:{hash(element.source_code)}:{hash(element.docstring)}:{hash(params_str)}"
    
    def _get_llm_description(self, element: CodeElement) -> str:
        """
        Generates a semantic description of a code element using LLM.
        
        Delegates to LLMManager to:
        1. Format the code element appropriately for the LLM
        2. Generate a natural language description
        3. Process and return the response
        
        Args:
            element: CodeElement containing the code to analyze
            
        Returns:
            Natural language description of the code element
        """
        # Use our custom cache instead of lru_cache
        cache_key: str = self._element_cache_key(element)
        if cache_key in self._node_cache:
            logger.info(f"Using cached LLM description for {element.type} '{element.name}'")
            return self._node_cache[cache_key]
        
        logger.info(f"Getting LLM description for {element.type} '{element.name}'")
        description: str = self.llm_manager.get_code_description(element)
        
        # Cache the result
        self._node_cache[cache_key] = description
        return description

    def _generate_module_description(self, module_doc: str) -> str:
        """
        Generates a module-level description using LLM.
        
        Takes the module's docstring and uses LLM to generate a more
        comprehensive description of the module's purpose and functionality.
        
        Args:
            module_doc: The module's docstring
            
        Returns:
            Enhanced natural language description of the module
        """
        # Use our custom cache instead of lru_cache
        cache_key: str = f"module:{hash(module_doc)}"
        if cache_key in self._node_cache:
            logger.info("Using cached module description")
            return self._node_cache[cache_key]
        
        logger.info("Getting LLM description for module")
        description: str = self.llm_manager.get_module_description(module_doc)
        
        # Cache the result
        self._node_cache[cache_key] = description
        return description
        
    def analyze_project_structure(self) -> Dict[str, Any]:
        """
        Analyzes the project structure and returns a comprehensive overview.
        
        This method:
        1. Maps file extensions to identify language distribution
        2. Identifies key directories and their purposes
        3. Categorizes files based on their function (source, test, config, docs)
        4. Computes statistics about code organization
        
        Returns:
            Dictionary containing project structure information:
            - language_distribution: Count of files by language
            - directory_structure: Hierarchical directory organization
            - file_categories: Files grouped by function
            - statistics: Overall code metrics
        """
        logger.info("Analyzing project structure")
        start_time: float = time.time()
        
        # Get all files in the repository
        all_files: List[str] = self._get_repository_files()
        
        # Initialize result structure
        result: Dict[str, Any] = {
            "language_distribution": defaultdict(int),
            "directory_structure": defaultdict(list),
            "file_categories": {
                "source": [],
                "test": [],
                "config": [],
                "documentation": [],
                "other": []
            },
            "statistics": {
                "total_files": len(all_files),
                "directories": set()
            }
        }
        
        # Process each file
        for file_path in all_files:
            rel_path: str = os.path.relpath(file_path, self.repo_path)
            
            # Get file extension and language
            _, ext = os.path.splitext(file_path)
            language: Optional[str] = None
            try:
                language = get_language_from_extension(file_path)
            except ValueError:
                pass
            
            # Update language distribution
            if language:
                result["language_distribution"][language] += 1
            else:
                result["language_distribution"][ext or "no_extension"] += 1
            
            # Update directory structure
            directory: str = os.path.dirname(rel_path)
            if directory:
                result["directory_structure"][directory].append(os.path.basename(file_path))
                result["statistics"]["directories"].add(directory)
            else:
                result["directory_structure"]["root"].append(os.path.basename(file_path))
            
            # Categorize files
            if "test" in rel_path.lower() or "tests" in rel_path.lower():
                result["file_categories"]["test"].append(rel_path)
            elif ext in (".md", ".txt", ".rst", ".html", ".pdf"):
                result["file_categories"]["documentation"].append(rel_path)
            elif ext in (".json", ".yml", ".yaml", ".ini", ".toml", ".cfg", ".config"):
                result["file_categories"]["config"].append(rel_path)
            elif language:
                result["file_categories"]["source"].append(rel_path)
            else:
                result["file_categories"]["other"].append(rel_path)
        
        # Convert defaultdicts to regular dicts for better serialization
        result["language_distribution"] = dict(result["language_distribution"])
        result["directory_structure"] = dict(result["directory_structure"])
        
        # Update statistics
        result["statistics"]["directories"] = list(result["statistics"]["directories"])
        result["statistics"]["directory_count"] = len(result["statistics"]["directories"])
        result["statistics"]["source_files"] = len(result["file_categories"]["source"])
        result["statistics"]["test_files"] = len(result["file_categories"]["test"])
        result["statistics"]["config_files"] = len(result["file_categories"]["config"])
        result["statistics"]["documentation_files"] = len(result["file_categories"]["documentation"])
        
        logger.info(f"Project structure analysis completed in {time.time() - start_time:.3f}s")
        return result
