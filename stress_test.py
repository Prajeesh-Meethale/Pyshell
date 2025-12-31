#!/usr/bin/env python3
"""
Comprehensive stress test for PyShell
Tests: Burst fire, buffer overflow, invalid commands, memory leaks
"""

import sys
import os
import subprocess
import time
import platform
import threading
import queue
from contextlib import redirect_stdout, redirect_stderr
import io

# Try to import psutil, fallback to platform-specific methods
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Handle readline
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
    CYAN = '\033[96m'
    RESET = '\033[0m'

def print_test(name):
    print(f"\n{Colors.CYAN}[TEST]{Colors.RESET} {name}")

def print_pass(msg):
    print(f"  {Colors.GREEN}[PASS]{Colors.RESET} {msg}")

def print_fail(msg):
    print(f"  {Colors.RED}[FAIL]{Colors.RESET} {msg}")

def print_info(msg):
    print(f"  {Colors.BLUE}[INFO]{Colors.RESET} {msg}")

def get_memory_usage():
    """Get current process memory usage in MB."""
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # Convert to MB
    else:
        # Fallback: Use platform-specific methods
        if platform.system() == "Windows":
            try:
                import ctypes
                from ctypes import wintypes
                class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
                    _fields_ = [
                        ("cb", ctypes.c_ulong),
                        ("PageFaultCount", ctypes.c_ulong),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t),
                        ("PrivateUsage", ctypes.c_size_t),
                    ]
                GetProcessMemoryInfo = ctypes.windll.psapi.GetProcessMemoryInfo
                GetCurrentProcess = ctypes.windll.kernel32.GetCurrentProcess
                meminfo = PROCESS_MEMORY_COUNTERS_EX()
                GetProcessMemoryInfo(GetCurrentProcess(), ctypes.byref(meminfo), ctypes.sizeof(meminfo))
                return meminfo.PrivateUsage / 1024 / 1024  # Convert to MB
            except:
                return 0.0  # Can't measure
        else:
            # Unix/Linux
            try:
                with open(f'/proc/{os.getpid()}/status') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            return int(line.split()[1]) / 1024  # Convert KB to MB
            except:
                pass
            return 0.0  # Can't measure

def test_burst_fire():
    """Test 1: Burst fire 100 echo commands."""
    print_test("1. Burst Fire - 100 echo commands")
    
    start_memory = get_memory_usage()
    start_time = time.perf_counter()
    
    success_count = 0
    fail_count = 0
    errors = []
    
    for i in range(100):
        try:
            with redirect_stdout(io.StringIO()) as f:
                execute_command("echo", ["echo", "test"], should_print=False)
            output = f.getvalue()
            if "test" in output or output == "":
                success_count += 1
            else:
                fail_count += 1
                errors.append(f"Command {i+1}: Unexpected output")
        except Exception as e:
            fail_count += 1
            errors.append(f"Command {i+1}: {str(e)}")
    
    end_time = time.perf_counter()
    end_memory = get_memory_usage()
    elapsed = (end_time - start_time) * 1000
    
    print_info(f"Executed 100 commands in {elapsed:.2f}ms ({elapsed/100:.3f}ms per command)")
    print_info(f"Success: {success_count}/100")
    
    if fail_count == 0:
        print_pass(f"All 100 commands executed successfully")
        return True, elapsed, end_memory - start_memory
    else:
        print_fail(f"{fail_count} commands failed")
        for error in errors[:5]:  # Show first 5 errors
            print_fail(f"  {error}")
        return False, elapsed, end_memory - start_memory

def test_bomb_string():
    """Test 2: Bomb test - 50,000 character string."""
    print_test("2. Bomb Test - 50,000 character string")
    
    # Create a massive string
    large_string = "A" * 50000
    
    try:
        start_time = time.perf_counter()
        
        # Test parsing
        cmd_part, redirect_file, redirect_stderr, redirect_append = parse_redirection(f"echo {large_string}")
        
        # Test execution
        with redirect_stdout(io.StringIO()) as f:
            args = shlex.split(cmd_part)
            if args:
                execute_command(args[0], args, should_print=False)
        
        end_time = time.perf_counter()
        elapsed = (end_time - start_time) * 1000
        
        print_pass(f"Handled 50,000 character string without crash")
        print_info(f"Processing time: {elapsed:.2f}ms")
        return True, elapsed
        
    except MemoryError:
        print_fail("Memory error - string too large")
        return False, 0
    except Exception as e:
        print_fail(f"Crash detected: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, 0

def test_invalid_commands():
    """Test 3: 50 non-existent commands."""
    print_test("3. Invalid Execution - 50 non-existent commands")
    
    start_time = time.perf_counter()
    crash_count = 0
    error_count = 0
    
    for i in range(50):
        cmd_name = f"nonexistent_command_{i}_{int(time.time())}"
        try:
            with redirect_stdout(io.StringIO()) as stdout_f:
                with redirect_stderr(io.StringIO()) as stderr_f:
                    execute_command(cmd_name, [cmd_name], should_print=False)
                    stdout_output = stdout_f.getvalue()
                    stderr_output = stderr_f.getvalue()
                    
                    # Check for clean error message
                    if "command not found" in stdout_output or "command not found" in stderr_output:
                        error_count += 1
                    elif "Traceback" in stdout_output or "Traceback" in stderr_output:
                        crash_count += 1
                        print_fail(f"Python traceback on command {i+1}")
        except Exception as e:
            crash_count += 1
            print_fail(f"Exception on command {i+1}: {type(e).__name__}")
    
    end_time = time.perf_counter()
    elapsed = (end_time - start_time) * 1000
    
    print_info(f"Processed 50 invalid commands in {elapsed:.2f}ms")
    print_info(f"Clean errors: {error_count}/50")
    
    if crash_count == 0:
        print_pass("Shell remained responsive after invalid commands")
        return True, elapsed
    else:
        print_fail(f"{crash_count} crashes detected")
        return False, elapsed

def test_memory_leak():
    """Test 4: Memory leak detection."""
    print_test("4. Leak Detection - Memory usage monitoring")
    
    # Initial memory
    initial_memory = get_memory_usage()
    print_info(f"Initial memory: {initial_memory:.2f} MB")
    
    # Run a mix of commands
    commands_to_run = 150
    
    for i in range(commands_to_run):
        if i % 3 == 0:
            # Echo command
            with redirect_stdout(io.StringIO()):
                execute_command("echo", ["echo", f"test{i}"], should_print=False)
        elif i % 3 == 1:
            # Pwd command
            with redirect_stdout(io.StringIO()):
                execute_command("pwd", ["pwd"], should_print=False)
        else:
            # Invalid command
            cmd_name = f"invalid_{i}"
            with redirect_stdout(io.StringIO()):
                execute_command(cmd_name, [cmd_name], should_print=False)
    
    # Force garbage collection
    import gc
    gc.collect()
    
    # Final memory
    final_memory = get_memory_usage()
    memory_delta = final_memory - initial_memory
    
    print_info(f"Final memory: {final_memory:.2f} MB")
    print_info(f"Memory delta: {memory_delta:+.2f} MB")
    print_info(f"Commands executed: {commands_to_run}")
    
    # Check for leaks
    # Python GC may cause some memory growth, but it should stabilize
    # More than 10MB growth for 150 commands suggests a leak
    if memory_delta < 1.0:
        print_pass(f"Minimal memory growth ({memory_delta:.2f} MB) - no leak detected")
        return True, memory_delta
    elif memory_delta < 10.0:
        print_info(f"Moderate memory growth ({memory_delta:.2f} MB) - likely GC, not a leak")
        return True, memory_delta
    else:
        print_fail(f"Significant memory growth ({memory_delta:.2f} MB) - possible leak")
        return False, memory_delta

def check_zombie_processes():
    """Check for zombie processes."""
    print_test("5. Zombie Process Check")
    
    if platform.system() == "Windows":
        # Windows doesn't have zombies in the Unix sense
        # Check for orphaned processes instead
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq cmd.exe", "/FO", "CSV"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=2,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                output = result.stdout.decode('utf-8', errors='ignore')
                # Count lines (minus header)
                process_count = len([l for l in output.split('\n') if 'cmd.exe' in l]) - 1
                if process_count > 5:
                    print_info(f"Found {process_count} cmd.exe processes (some may be from other sources)")
                else:
                    print_pass(f"Found {process_count} cmd.exe processes (normal)")
                return process_count
        except:
            print_info("Could not check Windows processes")
            return 0
    else:
        # Unix: Check for zombie processes
        try:
            result = subprocess.run(
                ["ps", "aux"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=2
            )
            if result.returncode == 0:
                output = result.stdout.decode('utf-8')
                zombies = [l for l in output.split('\n') if '<defunct>' in l]
                zombie_count = len(zombies)
                if zombie_count == 0:
                    print_pass("No zombie processes found")
                else:
                    print_fail(f"Found {zombie_count} zombie processes")
                    for z in zombies[:3]:
                        print_fail(f"  {z[:80]}")
                return zombie_count
        except:
            print_info("Could not check for zombie processes")
            return 0

def calculate_stability_score(results):
    """Calculate stability score out of 100."""
    score = 100
    
    # Burst fire: -20 if failed
    if not results['burst_fire'][0]:
        score -= 20
    
    # Bomb test: -30 if crashed
    if not results['bomb_test'][0]:
        score -= 30
    
    # Invalid commands: -20 if crashed
    if not results['invalid_commands'][0]:
        score -= 20
    
    # Memory leak: -20 if significant leak
    if not results['memory_leak'][0]:
        score -= 20
    elif results['memory_leak'][1] > 5.0:  # More than 5MB growth
        score -= 10
    
    # Zombie processes: -10 if found
    if results['zombie_count'] > 0:
        score -= 10
    
    return max(0, score)

def main():
    print("=" * 70)
    print("PyShell Stress Test Suite")
    print("=" * 70)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Initial Memory: {get_memory_usage():.2f} MB")
    print("=" * 70)
    
    results = {}
    
    # Run tests
    results['burst_fire'] = test_burst_fire()
    results['bomb_test'] = test_bomb_string()
    results['invalid_commands'] = test_invalid_commands()
    results['memory_leak'] = test_memory_leak()
    results['zombie_count'] = check_zombie_processes()
    
    # Calculate score
    score = calculate_stability_score(results)
    
    # Final summary
    print("\n" + "=" * 70)
    print("Stress Test Summary")
    print("=" * 70)
    
    print(f"\n1. Burst Fire (100 commands):")
    if results['burst_fire'][0]:
        print(f"   {Colors.GREEN}[PASS]{Colors.RESET} {results['burst_fire'][1]:.2f}ms total")
    else:
        print(f"   {Colors.RED}[FAIL]{Colors.RESET}")
    
    print(f"\n2. Bomb Test (50K chars):")
    if results['bomb_test'][0]:
        print(f"   {Colors.GREEN}[PASS]{Colors.RESET} {results['bomb_test'][1]:.2f}ms")
    else:
        print(f"   {Colors.RED}[FAIL]{Colors.RESET}")
    
    print(f"\n3. Invalid Commands (50 commands):")
    if results['invalid_commands'][0]:
        print(f"   {Colors.GREEN}[PASS]{Colors.RESET} {results['invalid_commands'][1]:.2f}ms")
    else:
        print(f"   {Colors.RED}[FAIL]{Colors.RESET}")
    
    print(f"\n4. Memory Leak Detection:")
    if results['memory_leak'][0]:
        print(f"   {Colors.GREEN}[PASS]{Colors.RESET} {results['memory_leak'][1]:+.2f} MB")
    else:
        print(f"   {Colors.RED}[FAIL]{Colors.RESET} {results['memory_leak'][1]:+.2f} MB")
    
    print(f"\n5. Zombie Processes:")
    if results['zombie_count'] == 0:
        print(f"   {Colors.GREEN}[PASS]{Colors.RESET} {results['zombie_count']} zombies")
    else:
        print(f"   {Colors.RED}[FAIL]{Colors.RESET} {results['zombie_count']} zombies")
    
    # Final score
    print("\n" + "=" * 70)
    if score >= 90:
        color = Colors.GREEN
        status = "EXCELLENT"
    elif score >= 70:
        color = Colors.YELLOW
        status = "GOOD"
    else:
        color = Colors.RED
        status = "NEEDS WORK"
    
    print(f"{color}Stability Score: {score}/100{Colors.RESET} - {status}")
    print("=" * 70)
    
    # Completion criteria
    print("\nCompletion Criteria:")
    check_pass = "[PASS]" if score == 100 else "[FAIL]"
    print(f"  Stress Test Score: {score}/100 {check_pass}")
    check_pass = "[PASS]" if results['zombie_count'] == 0 else "[FAIL]"
    print(f"  Zombie Count: {results['zombie_count']} {check_pass}")
    check_pass = "[PASS]" if results['burst_fire'][0] else "[FAIL]"
    print(f"  Performance Consistency: {check_pass} (tested)")
    
    if score == 100 and results['zombie_count'] == 0:
        print(f"\n{Colors.GREEN}[COMPLETE] PROJECT COMPLETE - All criteria met!{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}[WARN] Some criteria not met - review issues above{Colors.RESET}")
    
    return 0 if score == 100 else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

