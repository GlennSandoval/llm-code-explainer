# Project Structure Analysis Feature

This document describes the new project structure analysis feature added to the code-parser.

## Overview

The project structure analysis feature enhances the code-parser by:

1. Providing comprehensive analysis of a repository's structure
2. Using this structure to enrich LLM context for better code descriptions
3. Offering high-level project overviews using LLM

## Implementation Details

### New Methods

In `src/analyzer.py`:
- `analyze_project_structure()`: Analyzes repository structure and returns a comprehensive overview
  - Maps file extensions to identify language distribution
  - Identifies key directories and their purposes
  - Categorizes files based on their function (source, test, config, docs)
  - Computes statistics about code organization

In `src/llm_manager.py`:
- `set_project_structure()`: Sets project structure information for context enrichment
- `get_project_overview()`: Generates a high-level project description from structure data
- `_get_project_context()`: Creates a context block with project info for LLM prompts

### Updated Main Script

The `main.py` file has been updated to:
1. First analyze project structure
2. Set this structure in the LLM manager for context
3. Generate a high-level project overview
4. Format analysis results with structure information

### New Example

A new example `examples/project_structure_analysis.py` demonstrates:
1. Analyzing project structure
2. Getting project overviews from the LLM
3. Using structure context to enhance code analysis

## Benefits

This feature provides several advantages:

1. **Enhanced Context**: LLM now understands the broader project structure when analyzing individual code elements
2. **Better Insights**: Code descriptions have more context about their role in the larger project
3. **Project Overviews**: Quick summaries of a project's purpose and architecture
4. **Improved Organization**: Better categorization of files and directories

## Future Improvements

Potential enhancements:
1. Dependency graph generation
2. Module relationship analysis
3. Visual representation of project structure
4. Interactive exploration of repositories