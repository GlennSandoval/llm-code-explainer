import pytest
from unittest.mock import Mock, patch
import os
from src.analyzer import CodeAnalyzer
from src.tree_sitter_parser import TreeSitterParser

@pytest.fixture
def mock_repo():
    """Creates a temporary mock repository structure"""
    with patch('subprocess.run') as mock_run:
        # Mock git ls-files command
        mock_run.return_value.stdout = "test.py\nmodule/other.py"
        mock_run.return_value.returncode = 0
        yield mock_run

@pytest.fixture
def code_analyzer():
    """Creates a CodeAnalyzer instance with a mock repository path"""
    return CodeAnalyzer("/mock/repo/path")

def test_init(code_analyzer):
    """Test CodeAnalyzer initialization"""
    assert code_analyzer.repo_path == os.path.abspath("/mock/repo/path")
    assert code_analyzer.llm_manager is not None

def test_get_repository_files(code_analyzer, mock_repo):
    """Test getting repository files"""
    files = code_analyzer._get_repository_files()
    expected = [
        os.path.join("/mock/repo/path", "test.py"),
        os.path.join("/mock/repo/path", "module/other.py")
    ]
    assert files == expected

def test_get_repository_files_error():
    """Test handling of git command errors"""
    analyzer = CodeAnalyzer("/invalid/path")
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = Exception("Git command failed")
        with pytest.raises(ValueError, match="Error accessing git repository"):
            analyzer._get_repository_files()

@pytest.fixture
def mock_file_content():
    """Mock file content for testing"""
    return '''
class TestClass:
    """Test class docstring"""
    def test_method(self, param1, param2):
        """Test method docstring"""
        pass
'''

def test_read_file_content(code_analyzer):
    """Test reading file content"""
    with patch('builtins.open', mock_open := Mock()) as mock_file:
        mock_file.return_value.__enter__.return_value.read.return_value = "test content"
        content = code_analyzer._read_file_content("test.py")
        assert content == "test content"
        mock_open.assert_called_once_with("test.py", 'r', encoding='utf-8')

def test_read_file_content_fallback_encoding(code_analyzer):
    """Test reading file content with fallback encoding"""
    with patch('builtins.open') as mock_open:
        # First call raises UnicodeDecodeError, second call succeeds
        mock_open.side_effect = [
            UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid'),
            Mock().__enter__.return_value
        ]
        mock_open.return_value.__enter__.return_value.read.return_value = "test content"
        
        content = code_analyzer._read_file_content("test.py")
        assert content == "test content"

@patch('code_analyzer.get_language_from_extension')
@patch('code_analyzer.TreeSitterParser')
def test_analyze(mock_parser_class, mock_get_language, code_analyzer, mock_repo):
    """Test the analyze method"""
    # Setup mocks
    mock_get_language.return_value = "python"
    mock_parser = Mock()
    mock_parser_class.return_value = mock_parser
    
    # Mock parser methods
    mock_parser.get_module_docstring.return_value = "Module docstring"
    mock_parser.get_nodes_by_type.side_effect = [
        [Mock(parent=Mock(type='module'))],  # class nodes
        [Mock(parent=Mock(type='module'))]   # function nodes
    ]
    
    # Mock file reading
    with patch.object(code_analyzer, '_read_file_content') as mock_read:
        mock_read.return_value = "test content"
        
        # Mock analysis methods
        with patch.object(code_analyzer, '_analyze_class') as mock_analyze_class:
            with patch.object(code_analyzer, '_analyze_method') as mock_analyze_method:
                mock_analyze_class.return_value = "Class description"
                mock_analyze_method.return_value = "Method description"
                
                results = code_analyzer.analyze()
                
                assert len(results) > 0
                assert isinstance(results, dict)

def test_analyze_class(code_analyzer):
    """Test class analysis"""
    mock_parser = Mock(spec=TreeSitterParser)
    mock_class_node = Mock()
    
    # Setup mock returns
    mock_parser.get_node_text.side_effect = ["TestClass", "class TestClass:\n    pass"]
    mock_parser.get_node_docstring.return_value = "Test class docstring"
    mock_class_node.children = []
    
    with patch.object(code_analyzer, '_get_llm_description') as mock_llm:
        mock_llm.return_value = "LLM description"
        
        result = code_analyzer._analyze_class(mock_class_node, mock_parser)
        
        assert "TestClass" in result
        assert "LLM description" in result

def test_analyze_method(code_analyzer):
    """Test method analysis"""
    mock_parser = Mock(spec=TreeSitterParser)
    mock_method_node = Mock()
    
    # Setup mock returns
    mock_parser.get_node_text.side_effect = ["test_method", "def test_method():\n    pass"]
    mock_parser.get_node_docstring.return_value = "Test method docstring"
    mock_parser.get_method_parameters.return_value = ["param1", "param2"]
    
    with patch.object(code_analyzer, '_get_llm_description') as mock_llm:
        mock_llm.return_value = "LLM description"
        
        result = code_analyzer._analyze_method(mock_method_node, mock_parser)
        
        assert "test_method()" in result
        assert "LLM description" in result
        assert "Parameters: param1, param2" in result 