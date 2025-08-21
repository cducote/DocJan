#!/usr/bin/env python3
"""
Test runner for DocJan project.

Runs unit tests for backend services and provides test reporting.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_backend_tests():
    """Run Python backend tests using pytest."""
    print("🧪 Running Backend Unit Tests...")
    print("=" * 60)
    
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Run pytest with coverage
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/",
            "-v",
            "--tb=short",
            "--color=yes"
        ], check=True)
        
        print("\n✅ Backend tests completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Backend tests failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("\n❌ pytest not found. Install with: pip install pytest")
        return False


def run_integration_tests():
    """Run integration tests that require external services."""
    print("\n🔗 Running Integration Tests...")
    print("=" * 60)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/",
            "-m", "integration",
            "-v",
            "--tb=short"
        ], check=True)
        
        print("\n✅ Integration tests completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Integration tests failed with exit code {e.returncode}")
        return False


def check_test_coverage():
    """Generate test coverage report."""
    print("\n📊 Generating Test Coverage Report...")
    print("=" * 60)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/",
            "--cov=services",
            "--cov=confluence", 
            "--cov=models",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ], check=True)
        
        print("\n✅ Coverage report generated!")
        print("📁 HTML report available at: htmlcov/index.html")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Coverage generation failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("\n❌ pytest-cov not found. Install with: pip install pytest-cov")
        return False


def main():
    """Main test runner function."""
    print("🚀 DocJan Test Suite")
    print("=" * 60)
    
    # Check if pytest is available
    try:
        subprocess.run([sys.executable, "-c", "import pytest"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ pytest not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-cov"], check=True)
    
    success = True
    
    # Run backend tests
    if not run_backend_tests():
        success = False
    
    # Ask about integration tests
    if success:
        run_integration = input("\n🔗 Run integration tests? (requires Confluence access) [y/N]: ").lower()
        if run_integration in ['y', 'yes']:
            if not run_integration_tests():
                success = False
    
    # Generate coverage report
    if success:
        generate_coverage = input("\n📊 Generate coverage report? [y/N]: ").lower()
        if generate_coverage in ['y', 'yes']:
            check_test_coverage()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests completed successfully!")
        return 0
    else:
        print("💥 Some tests failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
