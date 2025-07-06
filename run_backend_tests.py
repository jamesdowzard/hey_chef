#!/usr/bin/env python3
"""
Test runner for Hey Chef v2 backend tests.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def run_backend_tests():
    """Run backend tests with proper Python path setup."""
    
    # Set environment variables
    os.environ['PYTHONPATH'] = str(project_root)
    os.environ['ENVIRONMENT'] = 'test'
    
    # Run pytest with proper configuration
    test_command = [
        sys.executable, '-m', 'pytest',
        'tests/backend/',
        '-v',
        '--tb=short',
        '--color=yes',
        '--durations=10'
    ]
    
    print("Running Hey Chef v2 backend tests...")
    print(f"Project root: {project_root}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    print(f"Test command: {' '.join(test_command)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(test_command, cwd=project_root, check=False)
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_backend_tests()
    sys.exit(exit_code)