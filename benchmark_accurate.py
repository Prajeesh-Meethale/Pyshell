#!/usr/bin/env python3
"""Accurate benchmark for external command execution"""

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
from main import find_executable

def benchmark_direct_subprocess(cmd, full_path, args=None, iterations=100):
    """Benchmark direct subprocess.Popen (what PyShell should use)."""
    if args is None:
        args = []
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        proc = subprocess.Popen(
            [cmd] + args,
            executable=full_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        proc.communicate()
        times.append((time.perf_counter() - start) * 1000)
    return times

def benchmark_subprocess_run(cmd, full_path, args=None, iterations=100):
    """Benchmark subprocess.run (alternative)."""
    if args is None:
        args = []
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        subprocess.run(
            [cmd] + args,
            executable=full_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        times.append((time.perf_counter() - start) * 1000)
    return times

def benchmark_native_shell(cmd, shell_cmd, iterations=100):
    """Benchmark native shell."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        subprocess.run(shell_cmd, 
                     stdout=subprocess.DEVNULL, 
                     stderr=subprocess.DEVNULL,
                     timeout=0.5,
                     creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0)
        times.append((time.perf_counter() - start) * 1000)
    return times

def main():
    print("=" * 70)
    print("Accurate External Command Execution Benchmark")
    print("=" * 70)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}\n")
    
    # Determine test command - use a command that definitely exists
    test_args = []
    if platform.system() == "Windows":
        # Use cmd /c echo which always exists
        test_cmd = "cmd"
        full_path = r"C:\Windows\System32\cmd.exe"  # Direct path
        test_args = ["/c", "echo", "test"]
        native_cmd = ["cmd", "/c", "echo", "test"]
        native_name = "CMD"
    else:
        test_cmd = "whoami"
        full_path = find_executable(test_cmd)
        if not full_path:
            test_cmd = "echo"
            full_path = find_executable(test_cmd)
        if not full_path:
            print("Error: No suitable test command found")
            return 1
        native_cmd = [test_cmd]
        native_name = "Bash"
    
    iterations = 100
    
    print(f"Testing command: {test_cmd} {' '.join(test_args) if test_args else ''}")
    print(f"Full path: {full_path}")
    print(f"Iterations: {iterations}\n")
    
    # Benchmark direct Popen (current PyShell method)
    print("1. subprocess.Popen + communicate() (current PyShell method):")
    popen_times = benchmark_direct_subprocess(test_cmd, full_path, test_args, iterations)
    popen_mean = statistics.mean(popen_times)
    print(f"   Mean: {popen_mean:.3f}ms")
    
    # Benchmark subprocess.run (alternative)
    print("\n2. subprocess.run() (alternative):")
    run_times = benchmark_subprocess_run(test_cmd, full_path, test_args, iterations)
    run_mean = statistics.mean(run_times)
    print(f"   Mean: {run_mean:.3f}ms")
    
    # Benchmark native shell
    print(f"\n3. {native_name} (native shell):")
    native_times = benchmark_native_shell(test_cmd, native_cmd, iterations)
    native_mean = statistics.mean(native_times)
    print(f"   Mean: {native_mean:.3f}ms")
    
    # Comparison
    print("\n" + "=" * 70)
    print("Comparison")
    print("=" * 70)
    print(f"subprocess.Popen: {popen_mean:.3f}ms")
    print(f"subprocess.run:  {run_mean:.3f}ms")
    print(f"{native_name}:         {native_mean:.3f}ms")
    
    diff_popen = popen_mean - native_mean
    diff_run = run_mean - native_mean
    
    print(f"\nPopen vs {native_name}: {diff_popen:+.3f}ms ({diff_popen/native_mean*100:+.1f}%)")
    print(f"run vs {native_name}:   {diff_run:+.3f}ms ({diff_run/native_mean*100:+.1f}%)")
    
    if popen_mean > native_mean * 1.2:
        print(f"\n[WARN] Popen is {diff_popen/native_mean*100:.1f}% slower than {native_name}")
        print("  Consider optimizations:")
        print("  - Use subprocess.run() for simpler cases")
        print("  - Consider os.execv on Unix (faster but less flexible)")
    elif popen_mean < native_mean * 0.9:
        print(f"\n[OK] Popen is faster than {native_name}")
    else:
        print(f"\n[OK] Performance is comparable")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()

