#!/usr/bin/env python3
"""
Comprehensive shell audit test suite
Tests functionality, signal handling, error handling, resource cleanup, and benchmarks
"""

import sys
import os
import subprocess
import time
import signal
import platform
import tempfile
import shutil
from contextlib import redirect_stdout, redirect_stderr
import io

# Handle readline for Windows
try:
    import readline
except ImportError:
    class DummyReadline:
        @staticmethod
        def parse_and_bind(*args, **kwargs): pass
        @staticmethod
        def set_completer(*args, **kwargs): pass
        @staticmethod
        def set_completer_delims(*args, **kwargs): pass
    sys.modules['readline'] = DummyReadline()

sys.path.insert(0, 'app')
from main import execute_command, parse_redirection
import shlex

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_test(name):
    print(f"\n{Colors.BLUE}[TEST]{Colors.RESET} {name}")

def print_pass(msg):
    print(f"  {Colors.GREEN}[PASS]{Colors.RESET}: {msg}")

def print_fail(msg):
    print(f"  {Colors.RED}[FAIL]{Colors.RESET}: {msg}")

def print_warn(msg):
    print(f"  {Colors.YELLOW}[WARN]{Colors.RESET}: {msg}")

# Test results
results = {
    'passed': [],
    'failed': [],
    'warnings': []
}

def test_functional():
    """Test 1: Functional Test"""
    print_test("1. Functional Test - cd, pwd, piped commands")
    
    # Test cd and pwd
    try:
        original_dir = os.getcwd()
        test_dir = tempfile.mkdtemp()
        
        # Test cd
        with redirect_stdout(io.StringIO()):
            execute_command("cd", ["cd", test_dir], should_print=False)
        
        if os.getcwd() == test_dir:
            print_pass("cd command works correctly")
            results['passed'].append("cd command")
        else:
            print_fail(f"cd failed: expected {test_dir}, got {os.getcwd()}")
            results['failed'].append("cd command")
        
        # Test pwd
        with redirect_stdout(io.StringIO()) as f:
            execute_command("pwd", ["pwd"], should_print=False)
            output = f.getvalue().strip()
        
        if output == test_dir:
            print_pass("pwd command works correctly")
            results['passed'].append("pwd command")
        else:
            print_fail(f"pwd failed: expected {test_dir}, got {output}")
            results['failed'].append("pwd command")
        
        # Restore directory
        os.chdir(original_dir)
        shutil.rmtree(test_dir)
        
    except Exception as e:
        print_fail(f"Functional test exception: {e}")
        results['failed'].append("functional test")
        import traceback
        traceback.print_exc()
    
    # Test piped commands (basic test - full pipe test needs shell running)
    print_warn("Piped commands test requires interactive shell - manual verification needed")

def test_error_handling():
    """Test 2: Error Robustness"""
    print_test("2. Error Robustness - Non-existent command")
    
    try:
        # Capture stderr
        stderr_capture = io.StringIO()
        
        with redirect_stderr(stderr_capture):
            with redirect_stdout(io.StringIO()) as stdout_capture:
                execute_command("nonexistentcommand12345", ["nonexistentcommand12345"], should_print=False)
                stdout_output = stdout_capture.getvalue()
        
        stderr_output = stderr_capture.getvalue()
        # Check if error message is clean (no Python traceback)
        if "nonexistentcommand12345: command not found" in stdout_output or "nonexistentcommand12345: command not found" in stderr_output:
            print_pass("Clean error message for non-existent command")
            results['passed'].append("error handling")
        elif "Traceback" in stdout_output or "Traceback" in stderr_output or "File" in stdout_output or "File" in stderr_output:
            print_fail("Python traceback shown instead of clean error")
            print_fail(f"Output: {stdout_output[:200]}...")
            results['failed'].append("error handling")
        else:
            print_warn(f"Unexpected output format: {stdout_output[:100]}")
            results['warnings'].append("error handling")
            
    except Exception as e:
        print_fail(f"Error handling test exception: {e}")
        results['failed'].append("error handling")
        import traceback
        traceback.print_exc()

def test_signal_handling():
    """Test 3: Signal Handling"""
    print_test("3. Signal Handling - Ctrl+C (SIGINT)")
    
    if platform.system() == "Windows":
        print_warn("Signal handling test requires Unix-like system (Windows uses different signal mechanism)")
        print_warn("Manual testing recommended: run 'sleep 10' and press Ctrl+C")
        results['warnings'].append("signal handling (Windows)")
        return
    
    print_warn("Signal handling requires interactive shell - manual verification needed")
    print_warn("To test: Run shell, execute 'sleep 10', press Ctrl+C")
    print_warn("Expected: Child process killed, shell continues running")
    results['warnings'].append("signal handling (needs manual test)")

def test_resource_cleanup():
    """Test 4: Resource Check - Zombie Processes"""
    print_test("4. Resource Check - Process Cleanup")
    
    if platform.system() == "Windows":
        print_warn("Zombie process check is Unix-specific")
        print_warn("Windows handles process cleanup differently")
        results['warnings'].append("zombie process check (Windows)")
        return
    
    print_warn("Zombie process check requires running processes - manual verification needed")
    print_warn("To test: Run multiple commands, check 'ps aux | grep defunct'")
    print_warn("Expected: No zombie processes")
    results['warnings'].append("zombie process check (needs manual test)")

def benchmark_echo():
    """Test 5: Benchmark - echo performance"""
    print_test("5. Benchmark - echo 'test' performance")
    
    iterations = 100
    
    # Benchmark PyShell
    print("  Benchmarking PyShell...")
    start = time.perf_counter()
    for _ in range(iterations):
        with redirect_stdout(io.StringIO()):
            execute_command("echo", ["echo", "test"], should_print=False)
    pyshell_time = (time.perf_counter() - start) * 1000 / iterations
    
    # Benchmark bash (if available)
    bash_time = None
    if platform.system() != "Windows":
        print("  Benchmarking Bash...")
        start = time.perf_counter()
        for _ in range(iterations):
            try:
                subprocess.run(["bash", "-c", "echo test"], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL,
                             timeout=0.1)
            except:
                pass
        bash_time = (time.perf_counter() - start) * 1000 / iterations
    else:
        # Test CMD on Windows
        print("  Benchmarking CMD...")
        start = time.perf_counter()
        for _ in range(iterations):
            try:
                subprocess.run(["cmd", "/c", "echo test"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             timeout=0.1,
                             creationflags=subprocess.CREATE_NO_WINDOW)
            except:
                pass
        cmd_time = (time.perf_counter() - start) * 1000 / iterations
        bash_time = cmd_time
        print(f"  CMD time: {cmd_time:.3f}ms per command")
    
    print(f"  PyShell time: {pyshell_time:.3f}ms per command")
    if bash_time:
        print(f"  Bash/CMD time: {bash_time:.3f}ms per command")
        diff = pyshell_time - bash_time
        print(f"  Difference: {diff:.3f}ms ({diff/bash_time*100:.1f}% slower)")
        results['passed'].append(f"benchmark (PyShell: {pyshell_time:.3f}ms, Bash: {bash_time:.3f}ms, diff: {diff:.3f}ms)")
    else:
        results['passed'].append(f"benchmark (PyShell: {pyshell_time:.3f}ms)")

def main():
    """Run all tests"""
    print("=" * 70)
    print("PyShell Production Readiness Audit")
    print("=" * 70)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")
    print("=" * 70)
    
    test_functional()
    test_error_handling()
    test_signal_handling()
    test_resource_cleanup()
    benchmark_echo()
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"{Colors.GREEN}Passed: {len(results['passed'])}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {len(results['failed'])}{Colors.RESET}")
    print(f"{Colors.YELLOW}Warnings: {len(results['warnings'])}{Colors.RESET}")
    
    if results['failed']:
        print(f"\n{Colors.RED}Failed Tests:{Colors.RESET}")
        for test in results['failed']:
            print(f"  - {test}")
    
    if results['warnings']:
        print(f"\n{Colors.YELLOW}Warnings (require manual testing):{Colors.RESET}")
        for test in results['warnings']:
            print(f"  - {test}")
    
    print("\n" + "=" * 70)
    
    return 0 if len(results['failed']) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

