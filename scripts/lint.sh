#!/bin/bash

# Automated Code Quality Check Script
# Runs all linting and documentation checks

set -e

echo "🔍 Running code quality checks..."

echo "📝 Checking docstring style with pydocstyle..."
python3 -m pydocstyle app/ --convention=google --match-dir="(?!tests|migrations|scripts)" --match="(?!test_|conftest).*\.py"

echo "⚫ Checking code formatting with black..."
python3 -m black --check --diff app/ --line-length=100

echo "🚀 Running ruff linter..."
python3 -m ruff check app/ --fix

echo "🧪 Running pytest..."
python3 -m pytest --tb=short -v

echo "✅ All checks passed!"