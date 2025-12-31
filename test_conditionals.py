#!/usr/bin/env python3
"""Test conditional scripting features"""

import sys
import os
from contextlib import redirect_stdout
import io

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
from main import execute_command, expand_variables, parse_if_then, evaluate_condition, parse_logical_chain

def test_exit_code_tracking():
    """Test exit code tracking."""
    print("Testing exit code tracking...")
    import app.main
    
    # Test successful command
    _, exit_code = execute_command("echo", ["echo", "test"], should_print=False)
    assert exit_code == 0, f"Expected 0, got {exit_code}"
    assert app.main.shell_status == 0, f"shell_status should be 0, got {app.main.shell_status}"
    print("  [OK] Successful command returns 0")
    
    # Test failed command (non-existent)
    _, exit_code = execute_command("nonexistent123", ["nonexistent123"], should_print=False)
    assert exit_code == 127, f"Expected 127, got {exit_code}"
    assert app.main.shell_status == 127, f"shell_status should be 127, got {app.main.shell_status}"
    print("  [OK] Non-existent command returns 127")
    
    # Reset for next test
    app.main.shell_status = 0
    
    print("  [PASS] Exit code tracking works\n")

def test_variable_expansion():
    """Test $status variable expansion."""
    print("Testing variable expansion...")
    
    # Set status to 1
    import app.main
    app.main.shell_status = 1
    
    result = expand_variables("echo $status")
    assert result == "echo 1", f"Expected 'echo 1', got '{result}'"
    print("  [OK] $status expands correctly")
    
    app.main.shell_status = 0
    result = expand_variables("echo $status")
    assert result == "echo 0", f"Expected 'echo 0', got '{result}'"
    print("  [OK] $status updates correctly")
    
    print("  [PASS] Variable expansion works\n")

def test_if_then():
    """Test if-then blocks."""
    print("Testing if-then blocks...")
    
    # Test parsing
    result = parse_if_then("if $status != 0 then echo Failed")
    assert result is not None, "Failed to parse if-then"
    assert result['condition'] == "$status != 0"
    assert result['command'] == "echo Failed"
    print("  [OK] if-then parsing works")
    
    # Test condition evaluation
    import app.main
    app.main.shell_status = 1
    assert evaluate_condition("$status != 0") == True
    assert evaluate_condition("$status == 0") == False
    print("  [OK] Condition evaluation works")
    
    app.main.shell_status = 0
    assert evaluate_condition("$status == 0") == True
    assert evaluate_condition("$status != 0") == False
    print("  [OK] Condition evaluation with == works")
    
    print("  [PASS] if-then blocks work\n")

def test_logical_chaining():
    """Test && and || operators."""
    print("Testing logical chaining...")
    
    # Test parsing
    result = parse_logical_chain("echo test && echo success")
    assert result is not None, "Failed to parse logical chain"
    assert len(result['parts']) == 2
    assert result['operators'] == ['&&']
    print("  [OK] && parsing works")
    
    result = parse_logical_chain("echo test || echo fallback")
    assert result is not None
    assert result['operators'] == ['||']
    print("  [OK] || parsing works")
    
    result = parse_logical_chain("cmd1 && cmd2 || cmd3")
    assert len(result['parts']) == 3
    assert result['operators'] == ['&&', '||']
    print("  [OK] Complex chain parsing works")
    
    print("  [PASS] Logical chaining parsing works\n")

def main():
    print("=" * 70)
    print("Conditional Scripting Feature Tests")
    print("=" * 70 + "\n")
    
    try:
        test_exit_code_tracking()
        test_variable_expansion()
        test_if_then()
        test_logical_chaining()
        
        print("=" * 70)
        print("[SUCCESS] All conditional scripting tests passed!")
        print("=" * 70)
        return 0
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

