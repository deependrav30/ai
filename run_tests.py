#!/usr/bin/env python3
"""
Test runner script for the AI Support System

Usage:
    python run_tests.py                 # Run all tests
    python run_tests.py unit            # Run only unit tests
    python run_tests.py integration     # Run only integration tests
    python run_tests.py --coverage      # Run with coverage report
"""

import sys
import subprocess
from pathlib import Path


def run_tests(test_type=None, coverage=False):
    """
    Run pytest with specified options
    
    Args:
        test_type: 'unit', 'integration', or None for all
        coverage: Whether to include coverage report
    """
    # Base pytest command
    cmd = ['pytest']
    
    # Add test type marker if specified
    if test_type == 'unit':
        cmd.extend(['-m', 'unit'])
        print("🧪 Running unit tests...")
    elif test_type == 'integration':
        cmd.extend(['-m', 'integration'])
        print("🔗 Running integration tests...")
    else:
        print("🧪 Running all tests...")
    
    # Add coverage if requested
    if coverage:
        cmd.extend(['--cov=agents', '--cov=integrations', '--cov-report=html', '--cov-report=term'])
        print("📊 Coverage report will be generated...")
    
    # Add verbose output
    cmd.append('-v')
    
    # Run pytest
    print(f"\nCommand: {' '.join(cmd)}\n")
    print("=" * 80)
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    print("=" * 80)
    
    if result.returncode == 0:
        print("\n✅ All tests passed!")
        if coverage:
            print("\n📊 Coverage report generated at: htmlcov/index.html")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


def main():
    """Parse arguments and run tests"""
    args = sys.argv[1:]
    
    test_type = None
    coverage = '--coverage' in args or '-c' in args
    
    if 'unit' in args:
        test_type = 'unit'
    elif 'integration' in args:
        test_type = 'integration'
    
    # Show help if requested
    if '--help' in args or '-h' in args:
        print(__doc__)
        return
    
    try:
        run_tests(test_type, coverage)
    except FileNotFoundError:
        print("❌ pytest not found. Install it with: pip install pytest pytest-asyncio pytest-cov")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)


if __name__ == '__main__':
    main()
