from typing import Dict, List
import subprocess
import os
import traceback
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

    def __init__(self, repo_path: str, provider: str = "openai"):
        """
        Initialize the CodeAnalyzer with a repository path and LLM provider.
        
        Args:
            repo_path: Path to the git repository to analyze
            provider: LLM provider to use for generating descriptions (default: "openai")
        """
        self.repo_path = os.path.abspath(repo_path)  # Convert to absolute path for consistency
        self.llm_manager = LLMManager(provider)  # Initialize LLM interface

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
                result = subprocess.run(
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
        results = {}

        for file_path in self._get_repository_files():
            # Skip files we can't parse
            try:
                language = get_language_from_extension(file_path)
                if not language:
                    continue
            except ValueError:
                continue

            try:
                # Parse file and extract code elements
                source_code = self._read_file_content(file_path)
                parser = TreeSitterParser(source_code, language=language)

                description = []

                # Get module docstring
                module_doc = parser.get_module_docstring()
                if module_doc:
                    description.append(self._generate_module_description(module_doc))

                # Analyze classes
                class_nodes = parser.get_nodes_by_type("class_definition")
                for node in class_nodes:
                    description.append(self._analyze_class(node, parser))

                # Analyze top-level functions
                function_nodes = parser.get_nodes_by_type("function_definition")
                top_level_functions = [
                    node for node in function_nodes if node.parent.type == "module"
                ]

                if top_level_functions:
                    description.append("\nTop-level functions:")
                    for node in top_level_functions:
                        description.append(self._analyze_method(node, parser))

                # Store results using relative path from repo root
                rel_path = os.path.relpath(file_path, self.repo_path)
                results[rel_path] = "\n".join(description)

            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
                traceback.print_exc()
                continue

        return results

    def _analyze_class(self, class_node, parser: TreeSitterParser) -> str:
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
        # Extract class name and source code
        class_name = parser.get_node_text(class_node.child_by_field_name("name"))
        class_source = parser.get_node_text(class_node)

        # Get class docstring
        docstring = parser.get_node_docstring(class_node)

        # Create CodeElement for the class
        class_element = CodeElement(
            name=class_name,
            type="class",
            docstring=docstring or "",
            source_code=class_source,
        )

        # Get LLM description for the class
        class_desc = [
            f"\nClass '{class_name}':",
            self._get_llm_description(class_element),
        ]

        # Analyze methods
        methods = []
        method_nodes = [
            node for node in class_node.children if node.type == "function_definition"
        ]
        for node in method_nodes:
            methods.append(self._analyze_method(node, parser))

        if methods:
            class_desc.append("\nMethods:")
            class_desc.extend(methods)

        return "\n".join(class_desc)

    def _analyze_method(self, method_node, parser: TreeSitterParser) -> str:
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
        # Extract method name and source code
        method_name = parser.get_node_text(method_node.child_by_field_name("name"))
        method_source = parser.get_node_text(method_node)

        # Get parameters
        params = parser.get_method_parameters(method_node)

        # Get method docstring
        docstring = parser.get_node_docstring(method_node)

        # Create CodeElement for the method
        method_element = CodeElement(
            name=method_name,
            type="method",
            docstring=docstring or "",
            source_code=method_source,
            parameters=params,
        )

        # Get LLM description
        method_desc = [
            f"\n- {method_name}()",
            f"  {self._get_llm_description(method_element)}",
        ]

        if params:
            method_desc.append(f"  Parameters: {', '.join(params)}")

        return "\n".join(method_desc)

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
        return self.llm_manager.get_code_description(element)

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
        return self.llm_manager.get_module_description(module_doc)
