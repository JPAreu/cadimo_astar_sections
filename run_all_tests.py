#!/usr/bin/env python3
"""
run_all_tests.py - Comprehensive Test Runner for CADIMO A* Pathfinding

This script runs all test suites in the tests/ directory and provides
a comprehensive report of the results.
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def run_test_file(test_file):
    """Run a single test file and return results."""
    print(f"\n{'='*80}")
    print(f"🧪 Running {test_file}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, f"tests/{test_file}"], 
            capture_output=True, 
            text=True, 
            timeout=300  # 5 minute timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        
        print(f"\n{'✅ PASSED' if success else '❌ FAILED'} - {test_file} ({duration:.2f}s)")
        
        return {
            'file': test_file,
            'success': success,
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT - {test_file} took too long (>5 minutes)")
        return {
            'file': test_file,
            'success': False,
            'duration': 300,
            'stdout': '',
            'stderr': 'Test timed out',
            'returncode': -1
        }
    except Exception as e:
        print(f"💥 ERROR - {test_file}: {e}")
        return {
            'file': test_file,
            'success': False,
            'duration': 0,
            'stdout': '',
            'stderr': str(e),
            'returncode': -2
        }

def main():
    """Run all test files and provide comprehensive results."""
    print("🚀 CADIMO A* Pathfinding - Comprehensive Test Suite")
    print("="*80)
    
    # Find all test files
    tests_dir = Path("tests")
    if not tests_dir.exists():
        print("❌ Tests directory not found!")
        return False
    
    test_files = sorted([f.name for f in tests_dir.glob("test_*.py")])
    
    if not test_files:
        print("❌ No test files found in tests/ directory!")
        return False
    
    print(f"Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  • {test_file}")
    
    # Run all tests
    results = []
    total_start_time = time.time()
    
    for test_file in test_files:
        result = run_test_file(test_file)
        results.append(result)
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Generate summary report
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
    print(f"{'='*80}")
    
    passed_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    print(f"Total Tests: {len(results)}")
    print(f"✅ Passed: {len(passed_tests)}")
    print(f"❌ Failed: {len(failed_tests)}")
    print(f"⏱️  Total Time: {total_duration:.2f} seconds")
    
    # Detailed results table
    print(f"\n{'Test File':<30} {'Status':<10} {'Duration':<10}")
    print("-" * 50)
    
    for result in results:
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        duration = f"{result['duration']:.2f}s"
        print(f"{result['file']:<30} {status:<10} {duration:<10}")
    
    # Show failures in detail
    if failed_tests:
        print(f"\n{'='*80}")
        print("❌ FAILED TESTS DETAILS")
        print(f"{'='*80}")
        
        for result in failed_tests:
            print(f"\n🔍 {result['file']}:")
            print(f"   Return code: {result['returncode']}")
            if result['stderr']:
                print(f"   Error: {result['stderr']}")
            if result['stdout'] and len(result['stdout']) < 500:
                print(f"   Output: {result['stdout'][:500]}...")
    
    # Overall result
    print(f"\n{'='*80}")
    if len(failed_tests) == 0:
        print("🎉 ALL TESTS PASSED! The A* pathfinding system is working correctly.")
        print("✅ All algorithms (direct, PPO, multi-PPO, forward path, system filtering) are functional.")
        print("✅ All edge cases and error conditions are properly handled.")
        print("✅ All graph formats and data structures are compatible.")
        return True
    else:
        print(f"⚠️  {len(failed_tests)} TEST(S) FAILED! Please review the failures above.")
        print("🔧 Check the individual test outputs for debugging information.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 