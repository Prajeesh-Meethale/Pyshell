import sys
import os
import subprocess
import shlex
import readline
import glob
import signal
import platform


def find_executable(command):
    for path in os.environ.get('PATH', '').split(os.pathsep):
        full_path = os.path.join(path, command)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None


def get_all_executables():
    """Get all executable files from PATH - using glob like their example."""
    matches = []
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    
    for dir_path in path_dirs:
        if not dir_path:
            continue
        try:
            for file_path in glob.glob(os.path.join(dir_path, "*")):
                if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                    cmd_name = os.path.basename(file_path)
                    if cmd_name not in matches:
                        matches.append(cmd_name)
        except Exception:
            pass
    
    return matches


def parse_redirection(cmd_line):
    """Parse redirection from command line."""
    redirect_file = None
    redirect_stderr = False
    redirect_append = False
    
    def is_outside_quotes(pos, text):
        before = text[:pos]
        in_single = False
        in_double = False
        j = 0
        while j < len(before):
            if before[j] == '\\' and j + 1 < len(before):
                j += 2
                continue
            if before[j] == "'" and not in_double:
                in_single = not in_single
            elif before[j] == '"' and not in_single:
                in_double = not in_double
            j += 1
        return not in_single and not in_double
    
    for i in range(len(cmd_line) - 2, -1, -1):
        if cmd_line[i:i+3] == '2>>' and is_outside_quotes(i, cmd_line):
            return cmd_line[:i].strip(), cmd_line[i+3:].strip(), True, True
    
    for i in range(len(cmd_line) - 1, -1, -1):
        if cmd_line[i:i+2] == '2>' and is_outside_quotes(i, cmd_line):
            return cmd_line[:i].strip(), cmd_line[i+2:].strip(), True, False
    
    for i in range(len(cmd_line) - 2, -1, -1):
        if cmd_line[i:i+3] == '1>>' and is_outside_quotes(i, cmd_line):
            return cmd_line[:i].strip(), cmd_line[i+3:].strip(), False, True
    
    for i in range(len(cmd_line) - 1, -1, -1):
        if cmd_line[i:i+2] == '1>' and is_outside_quotes(i, cmd_line):
            return cmd_line[:i].strip(), cmd_line[i+2:].strip(), False, False
    
    for i in range(len(cmd_line) - 2, -1, -1):
        if cmd_line[i:i+2] == '>>' and is_outside_quotes(i, cmd_line):
            return cmd_line[:i].strip(), cmd_line[i+2:].strip(), False, True
    
    for i in range(len(cmd_line) - 1, -1, -1):
        if cmd_line[i] == '>' and is_outside_quotes(i, cmd_line):
            if i + 1 < len(cmd_line) and cmd_line[i+1] == '>':
                continue
            return cmd_line[:i].strip(), cmd_line[i+1:].strip(), False, False
    
    return cmd_line, None, False, False


# Global history list
command_history = []

# Global exit status variable ($status)
shell_status = 0  # Last command exit code


def execute_command(command, args, redirect_file=None, redirect_stderr=False, redirect_append=False, stdin_data=None, should_print=True, process_tracker=None):
    """Execute a single command.
    
    Args:
        process_tracker: List to track processes for signal handling (optional)
    
    Returns:
        tuple: (output_bytes, exit_code)
    """
    global shell_status
    
    if command == "exit":
        exit_code = 0 if not args or len(args) < 2 else int(args[1])
        shell_status = exit_code
        sys.exit(exit_code)
    
    elif command == "echo":
        output = " ".join(args[1:]) + '\n'
        
        if redirect_file and not redirect_stderr:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                f.write(output)
            shell_status = 0
            return b"", 0
        
        if redirect_stderr and redirect_file:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                pass
        
        sys.stdout.write(output)
        sys.stdout.flush()
        shell_status = 0
        return b"", 0
    
    elif command == "type":
        if len(args) < 2:
            shell_status = 0
            return b"", 0
        target = args[1]
        if target in ["exit", "echo", "type", "pwd", "cd", "history"]:
            output = f"{target} is a shell builtin\n"
            exit_code = 0
        else:
            full_path = find_executable(target)
            if full_path:
                output = f"{full_path}\n"
                exit_code = 0
            else:
                output = f"{target}: not found\n"
                exit_code = 1
        
        if redirect_file and not redirect_stderr:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                f.write(output)
            shell_status = exit_code
            return b"", exit_code
        
        if redirect_stderr and redirect_file:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                pass
        
        sys.stdout.write(output)
        sys.stdout.flush()
        shell_status = exit_code
        return b"", exit_code
    
    elif command == "pwd":
        output = os.getcwd() + '\n'
        
        if redirect_file and not redirect_stderr:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                f.write(output)
            shell_status = 0
            return b"", 0
        
        if redirect_stderr and redirect_file:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                pass
        
        sys.stdout.write(output)
        sys.stdout.flush()
        shell_status = 0
        return b"", 0
    
    elif command == "cd":
        exit_code = 0
        if len(args) > 1:
            path = os.path.expanduser(args[1])
            try:
                os.chdir(path)
            except OSError:
                print(f"cd: {args[1]}: No such file or directory")
                exit_code = 1
        else:
            home = os.path.expanduser("~")
            os.chdir(home)
        shell_status = exit_code
        return b"", exit_code
    
    elif command == "history":
        # Check for -r flag (read history from file)
        if len(args) > 1 and args[1] == "-r":
            if len(args) > 2:
                file_path = args[2]
                try:
                    with open(file_path, 'r') as f:
                        for line in f:
                            line = line.rstrip('\n')
                            # Skip empty lines
                            if line.strip():
                                command_history.append(line)
                except FileNotFoundError:
                    print(f"history: {file_path}: No such file or directory")
                except Exception as e:
                    print(f"history: {file_path}: {e}")
            return b""
        
        # Get limit if provided
        limit = None
        if len(args) > 1:
            try:
                limit = int(args[1])
            except ValueError:
                pass
        
        # Determine which entries to show
        if limit is not None:
            # Show last n entries
            start_idx = max(0, len(command_history) - limit)
            entries_to_show = command_history[start_idx:]
            start_num = start_idx + 1
        else:
            # Show all entries
            entries_to_show = command_history
            start_num = 1
        
        # Print history
        output = ""
        for i, cmd in enumerate(entries_to_show, start=start_num):
            output += f"    {i}  {cmd}\n"
        
        if redirect_file and not redirect_stderr:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                f.write(output)
            return b""
        
        sys.stdout.write(output)
        sys.stdout.flush()
        shell_status = 0
        return b"", 0
    
    else:
        full_path = find_executable(command)
        if not full_path:
            print(f"{command}: command not found")
            shell_status = 127  # Standard "command not found" exit code
            return b"", 127
        
        cmd_str = ' '.join([command] + args[1:])
        
        if redirect_file:
            if redirect_stderr:
                op = '2>>' if redirect_append else '2>'
            else:
                op = '>>' if redirect_append else '>'
            cmd_str = f"{cmd_str} {op} {redirect_file}"
            exit_code = subprocess.call(cmd_str, shell=True)
            shell_status = exit_code
            return b"", exit_code
        else:
            # Optimize: Use subprocess.run() for simple cases (faster)
            # Use Popen only when process tracking is needed for signal handling
            if process_tracker is None:
                # Simple case: no process tracking needed, use faster subprocess.run()
                result = subprocess.run(
                    [command] + args[1:],
                    executable=full_path,
                    stdout=subprocess.PIPE,
                    stderr=None
                )
                exit_code = result.returncode
                output = result.stdout if result.stdout else b""
                if output and should_print:
                    sys.stdout.buffer.write(output)
                    sys.stdout.buffer.flush()
                shell_status = exit_code
                return output, exit_code
            else:
                # Need process tracking for signal handling - use Popen
                proc = subprocess.Popen(
                    [command] + args[1:],
                    executable=full_path,
                    stdout=subprocess.PIPE,
                    stderr=None
                )
                # Track process for signal handling
                process_tracker.append(proc)
                try:
                    output, _ = proc.communicate()
                    exit_code = proc.returncode
                    output = output if output else b""
                    if output and should_print:
                        sys.stdout.buffer.write(output)
                        sys.stdout.buffer.flush()
                    shell_status = exit_code
                    return output, exit_code
                except KeyboardInterrupt:
                    # Handle Ctrl+C
                    proc.terminate()
                    try:
                        proc.wait(timeout=0.1)
                    except:
                        pass
                    shell_status = 130  # Standard exit code for SIGINT
                    raise
                finally:
                    if proc in process_tracker:
                        process_tracker.remove(proc)


# Global variables for tab completion
last_tab_text = ""
last_tab_matches = []
last_tab_count = 0


def get_executable_matches(text):
    """Find all executables in PATH that match the given prefix."""
    matches = []
    
    # First, check builtins
    builtins = ["exit", "echo", "type", "pwd", "cd", "history"]
    for cmd in builtins:
        if cmd.startswith(text):
            matches.append(cmd)
    
    # Then check executables in PATH
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    for dir_path in path_dirs:
        if not dir_path:
            continue
        
        try:
            for file_path in glob.glob(os.path.join(dir_path, "*")):
                if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                    cmd_name = os.path.basename(file_path)
                    if cmd_name.startswith(text) and cmd_name not in matches:
                        matches.append(cmd_name)
        except Exception:
            pass
    
    return sorted(matches)


def get_longest_common_prefix(strings):
    """Get the longest common prefix of a list of strings."""
    if not strings:
        return ""
    if len(strings) == 1:
        return strings[0]
        
    prefix = strings[0]
    for string in strings[1:]:
        # Find the length of common prefix
        length = 0
        for i, (c1, c2) in enumerate(zip(prefix, string)):
            if c1 != c2:
                break
            length = i + 1
        
        # Update prefix to common part
        prefix = prefix[:length]
        if not prefix:
            break
            
    return prefix


def complete(text, state):
    """Custom tab completion function for readline."""
    global last_tab_text, last_tab_matches, last_tab_count
    
    # Split the line to get the current command/args
    line = readline.get_line_buffer()
    
    # First word (command) completion
    if not line.strip() or " " not in line.lstrip():
        # New completion attempt or different text
        if text != last_tab_text:
            last_tab_text = text
            last_tab_matches = get_executable_matches(text)
            last_tab_count = 0
        
        # No matches
        if not last_tab_matches:
            if state == 0:
                sys.stdout.write('\a')  # Ring bell
                sys.stdout.flush()
            return None
            
        # Single match - add space
        if len(last_tab_matches) == 1:
            if state == 0:
                return last_tab_matches[0] + " "
            return None
            
        # Multiple matches
        # Try to complete to longest common prefix
        lcp = get_longest_common_prefix(last_tab_matches)
        if lcp and len(lcp) > len(text):
            # There's a longer common prefix - complete to it
            if state == 0:
                return lcp
            return None
        
        # No progress possible with LCP
        if last_tab_count == 0:
            # First tab press - increment counter, ring bell, return the text
            last_tab_count += 1
            if state == 0:
                sys.stdout.write('\a')  # Ring bell
                sys.stdout.flush()
                return text
            return None
        else:
            # Second tab press - display all matches
            if state == 0:
                print()  # New line
                print("  ".join(last_tab_matches))
                sys.stdout.write(f"$ {text}")
                sys.stdout.flush()
                return text
            return None
    
    # Multiple word completion (not implemented yet)
    if state == 0:
        return text
    return None


def expand_variables(text):
    """Expand shell variables like $status."""
    global shell_status
    if '$status' in text:
        text = text.replace('$status', str(shell_status))
    return text

def parse_if_then(line):
    """Parse if-then blocks: if [condition] then [command]"""
    line = line.strip()
    if not line.startswith('if '):
        return None
    
    # Find 'then'
    then_pos = line.find(' then ')
    if then_pos == -1:
        return None
    
    condition = line[3:then_pos].strip()  # Skip 'if '
    command = line[then_pos + 6:].strip()  # Skip ' then '
    
    return {'type': 'if', 'condition': condition, 'command': command}

def evaluate_condition(condition):
    """Evaluate a condition like '$status != 0' or '$status == 0'."""
    global shell_status
    condition = condition.strip()
    
    # Replace $status with actual value
    condition = condition.replace('$status', str(shell_status))
    
    # Parse comparison operators
    operators = ['!=', '==', '>=', '<=', '>', '<']
    for op in operators:
        if op in condition:
            parts = condition.split(op, 1)
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()
                try:
                    left_val = int(left)
                    right_val = int(right)
                    if op == '==':
                        return left_val == right_val
                    elif op == '!=':
                        return left_val != right_val
                    elif op == '>=':
                        return left_val >= right_val
                    elif op == '<=':
                        return left_val <= right_val
                    elif op == '>':
                        return left_val > right_val
                    elif op == '<':
                        return left_val < right_val
                except ValueError:
                    # String comparison
                    if op == '==':
                        return left == right
                    elif op == '!=':
                        return left != right
    return False

def parse_logical_chain(line):
    """Parse logical chaining: cmd1 && cmd2 || cmd3"""
    def is_outside_quotes(pos, text):
        before = text[:pos]
        in_single = False
        in_double = False
        i = 0
        while i < len(before):
            if before[i] == '\\' and i + 1 < len(before):
                i += 2
                continue
            if before[i] == "'" and not in_double:
                in_single = not in_single
            elif before[i] == '"' and not in_single:
                in_double = not in_double
            i += 1
        return not in_single and not in_double
    
    parts = []
    current = ""
    operators = []
    
    i = 0
    while i < len(line):
        if i < len(line) - 1 and line[i:i+2] == '&&' and is_outside_quotes(i, line):
            parts.append(current.strip())
            operators.append('&&')
            current = ""
            i += 2
        elif i < len(line) - 1 and line[i:i+2] == '||' and is_outside_quotes(i, line):
            parts.append(current.strip())
            operators.append('||')
            current = ""
            i += 2
        else:
            current += line[i]
            i += 1
    
    if current.strip():
        parts.append(current.strip())
    
    if len(parts) > 1:
        return {'type': 'chain', 'parts': parts, 'operators': operators}
    return None

def main():
    global last_tab_count, last_tab_text, command_history, shell_status
    
    # Track running child processes for signal handling
    current_processes = []
    
    def signal_handler(signum, frame):
        """Handle SIGINT (Ctrl+C) - kill child processes but keep shell running."""
        if current_processes:
            for proc in current_processes:
                try:
                    if isinstance(proc, int):
                        # Process ID from fork
                        os.kill(proc, signal.SIGTERM)
                    else:
                        # subprocess.Popen object
                        proc.terminate()
                except (ProcessLookupError, OSError):
                    pass
            # Wait for processes to terminate
            for proc in current_processes:
                try:
                    if isinstance(proc, int):
                        os.waitpid(proc, 0)
                    else:
                        proc.wait(timeout=0.1)
                except:
                    pass
            current_processes.clear()
        # Print newline and prompt
        print()  # New line after ^C
        sys.stdout.flush()
    
    # Register signal handler (Unix only)
    if platform.system() != "Windows":
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    # Setup readline
    try:
        readline.parse_and_bind("tab: complete")
        readline.set_completer(complete)
        readline.set_completer_delims(" \t\n")
    except:
        pass  # readline not available on Windows
    
    while True:
        # Reset for new line
        last_tab_count = 0
        last_tab_text = ""
        
        try:
            # Use input() with prompt so readline knows about it
            line = input("$ ")
        except EOFError:
            break
        
        if not line.strip():
            continue
        
        # Add to history
        command_history.append(line)
        
        # Expand variables
        line = expand_variables(line)
        
        # Check for if-then blocks
        if_block = parse_if_then(line)
        if if_block:
            condition_result = evaluate_condition(if_block['condition'])
            if condition_result:
                # Execute the command
                line = if_block['command']
            else:
                # Condition false, skip command
                continue
        
        # Check for logical chaining (&& and ||)
        chain = parse_logical_chain(line)
        if chain:
            # Execute commands in chain based on operators
            last_exit_code = 0
            for i, cmd_part in enumerate(chain['parts']):
                # Parse and execute this part
                cmd_part, redirect_file, redirect_stderr, redirect_append = parse_redirection(cmd_part)
                args = shlex.split(cmd_part)
                if args:
                    _, exit_code = execute_command(args[0], args, redirect_file, redirect_stderr, redirect_append, process_tracker=current_processes)
                    
                    # Check if we should continue based on operator
                    if i < len(chain['operators']):
                        op = chain['operators'][i]
                        if op == '&&' and exit_code != 0:
                            # && requires success, stop on failure
                            break
                        elif op == '||' and exit_code == 0:
                            # || requires failure, stop on success
                            break
                    last_exit_code = exit_code
            continue
        
        # Parse pipes FIRST
        def is_outside_quotes(pos, text):
            before = text[:pos]
            in_single = False
            in_double = False
            i = 0
            while i < len(before):
                if before[i] == '\\' and i + 1 < len(before):
                    i += 2
                    continue
                if before[i] == "'" and not in_double:
                    in_single = not in_single
                elif before[i] == '"' and not in_single:
                    in_double = not in_double
                i += 1
            return not in_single and not in_double
        
        # Find pipe positions
        pipe_parts = []
        current = ""
        for i, char in enumerate(line):
            if char == '|' and is_outside_quotes(i, line):
                pipe_parts.append(current.strip())
                current = ""
            else:
                current += char
        pipe_parts.append(current.strip())
        
        if len(pipe_parts) == 1:
            # No pipes
            cmd_part, redirect_file, redirect_stderr, redirect_append = parse_redirection(pipe_parts[0])
            args = shlex.split(cmd_part)
            if args:
                # Execute command with process tracking for signal handling
                # Note: exit code is stored in shell_status global variable
                execute_command(args[0], args, redirect_file, redirect_stderr, redirect_append, process_tracker=current_processes)
        else:
            # Has pipes
            processes = []
            prev_read_fd = None
            
            for idx, pipe_cmd in enumerate(pipe_parts):
                is_last = (idx == len(pipe_parts) - 1)
                cmd_part, redirect_file, redirect_stderr, redirect_append = parse_redirection(pipe_cmd)
                args = shlex.split(cmd_part)
                
                if not args:
                    continue
                
                command_name = args[0]
                
                builtins = ["exit", "echo", "type", "pwd", "cd", "history"]
                if command_name in builtins:
                    if not is_last:
                        if platform.system() == "Windows":
                            # Windows doesn't support fork - use subprocess instead
                            # Handle frozen executables (PyInstaller)
                            if getattr(sys, 'frozen', False):
                                # Running as compiled executable
                                base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
                            else:
                                # Running as script
                                base_path = os.path.dirname(os.path.dirname(__file__))
                            
                            read_fd, write_fd = os.pipe()
                            proc = subprocess.Popen(
                                [sys.executable, "-c", 
                                 f"import sys; sys.path.insert(0, r'{base_path}'); "
                                 f"from app.main import execute_command; "
                                 f"import os; os.dup2({read_fd}, 0); os.dup2({write_fd}, 1); "
                                 f"execute_command('{command_name}', {args})"],
                                stdin=prev_read_fd if prev_read_fd else None,
                                stdout=write_fd,
                                stderr=subprocess.DEVNULL
                            )
                            processes.append(proc)
                            os.close(write_fd)
                            if prev_read_fd is not None:
                                os.close(prev_read_fd)
                            prev_read_fd = read_fd
                            continue
                        else:
                            # Unix fork
                            read_fd, write_fd = os.pipe()
                            pid = os.fork()
                            if pid == 0:
                                if prev_read_fd is not None:
                                    os.dup2(prev_read_fd, 0)
                                    os.close(prev_read_fd)
                                os.dup2(write_fd, 1)
                                os.close(write_fd)
                                os.close(read_fd)
                                execute_command(command_name, args, redirect_file, redirect_stderr, redirect_append)
                                sys.exit(0)
                            else:
                                processes.append(pid)
                            os.close(write_fd)
                            if prev_read_fd is not None:
                                os.close(prev_read_fd)
                            prev_read_fd = read_fd
                    else:
                        if prev_read_fd is not None:
                            try:
                                os.read(prev_read_fd, 1000000)
                            except:
                                pass
                            os.close(prev_read_fd)
                        execute_command(command_name, args, redirect_file, redirect_stderr, redirect_append)
                    continue
                
                full_path = find_executable(command_name)
                if not full_path:
                    print(f"{command_name}: command not found")
                    break
                
                if not is_last:
                    read_fd, write_fd = os.pipe()
                    proc = subprocess.Popen(
                        [command_name] + args[1:],
                        executable=full_path,
                        stdin=prev_read_fd,
                        stdout=write_fd,
                        stderr=subprocess.DEVNULL
                    )
                    processes.append(proc)
                    current_processes.append(proc)  # Track for signal handling
                    os.close(write_fd)
                    if prev_read_fd is not None:
                        os.close(prev_read_fd)
                    prev_read_fd = read_fd
                else:
                    if redirect_file:
                        if redirect_stderr:
                            op = '2>>' if redirect_append else '2>'
                        else:
                            op = '>>' if redirect_append else '>'
                        cmd_str = f"{command_name} {' '.join(args[1:])} {op} {redirect_file}"
                        proc = subprocess.Popen(cmd_str, shell=True, stdin=prev_read_fd, stdout=None, stderr=None)
                    else:
                        proc = subprocess.Popen(
                            [command_name] + args[1:],
                            executable=full_path,
                            stdin=prev_read_fd,
                            stdout=None,
                            stderr=subprocess.DEVNULL
                        )
                    processes.append(proc)
                    current_processes.append(proc)  # Track for signal handling
                    if prev_read_fd is not None:
                        os.close(prev_read_fd)
            
            # Wait for all processes and clean up
            for proc in processes:
                try:
                    if isinstance(proc, int):
                        # Process ID from fork
                        os.waitpid(proc, 0)
                    else:
                        # subprocess.Popen object
                        proc.wait()
                    # Remove from tracking after successful wait
                    if proc in current_processes:
                        current_processes.remove(proc)
                except (ProcessLookupError, OSError, KeyboardInterrupt):
                    # Process already terminated or interrupted
                    try:
                        if isinstance(proc, int):
                            try:
                                if platform.system() != "Windows":
                                    os.kill(proc, signal.SIGTERM)
                                os.waitpid(proc, 0)
                            except:
                                pass
                        else:
                            proc.terminate()
                            proc.wait(timeout=0.1)
                        if proc in current_processes:
                            current_processes.remove(proc)
                    except:
                        if proc in current_processes:
                            current_processes.remove(proc)


if __name__ == "__main__":
    main()
 