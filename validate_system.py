#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System validation script for OpenEarlyEducation.

Runs comprehensive tests, validates configuration, and checks system health.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def run_command(cmd: List[str], description: str) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, f"Error running {description}: {e}"


def validate_python_environment() -> bool:
    """Validate Python environment and dependencies."""
    print("Validating Python environment...")

    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 11):
        print(f"Python version {python_version.major}.{python_version.minor} is not supported")
        print("   Please use Python 3.11 or higher")
        return False

    print(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} detected")

    # Check if we're in a virtual environment
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    if not in_venv:
        print("Warning: Not running in a virtual environment")
        print("   Consider using: python -m venv venv && source venv/bin/activate")

    return True


def validate_dependencies() -> bool:
    """Validate that all dependencies are installed."""
    print("Validating dependencies...")

    try:
        import openai

        print("OpenAI package installed")
    except ImportError:
        print("OpenAI package not installed")
        return False

    try:
        import fastapi

        print("FastAPI package installed")
    except ImportError:
        print("FastAPI package not installed")
        return False

    try:
        import rich

        print("Rich (TUI) package installed")
    except ImportError:
        print("Rich package not installed")
        return False

    try:
        import pydantic

        print("Pydantic package installed")
    except ImportError:
        print("Pydantic package not installed")
        return False

    try:
        import jinja2

        print("Jinja2 package installed")
    except ImportError:
        print("Jinja2 package not installed")
        return False

    return True


def run_tests() -> bool:
    """Run the test suite."""
    print("Running test suite...")

    success, output = run_command(["python", "-m", "pytest", "--tb=short"], "pytest")
    if success:
        print("All tests passed!")
        print(output)
        return True
    else:
        print("Some tests failed:")
        print(output)
        return False


def validate_configuration() -> bool:
    """Validate system configuration."""
    print("Validating configuration...")

    # Check if .env file exists or if OPENAI_API_KEY is set
    env_file = Path(".env")
    api_key_set = os.getenv("OPENAI_API_KEY") is not None

    if not api_key_set and not env_file.exists():
        print("Warning: OPENAI_API_KEY not set and no .env file found")
        print("   The system won't work without an OpenAI API key")
    elif api_key_set:
        print("OpenAI API key is configured")
    else:
        print("Configuration files found")

    # Check if required directories exist
    required_dirs = ["data", "logs", "src/core/templates"]
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"Directory {dir_name} exists")
        else:
            print(f"Directory {dir_name} not found (will be created on first run)")

    return True


def validate_code_structure() -> bool:
    """Validate that the code structure is correct."""
    print("Validating code structure...")

    required_files = [
        "src/main.py",
        "src/core/config.py",
        "src/core/database.py",
        "src/core/models.py",
        "src/core/assistant.py",
        "src/core/engine.py",
        "src/core/reports.py",
        "src/core/assessment.py",
        "src/tui/app.py",
        "src/api/app.py",
        "requirements.txt",
        "README.md",
        "setup.py",
        "pyproject.toml",
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print("Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False

    print("All required files present")
    return True


def validate_docker_setup() -> bool:
    """Validate Docker setup."""
    print("Validating Docker setup...")

    success, output = run_command(["docker", "--version"], "docker version check")
    if success:
        print("Docker is installed")
    else:
        print("Docker not found (optional)")
        return True  # Docker is optional

    # Check if Dockerfile exists
    if Path("Dockerfile").exists():
        print("Dockerfile found")
    else:
        print("Dockerfile not found")
        return True

    # Check if docker-compose.yml exists
    if Path("docker-compose.yml").exists():
        print("Docker Compose configuration found")
    else:
        print("Docker Compose configuration not found")
        return True

    return True


def validate_git_setup() -> bool:
    """Validate Git setup."""
    print("Validating Git setup...")

    success, output = run_command(["git", "--version"], "git version check")
    if success:
        print("Git is installed")
    else:
        print("Git not found")
        return False

    # Check if we're in a git repository
    success, output = run_command(["git", "rev-parse", "--git-dir"], "git repo check")
    if success:
        print("Git repository initialized")
    else:
        print("Not a Git repository")
        return True  # This is OK for initial setup

    return True


def main() -> int:
    """Main validation function."""
    print("OpenEarlyEducation System Validation")
    print("=" * 50)

    validation_checks = [
        validate_python_environment,
        validate_dependencies,
        validate_code_structure,
        validate_configuration,
        validate_git_setup,
        validate_docker_setup,
    ]

    all_passed = True
    for check in validation_checks:
        try:
            if not check():
                all_passed = False
            print()
        except Exception as e:
            print(f"Error during {check.__name__}: {e}")
            all_passed = False
            print()

    # Run tests separately (they might take longer)
    if all_passed:
        if not run_tests():
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("System validation completed successfully!")
        print("OpenEarlyEducation is ready to use")
        print()
        print("Next steps:")
        print("1. Set your OpenAI API key: export OPENAI_API_KEY='your-key'")
        print("2. Run the TUI: python -m src.main tui")
        print("3. Or start the API server: python -m src.main api")
        return 0
    else:
        print("System validation failed!")
        print("Please fix the issues above before running OpenEarlyEducation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
