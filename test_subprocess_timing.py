#!/usr/bin/env python3
"""Test actual subprocess timing"""

import time
import subprocess
import sys
import os
import platform

# Test direct subprocess.run
print("Testing direct subprocess.run:")
times = []
for _ in range(10):
    start = time.perf_counter()
    subprocess.run(['hostname'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    times.append((time.perf_counter() - start) * 1000)
print(f"  Mean: {sum(times)/len(times):.3f}ms")

# Test subprocess.Popen with communicate
print("\nTesting subprocess.Popen + communicate:")
times = []
for _ in range(10):
    start = time.perf_counter()
    proc = subprocess.Popen(['hostname'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    proc.communicate()
    times.append((time.perf_counter() - start) * 1000)
print(f"  Mean: {sum(times)/len(times):.3f}ms")

# Test with executable parameter
print("\nTesting with executable parameter:")
from app.main import find_executable
full_path = find_executable('hostname')
if full_path:
    times = []
    for _ in range(10):
        start = time.perf_counter()
        proc = subprocess.Popen(['hostname'], executable=full_path, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        proc.communicate()
        times.append((time.perf_counter() - start) * 1000)
    print(f"  Mean: {sum(times)/len(times):.3f}ms")

