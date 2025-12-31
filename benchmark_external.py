#!/usr/bin/env python3
"""
Benchmark external command execution (process fork overhead)
Compares PyShell vs Bash/CMD for whoami/hostname
"""

import time
import subprocess
import sys
import os
import platform
import statistics

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
from main import execute_command, find_executable
from contextlib import redirect_stdout
import io

def benchmark_pyshell_external(cmd, iterations=100):
    """Benchmark PyShell external command execution."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        try:
            with redirect_stdout(io.StringIO()):
                execute_command(cmd, [cmd], should_print=False)
        except:
            pass
        times.append((time.perf_counter() - start) * 1000)
    return times

def benchmark_native_shell(cmd, shell_cmd, iterations=100):
    """Benchmark native shell external command execution."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        try:
            subprocess.run(shell_cmd, 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL,
                         timeout=0.5,
                         creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0)
        except:
            pass
        times.append((time.perf_counter() - start) * 1000)
    return times

def analyze_subprocess_usage():
    """Analyze how subprocess is currently being used."""
    print("\n" + "=" * 70)
    print("Analyzing Current subprocess Usage")
    print("=" * 70)
    
    # Read the main.py file to see subprocess usage
    with open('app/main.py', 'r') as f:
        content = f.read()
        subprocess_count = content.count('subprocess.')
        run_count = content.count('subprocess.run')
        popen_count = content.count('subprocess.Popen')
        call_count = content.count('subprocess.call')
        
        print(f"subprocess.run() calls: {run_count}")
        print(f"subprocess.Popen() calls: {popen_count}")
        print(f"subprocess.call() calls: {call_count}")
        print(f"Total subprocess calls: {subprocess_count}")
        
        # Check for potential optimizations
        if 'subprocess.run' in content:
            print("\n[WARN] Found subprocess.run() - this may be slower than Popen")
            print("  subprocess.run() waits for completion and collects output")
            print("  For external commands, Popen + communicate() might be more efficient")
        
        if 'subprocess.call' in content:
            print("\n[WARN] Found subprocess.call() - this uses shell=True")
            print("  shell=True adds shell interpretation overhead")
            print("  Direct execution is faster")

def main():
    print("=" * 70)
    print("External Command Execution Benchmark")
    print("=" * 70)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}\n")
    
    # Determine test command
    if platform.system() == "Windows":
        test_cmd = "whoami"
        native_cmd = ["cmd", "/c", "whoami"]
        native_name = "CMD"
    else:
        test_cmd = "whoami"
        native_cmd = ["whoami"]  # Direct exec
        native_name = "Bash"
    
    # Check if command exists
    if not find_executable(test_cmd):
        print(f"[WARN] {test_cmd} not found in PATH")
        if platform.system() == "Windows":
            test_cmd = "hostname"
            native_cmd = ["cmd", "/c", "hostname"]
        else:
            test_cmd = "hostname"
            native_cmd = ["hostname"]
        print(f"  Using {test_cmd} instead")
    
    iterations = 100
    
    print(f"\nTesting command: {test_cmd}")
    print(f"Iterations: {iterations}")
    print(f"\nThis tests process fork/exec overhead (external command execution)\n")
    
    # Benchmark PyShell
    print("Benchmarking PyShell...")
    pyshell_times = benchmark_pyshell_external(test_cmd, iterations)
    pyshell_mean = statistics.mean(pyshell_times)
    pyshell_median = statistics.median(pyshell_times)
    pyshell_min = min(pyshell_times)
    pyshell_max = max(pyshell_times)
    
    print(f"  Mean:   {pyshell_mean:.3f}ms")
    print(f"  Median: {pyshell_median:.3f}ms")
    print(f"  Min:    {pyshell_min:.3f}ms")
    print(f"  Max:    {pyshell_max:.3f}ms")
    
    # Benchmark native shell
    print(f"\nBenchmarking {native_name}...")
    native_times = benchmark_native_shell(test_cmd, native_cmd, iterations)
    native_mean = statistics.mean(native_times)
    native_median = statistics.median(native_times)
    native_min = min(native_times)
    native_max = max(native_times)
    
    print(f"  Mean:   {native_mean:.3f}ms")
    print(f"  Median: {native_median:.3f}ms")
    print(f"  Min:    {native_min:.3f}ms")
    print(f"  Max:    {native_max:.3f}ms")
    
    # Comparison
    print("\n" + "=" * 70)
    print("Comparison")
    print("=" * 70)
    diff = pyshell_mean - native_mean
    ratio = pyshell_mean / native_mean if native_mean > 0 else 0
    percent_slower = ((pyshell_mean - native_mean) / native_mean * 100) if native_mean > 0 else 0
    
    print(f"PyShell:  {pyshell_mean:.3f}ms (mean)")
    print(f"{native_name}:     {native_mean:.3f}ms (mean)")
    print(f"\nDifference: {diff:+.3f}ms ({percent_slower:+.1f}%)")
    print(f"Speed ratio: {ratio:.2f}x")
    
    if pyshell_mean > native_mean * 1.5:
        print(f"\n[WARN] PyShell is {percent_slower:.1f}% slower - optimization recommended")
        print("  Analyzing subprocess usage for optimization opportunities...")
        analyze_subprocess_usage()
    elif pyshell_mean < native_mean * 0.9:
        print(f"\n[OK] PyShell is faster (likely due to Python optimizations)")
    else:
        print(f"\n[OK] Performance is comparable to {native_name}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()

