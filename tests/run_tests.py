"""
Test Runner Script

Convenient script to run tests with various options.
"""

import sys
import subprocess
from pathlib import Path


def run_tests(args=None):
    """
    Run pytest with specified arguments.
    
    Args:
        args: List of additional pytest arguments
    """
    if args is None:
        args = []
    
    # Base command
    cmd = ["pytest"] + args
    
    print(f"Running: {' '.join(cmd)}")
    print("=" * 70)
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run AI-Symp-Controller tests")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--failed", action="store_true", help="Re-run failed tests")
    parser.add_argument("--pdb", action="store_true", help="Drop into debugger on failure")
    parser.add_argument("args", nargs="*", help="Additional pytest arguments")
    
    args = parser.parse_args()
    
    pytest_args = args.args.copy()
    
    if args.unit:
        pytest_args.extend(["-m", "unit"])
    
    if args.integration:
        pytest_args.extend(["-m", "integration"])
    
    if args.fast:
        pytest_args.extend(["-m", "not slow"])
    
    if args.coverage:
        pytest_args.extend(["--cov=modules", "--cov-report=html", "--cov-report=term"])
    
    if args.verbose:
        pytest_args.append("-vv")
    
    if args.failed:
        pytest_args.append("--lf")
    
    if args.pdb:
        pytest_args.append("--pdb")
    
    return run_tests(pytest_args)


if __name__ == "__main__":
    sys.exit(main())

