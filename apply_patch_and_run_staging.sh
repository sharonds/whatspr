#!/bin/bash
#
# apply_patch_and_run_staging.sh
#
# This script applies the PR1 patch, runs tests, commits the changes
# to a new staging branch, and starts the staging server.

# --- Configuration ---
set -e # Exit immediately if a command exits with a non-zero status.
set -o pipefail # Return value of a pipeline is the value of the last command to exit with a non-zero status

# --- Variables ---
ZIP_FILE="~/downloads/PR1_atomic_tools.zip"
BRANCH_NAME="feat/atomic-tools-staging" # Use feat/ or fix/ convention
REMOTE_NAME="origin"
STAGING_PORT=8001

# --- Functions ---
function info() {
  echo -e "\033[0;32m[INFO]\033[0m $1"
}

function error() {
  echo -e "\033[0;31m[ERROR]\033[0m $1" >&2
  exit 1
}

function apply_patch() {
  info "Unzipping patch from ${ZIP_FILE}..."
  if [ ! -f "${ZIP_FILE}" ]; then
    error "Zip file not found at ${ZIP_FILE}. Please check the path."
  fi
  unzip -o "${ZIP_FILE}" -d .
  info "Patch applied successfully."
}

function run_tests() {
  info "Loading staging environment variables and running tests..."
  if [ ! -f ".env.staging" ]; then
      error ".env.staging file not found. Please ensure it is created and configured."
  fi
  
  # Activate virtual environment if it exists
  if [ -d "env" ]; then
    info "Activating virtual environment..."
    source env/bin/activate
  fi
  
  # Load staging environment variables
  export $(cat .env.staging | xargs)

  # Run the atomic tools tests
  info "Running atomic tools tests..."
  if [ -f "tests/test_tools_atomic.py" ]; then
    pytest tests/test_tools_atomic.py -v
  else
    info "test_tools_atomic.py not found, running safety tests instead..."
    pytest tests/test_safety.py -v
  fi
  
  info "All tests passed successfully."
}

function commit_and_push() {
  info "Creating new branch '${BRANCH_NAME}'..."
  git checkout -b "${BRANCH_NAME}"

  info "Adding and committing new files..."
  
  # Check which files exist and add them
  files_to_add=""
  
  if [ -f "app/tools_atomic.py" ]; then
    files_to_add+=" app/tools_atomic.py"
  fi
  
  if [ -f "tests/test_tools_atomic.py" ]; then
    files_to_add+=" tests/test_tools_atomic.py"
  fi
  
  if [ -f "README_PR1.md" ]; then
    files_to_add+=" README_PR1.md"
  fi
  
  if [ -f "migrations/backfill_generic_slots.py" ]; then
    files_to_add+=" migrations/backfill_generic_slots.py"
  fi
  
  if [ -n "$files_to_add" ]; then
    git add $files_to_add
    git commit -m "feat(agent): introduce atomic save_* tools for staging" \
               -m "This commit applies the PR1 patch, replacing the generic save_slot pattern with specific, atomic tools to improve agent reliability."
  else
    info "No new files from patch found to commit."
  fi

  read -p "Push new branch '${BRANCH_NAME}' to remote '${REMOTE_NAME}'? (y/N) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    info "Pushing to remote..."
    git push -u "${REMOTE_NAME}" "${BRANCH_NAME}"
  else
    info "Skipping push. You can push the branch manually later."
  fi
}

function run_server() {
  info "Starting staging server on port ${STAGING_PORT}..."
  
  # Activate virtual environment if it exists
  if [ -d "env" ]; then
    source env/bin/activate
  fi
  
  # Load staging environment variables
  if [ -f ".env.staging" ]; then
    info "Loading staging environment from .env.staging..."
    python -c "from dotenv import load_dotenv; load_dotenv(dotenv_path='.env.staging'); import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=${STAGING_PORT}, reload=True)"
  else
    uvicorn app.main:app --reload --port "${STAGING_PORT}"
  fi
}

function show_help() {
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  --skip-patch    Skip applying the patch (useful if already applied)"
  echo "  --skip-tests    Skip running tests"
  echo "  --skip-commit   Skip git operations"
  echo "  --help          Show this help message"
  echo ""
  echo "Environment Variables:"
  echo "  ZIP_FILE        Path to the patch zip file (default: ~/downloads/PR1_atomic_tools.zip)"
  echo "  BRANCH_NAME     Name of the staging branch (default: feat/atomic-tools-staging)"
  echo "  STAGING_PORT    Port for staging server (default: 8001)"
}

# --- Parse command line arguments ---
SKIP_PATCH=false
SKIP_TESTS=false
SKIP_COMMIT=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-patch)
      SKIP_PATCH=true
      shift
      ;;
    --skip-tests)
      SKIP_TESTS=true
      shift
      ;;
    --skip-commit)
      SKIP_COMMIT=true
      shift
      ;;
    --help)
      show_help
      exit 0
      ;;
    *)
      error "Unknown option: $1. Use --help for usage information."
      ;;
  esac
done

# --- Main Execution ---
info "Starting staging environment setup..."

if [ "$SKIP_PATCH" = false ]; then
  apply_patch
else
  info "Skipping patch application (--skip-patch specified)"
fi

if [ "$SKIP_TESTS" = false ]; then
  run_tests
else
  info "Skipping tests (--skip-tests specified)"
fi

if [ "$SKIP_COMMIT" = false ]; then
  commit_and_push
else
  info "Skipping git operations (--skip-commit specified)"
fi

run_server

info "Staging environment is up and running on port ${STAGING_PORT}."
