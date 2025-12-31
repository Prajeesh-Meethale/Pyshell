# PyShell

An interactive shell implementation in Python.

PyShell interprets shell commands, runs external programs, and provides builtin commands like cd, pwd, echo, and more. It features conditional execution logic, exit code tracking, and is packaged as a standalone Windows executable.

**See [FEATURE_COMPARISON.md](FEATURE_COMPARISON.md) for a detailed feature comparison with bash/sh.**

## Quick Feature Comparison

| Feature | bash/sh | PyShell |
|---------|---------|---------|
| Command execution | ✅ | ✅ |
| Pipes (`\|`) | ✅ | ✅ |
| Redirection (`>`, `>>`, `2>`) | ✅ | ✅ |
| Background (`&`) | ✅ | ✅ |
| Built-ins (cd, pwd, echo) | ✅ | ✅ |
| Signals (Ctrl+C) | ✅ | ✅ |
| Conditional (`if-then`, `&&`, `\|\|`) | ✅ | ✅ |
| Exit code tracking | ✅ | ✅ |
| Tab completion | ✅ | ✅ |
| Command history | ✅ | ✅ |

See [FEATURE_COMPARISON.md](FEATURE_COMPARISON.md) for full details

## Getting Started

The entry point for your `shell` implementation is in `app/main.py`.

## Running Locally

1. Ensure you have `uv` installed locally (or Python 3.14+)
2. Run `./your_program.sh` to run your program, which is implemented in `app/main.py`.
3. Or run directly: `python -m app.main`

## Conditional Execution Flow

PyShell supports explicit exit-code-based conditional execution, evaluated in-process:

### Exit Code Tracking

Every command stores its exit code in the `$status` variable:
- `0` = success
- Non-zero = failure (127 for command not found, etc.)

```bash
$ echo hello
hello
$ echo $status
0
$ nonexistent_command
nonexistent_command: command not found
$ echo $status
127
```

### If-Then Blocks

Execute commands conditionally based on exit codes:

```bash
$ nonexistent_command
nonexistent_command: command not found
$ if $status != 0 then echo "Command failed!"
Command failed!
```

**Syntax:** `if [condition] then [command]`

**Supported operators:** `==`, `!=`, `>`, `<`, `>=`, `<=`

### Logical Chaining

Chain commands with `&&` (AND) and `||` (OR) operators:

```bash
# Execute second command only if first succeeds
$ echo test && echo success
test
success

# Execute second command only if first fails
$ nonexistent_command || echo "Fallback executed"
nonexistent_command: command not found
Fallback executed

# Complex chains
$ cmd1 && cmd2 || cmd3
```

**Behavior:**
- `cmd1 && cmd2`: Execute `cmd2` only if `cmd1` succeeds (exit code 0)
- `cmd1 || cmd2`: Execute `cmd2` only if `cmd1` fails (exit code != 0)

### Performance

All conditional logic is evaluated **in-process by Python**, maintaining the same instant performance as builtin commands. No external process overhead for conditionals.

## Testing

Run the comprehensive audit suite:
```bash
python test_shell_audit.py
```

Test conditional features:
```bash
python test_conditionals.py
```

This tests:
- Functional correctness (cd, pwd, commands)
- Error handling (non-existent commands)
- Signal handling (Ctrl+C)
- Process cleanup (zombie prevention)
- Performance benchmarks
- Conditional execution (if-then, &&, ||)
- Exit code tracking

## Features

- Command parsing and execution
- Builtin commands (cd, pwd, echo, etc.)
- External program execution
- I/O redirection
- Piping between commands
- **Background processes** (`&`) - Run commands in background
- **Signal handling** (Ctrl+C) - Gracefully terminate child processes
- Environment variable handling
- Tab completion
- Command history
- **Conditional execution flow** (if-then, &&, ||)
- **Exit code tracking** ($status variable)

## Benchmarks

Performance metrics measured on Windows 11 (Python 3.14.2):

### Builtin Commands
- `echo "test"`: **0.003ms** (PyShell) vs **64.5ms** (CMD/PowerShell)
- Builtin commands run in-process with minimal overhead

### Command Parsing
- Simple command parsing: **~0.014ms**
- Complex command with redirections: **~0.028ms**
- Quoted arguments parsing: **~0.033ms**

### External Program Execution
- Process spawn overhead: **~2-5ms** (similar to native shells)
- PATH resolution: **< 1ms** (typical PATH with 10-20 directories)
- Environment variable lookup: **< 0.1ms**

### Performance Comparison Summary
| Operation | PyShell | Bash/CMD | Notes |
|-----------|---------|----------|-------|
| Builtin commands | 0.003ms | 64-100ms | In-process execution |
| External commands | ~65ms | ~65ms | Comparable overhead |
| Command parsing | 0.014ms | <0.1ms | Both very fast |

**Key Insight:** PyShell's builtin commands (echo, pwd, cd, type, history) run in-process, making them fast for interactive use and scripts that heavily use builtins.

*Note: Actual performance may vary based on system load, Python version, and hardware specifications. Run `python test_shell_audit.py` for current benchmarks.*

