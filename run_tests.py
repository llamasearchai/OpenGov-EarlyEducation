#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete test runner for OpenEarlyEducation.

Runs all tests with comprehensive reporting and validation.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


class TestRunner:
    """Comprehensive test runner with reporting."""

    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        self.failed_tests = []
        self.passed_tests = []

    def run_command(self, cmd: List[str], description: str) -> Tuple[bool, str]:
        """Run a command and return success status and output."""
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, cwd=Path(__file__).parent
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, f"Error running {description}: {e}"

    def run_unit_tests(self) -> bool:
        """Run unit tests."""
        print("Running unit tests...")

        success, output = self.run_command(
            ["python", "-m", "pytest", "tests/test_models.py", "-v"], "unit tests"
        )

        self.test_results["unit_tests"] = {"passed": success, "output": output}

        if success:
            print("Unit tests passed")
            self.passed_tests.append("unit_tests")
        else:
            print("Unit tests failed")
            self.failed_tests.append("unit_tests")

        print(output)
        return success

    def run_database_tests(self) -> bool:
        """Run database tests."""
        print("Running database tests...")

        success, output = self.run_command(
            ["python", "-m", "pytest", "tests/test_database.py", "-v"], "database tests"
        )

        self.test_results["database_tests"] = {"passed": success, "output": output}

        if success:
            print("Database tests passed")
            self.passed_tests.append("database_tests")
        else:
            print("Database tests failed")
            self.failed_tests.append("database_tests")

        print(output)
        return success

    def run_integration_tests(self) -> bool:
        """Run integration tests."""
        print("Running integration tests...")

        success, output = self.run_command(
            ["python", "-m", "pytest", "tests/test_integration.py", "-v"], "integration tests"
        )

        self.test_results["integration_tests"] = {"passed": success, "output": output}

        if success:
            print("Integration tests passed")
            self.passed_tests.append("integration_tests")
        else:
            print("Integration tests failed")
            self.failed_tests.append("integration_tests")

        print(output)
        return success

    def run_all_tests(self) -> bool:
        """Run all tests."""
        print("Running complete test suite...")
        print("=" * 60)

        tests_passed = True

        # Run different test categories
        if not self.run_unit_tests():
            tests_passed = False

        print("\n" + "=" * 60 + "\n")

        if not self.run_database_tests():
            tests_passed = False

        print("\n" + "=" * 60 + "\n")

        if not self.run_integration_tests():
            tests_passed = False

        print("\n" + "=" * 60 + "\n")

        return tests_passed

    def run_coverage_report(self) -> bool:
        """Run coverage report."""
        print("Generating coverage report...")

        success, output = self.run_command(
            ["python", "-m", "pytest", "--cov=src", "--cov-report=html", "--cov-report=term"],
            "coverage report",
        )

        if success:
            print("Coverage report generated")
            print("Coverage report available in: htmlcov/index.html")
        else:
            print("Coverage report generation had issues")

        print(output)
        return success

    def validate_system_health(self) -> bool:
        """Run system health validation."""
        print("Running system health check...")

        try:
            # Import the validation script
            from validate_system import main as validate_main

            result = validate_main()
            return result == 0
        except Exception as e:
            print(f"System validation failed: {e}")
            return False

    def run_linting(self) -> bool:
        """Run code linting."""
        print("Running code linting...")

        all_passed = True

        # Black formatting check
        success, output = self.run_command(
            ["python", "-m", "black", "--check", "--diff", "src/", "tests/"],
            "black formatting check",
        )

        if success:
            print("Code formatting is correct (Black)")
        else:
            print("Code formatting issues found (Black)")
            print(output)
            all_passed = False

        # Flake8 linting (core + tests to keep scope focused)
        success, output = self.run_command(
            ["python", "-m", "flake8", "src/core/", "tests/"], "flake8 linting"
        )

        if success:
            print("No linting issues (Flake8)")
        else:
            print("Linting issues found (Flake8)")
            print(output)
            all_passed = False

        # Mypy type checking (core only)
        success, output = self.run_command(
            ["python", "-m", "mypy", "src/core"], "mypy type checking"
        )

        if success:
            print("Type checking passed (mypy)")
        else:
            print("Type checking issues found (mypy)")
            print(output)
            all_passed = False

        return all_passed

    def generate_test_report(self) -> None:
        """Generate comprehensive test report."""
        print("\n" + "=" * 60)
        print("COMPREHENSIVE TEST REPORT")
        print("=" * 60)

        total_tests = len(self.passed_tests) + len(self.failed_tests)
        passed_count = len(self.passed_tests)
        failed_count = len(self.failed_tests)

        print(f"Total Test Categories: {total_tests}")
        print(f"Passed: {passed_count}")
        print(f"Failed: {failed_count}")
        print(
            f"Success Rate: {((passed_count / total_tests) * 100):.1f}%"
            if total_tests > 0
            else "N/A"
        )

        if self.failed_tests:
            print(f"\nFailed Tests: {', '.join(self.failed_tests)}")
            for test_name in self.failed_tests:
                if test_name in self.test_results:
                    print(f"\n--- {test_name.upper()} OUTPUT ---")
                    print(self.test_results[test_name]["output"][-1000:])  # Last 1000 chars
        else:
            print("\nAll tests passed!")

    def run_full_validation(self) -> int:
        """Run complete validation suite."""
        print("OpenEarlyEducation Complete Validation Suite")
        print("=" * 60)

        # Run all tests
        tests_passed = self.run_all_tests()

        print("\n" + "=" * 60)

        # Run linting
        linting_passed = self.run_linting()

        print("\n" + "=" * 60)

        # Run system health check
        health_ok = self.validate_system_health()

        print("\n" + "=" * 60)

        # Generate coverage report if tests passed
        if tests_passed:
            self.run_coverage_report()

        # Generate final report
        print("\n" + "=" * 60)
        self.generate_test_report()

        # Return appropriate exit code
        if tests_passed and linting_passed and health_ok:
            print("VALIDATION COMPLETE - All systems operational!")
            return 0
        else:
            print("VALIDATION COMPLETE - Some issues require attention")
            return 1


def main() -> int:
    """Main test runner function."""
    runner = TestRunner()
    return runner.run_full_validation()


if __name__ == "__main__":
    sys.exit(main())
