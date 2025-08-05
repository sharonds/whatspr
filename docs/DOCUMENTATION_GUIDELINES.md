# Documentation Guidelines

This document outlines the documentation standards for the WhatsPR project to ensure consistent, high-quality code documentation.

## Overview

All functions, classes, and modules in this codebase must include Google-style docstrings. This is enforced automatically through our CI/CD pipeline using `pydocstyle`.

## Google Docstring Style

We use the **Google docstring convention** for all Python code. This provides clear, readable documentation that integrates well with documentation generators and IDEs.

### Function Docstring Template

```python
def example_function(param1: str, param2: int = 0) -> bool:
    """Brief description of what the function does.
    
    More detailed description if needed. This can span multiple lines
    and provide additional context about the function's behavior.
    
    Args:
        param1: Description of the first parameter.
        param2: Description of the second parameter with default value.
        
    Returns:
        bool: Description of what the function returns.
        
    Raises:
        ValueError: When param1 is empty.
        RuntimeError: When operation fails.
        
    Example:
        Basic usage example:
        
        >>> result = example_function("hello", 42)
        >>> print(result)
        True
    """
    # Implementation here
    pass
```

### Class Docstring Template

```python
class ExampleClass:
    """Brief description of the class purpose.
    
    Detailed description of the class functionality, its role in the system,
    and any important usage patterns or constraints.
    
    Attributes:
        attribute1: Description of public attribute.
        attribute2: Description of another attribute.
        
    Example:
        Basic usage example:
        
        >>> obj = ExampleClass()
        >>> obj.method()
    """
    
    def __init__(self, param: str):
        """Initialize the class with required parameters.
        
        Args:
            param: Description of the initialization parameter.
        """
        self.attribute1 = param
```

### Module Docstring Template

```python
"""Brief description of the module's purpose.

This module provides functionality for [specific purpose]. It includes
classes and functions for [main capabilities].

Typical usage example:
    
    from module import main_function
    result = main_function()
"""
```

## Documentation Requirements

### Required Sections

1. **Brief Description**: One-line summary of the function/class purpose
2. **Args**: Document all parameters with type information when not obvious
3. **Returns**: Describe return value and type
4. **Raises**: Document exceptions that might be raised

### Optional Sections

1. **Example**: Provide usage examples for complex functions
2. **Note**: Additional important information
3. **Warning**: Critical warnings about usage

### Exceptions

The following items are **excluded** from docstring requirements:

- Test functions (files starting with `test_`)
- Private functions (starting with `_`) - optional but recommended
- Simple property getters/setters
- `__init__.py` files (module docstring optional)

## Style Guidelines

### Do's

✅ **Be concise but descriptive**
```python
def validate_phone(number: str) -> bool:
    """Validate phone number format for international standard."""
```

✅ **Use active voice**
```python
def save_data(data: dict) -> None:
    """Save data to the database."""
```

✅ **Include type information in complex cases**
```python
def process_results(data: List[Dict[str, Any]]) -> Optional[str]:
    """Process API results and return formatted summary.
    
    Args:
        data: List of dictionaries containing API response data.
        
    Returns:
        Optional[str]: Formatted summary string or None if no data.
    """
```

### Don'ts

❌ **Don't repeat obvious information**
```python
# Bad
def get_name(self) -> str:
    """Get the name and return the name."""
    
# Good  
def get_name(self) -> str:
    """Return the user's full name."""
```

❌ **Don't use unclear pronouns**
```python
# Bad
def process_data(items: list) -> list:
    """Process them and return it."""
    
# Good
def process_data(items: list) -> list:
    """Process input items and return filtered results."""
```

## Automated Enforcement

### Pre-commit Hooks

The project uses pre-commit hooks to automatically validate docstrings:

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### CI/CD Pipeline

Our GitHub Actions workflow automatically:

1. Checks docstring compliance with `pydocstyle`
2. Validates code formatting with `black`
3. Runs linting with `ruff`
4. Executes the test suite

### Local Development

Run the complete quality check locally:

```bash
# Run all checks
./scripts/lint.sh

# Run only docstring checks
pydocstyle app/ --convention=google
```

## Configuration

### pydocstyle Configuration

Located in `pyproject.toml`:

```toml
[tool.pydocstyle]
convention = "google"
add-ignore = ["D100", "D104", "D105", "D107"]
match-dir = "(?!tests|migrations|scripts)"
match = "(?!test_|conftest).*\\.py"
```

### Ignored Rules

- `D100`: Missing docstring in public module
- `D104`: Missing docstring in public package  
- `D105`: Missing docstring in magic method
- `D107`: Missing docstring in __init__

## Examples from Codebase

### Security Function Example

```python
def validate_request_rate(phone: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
    """Validate request rate limits for phone numbers.
    
    Implements sliding window rate limiting to prevent abuse. Uses in-memory
    storage for simplicity (production should use Redis).
    
    Args:
        phone: Phone number to check rate limits for.
        max_requests: Maximum allowed requests in the time window.
        window_seconds: Time window in seconds for rate limiting.
        
    Returns:
        bool: True if request is allowed, False if rate limit exceeded.
    """
```

### Agent Runtime Example

```python
def run_thread(thread_id: Optional[str], user_msg: str) -> Tuple[str, str, List[Dict[str, Any]]]:
    """Execute conversation turn with OpenAI Assistant.
    
    Sends user message to assistant, handles tool calls, and returns response.
    Creates new thread lazily if none provided. Implements exponential backoff
    polling for run completion with timeout protection.
    
    Args:
        thread_id: Optional conversation thread ID. Creates new if None.
        user_msg: User's message content to send to assistant.
        
    Returns:
        Tuple containing:
            - Assistant's reply text
            - Thread ID (created if was None)
            - List of tool call data (currently empty)
            
    Raises:
        RuntimeError: If run fails, is cancelled, or times out after max attempts.
        Exception: If API calls fail due to network or authentication issues.
    """
```

## Integration with IDEs

Most modern IDEs support Google-style docstrings:

- **VS Code**: Install Python extension for docstring support
- **PyCharm**: Built-in Google docstring templates
- **Vim/Neovim**: Use plugins like `vim-python-docstring`

## Resources

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [PEP 257 - Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)
- [pydocstyle Documentation](http://www.pydocstyle.org/)

## Questions?

For questions about documentation standards or exceptions to these guidelines, please:

1. Check existing code examples in the repository
2. Refer to the Google Python Style Guide
3. Create an issue for clarification on complex cases

Remember: Good documentation is an investment in the maintainability and usability of our codebase. Take the time to write clear, helpful docstrings that future developers (including yourself) will appreciate.