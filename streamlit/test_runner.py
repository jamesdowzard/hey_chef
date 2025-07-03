#!/usr/bin/env python3
"""
Automated test runner for Hey Chef application.
Runs comprehensive test suite and reports results.
"""
import subprocess
import sys
import os
from pathlib import Path
import json
import time
from typing import Dict, List, Tuple


class TestRunner:
    """Runs and manages test execution for the Hey Chef application."""
    
    def __init__(self, project_root: str = None):
        """Initialize test runner."""
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.test_dir = self.project_root / "test"
        self.results = {}
        
    def run_all_tests(self) -> Dict:
        """Run all tests and return comprehensive results."""
        print("🧪 Starting comprehensive test suite for Hey Chef...")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run different test categories
        test_categories = [
            ("Unit Tests", self._run_unit_tests),
            ("Integration Tests", self._run_integration_tests),
            ("Notion API Tests", self._run_notion_tests),
            ("Configuration Tests", self._run_config_tests),
        ]
        
        all_results = {}
        overall_success = True
        
        for category_name, test_func in test_categories:
            print(f"\n📋 Running {category_name}...")
            print("-" * 40)
            
            try:
                result = test_func()
                all_results[category_name] = result
                
                if result["success"]:
                    print(f"✅ {category_name}: PASSED ({result['tests_run']} tests)")
                else:
                    print(f"❌ {category_name}: FAILED ({result['failures']} failures)")
                    overall_success = False
                    
            except Exception as e:
                print(f"💥 {category_name}: ERROR - {e}")
                all_results[category_name] = {
                    "success": False,
                    "error": str(e),
                    "tests_run": 0,
                    "failures": 1
                }
                overall_success = False
        
        end_time = time.time()
        
        # Generate summary
        summary = self._generate_summary(all_results, end_time - start_time)
        summary["overall_success"] = overall_success
        
        self._print_summary(summary)
        return summary
    
    def _run_unit_tests(self) -> Dict:
        """Run unit tests."""
        return self._run_pytest_category([
            "test_audio_components.py",
            "test_config.py"
        ])
    
    def _run_integration_tests(self) -> Dict:
        """Run integration tests."""
        return self._run_pytest_category([
            "test_app_functions.py"
        ])
    
    def _run_notion_tests(self) -> Dict:
        """Run Notion API tests."""
        return self._run_pytest_category([
            "test_notion_api.py"
        ])
    
    def _run_config_tests(self) -> Dict:
        """Run configuration tests."""
        return self._run_pytest_category([
            "test_config.py::TestSettings",
            "test_config.py::TestChefPrompts"
        ])
    
    def _run_pytest_category(self, test_files: List[str]) -> Dict:
        """Run pytest on specific test files."""
        # Build pytest command
        cmd = ["python", "-m", "pytest", "-v", "--tb=short"]
        
        # Add specific test files
        for test_file in test_files:
            test_path = self.test_dir / test_file
            if test_path.exists():
                cmd.append(str(test_path))
        
        # Run tests
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return self._parse_pytest_output(result)
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Tests timed out after 5 minutes",
                "tests_run": 0,
                "failures": 1,
                "output": ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to run tests: {e}",
                "tests_run": 0,
                "failures": 1,
                "output": ""
            }
    
    def _parse_pytest_output(self, result: subprocess.CompletedProcess) -> Dict:
        """Parse pytest output and extract results."""
        output = result.stdout + result.stderr
        
        # Extract test counts from pytest output
        tests_run = 0
        failures = 0
        errors = 0
        
        lines = output.split('\n')
        for line in lines:
            if 'passed' in line and ('failed' in line or 'error' in line):
                # Line like: "2 failed, 3 passed in 1.23s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed":
                        tests_run += int(parts[i-1])
                    elif part == "failed":
                        failures += int(parts[i-1])
                    elif part == "error":
                        errors += int(parts[i-1])
            elif 'passed' in line and line.strip().endswith('s'):
                # Line like: "5 passed in 1.23s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed":
                        tests_run += int(parts[i-1])
        
        return {
            "success": result.returncode == 0,
            "tests_run": tests_run,
            "failures": failures + errors,
            "output": output,
            "return_code": result.returncode
        }
    
    def _generate_summary(self, results: Dict, duration: float) -> Dict:
        """Generate test summary."""
        total_tests = sum(r.get("tests_run", 0) for r in results.values())
        total_failures = sum(r.get("failures", 0) for r in results.values())
        
        return {
            "total_tests": total_tests,
            "total_failures": total_failures,
            "success_rate": (total_tests - total_failures) / total_tests * 100 if total_tests > 0 else 0,
            "duration": duration,
            "categories": results
        }
    
    def _print_summary(self, summary: Dict):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        print(f"Total Tests Run: {summary['total_tests']}")
        print(f"Failures: {summary['total_failures']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Duration: {summary['duration']:.2f} seconds")
        
        if summary["overall_success"]:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print("\n⚠️  SOME TESTS FAILED")
            print("\nFailed Categories:")
            for category, result in summary["categories"].items():
                if not result.get("success", True):
                    print(f"  - {category}: {result.get('failures', 0)} failures")
        
        print("=" * 60)
    
    def run_specific_tests(self, test_pattern: str) -> Dict:
        """Run tests matching a specific pattern."""
        cmd = ["python", "-m", "pytest", "-v", "--tb=short", "-k", test_pattern]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return self._parse_pytest_output(result)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to run tests: {e}",
                "tests_run": 0,
                "failures": 1
            }
    
    def check_test_environment(self) -> bool:
        """Check if test environment is properly set up."""
        print("🔍 Checking test environment...")
        
        # Check if pytest is installed
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print("❌ pytest not installed")
                return False
            print("✅ pytest available")
        except Exception:
            print("❌ pytest not available")
            return False
        
        # Check if test files exist
        test_files = [
            "test_notion_api.py",
            "test_app_functions.py", 
            "test_audio_components.py",
            "test_config.py"
        ]
        
        missing_files = []
        for test_file in test_files:
            if not (self.test_dir / test_file).exists():
                missing_files.append(test_file)
        
        if missing_files:
            print(f"❌ Missing test files: {missing_files}")
            return False
        
        print("✅ All test files present")
        
        # Check if source modules can be imported
        sys.path.append(str(self.project_root / "src"))
        
        try:
            import config.settings
            import audio.speech_to_text
            import ui.app
            print("✅ Source modules can be imported")
        except ImportError as e:
            print(f"❌ Cannot import source modules: {e}")
            return False
        
        print("✅ Test environment ready")
        return True


def main():
    """Main entry point for test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Hey Chef test suite")
    parser.add_argument("--pattern", "-k", help="Run tests matching pattern")
    parser.add_argument("--check-env", action="store_true", help="Check test environment")
    parser.add_argument("--project-root", help="Project root directory")
    
    args = parser.parse_args()
    
    runner = TestRunner(args.project_root)
    
    if args.check_env:
        if runner.check_test_environment():
            print("✅ Test environment is ready")
            sys.exit(0)
        else:
            print("❌ Test environment has issues")
            sys.exit(1)
    
    if args.pattern:
        result = runner.run_specific_tests(args.pattern)
        if result["success"]:
            print(f"✅ Tests matching '{args.pattern}' passed")
            sys.exit(0)
        else:
            print(f"❌ Tests matching '{args.pattern}' failed")
            sys.exit(1)
    
    # Run all tests
    summary = runner.run_all_tests()
    
    if summary["overall_success"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()