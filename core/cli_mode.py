"""
CLI mode implementation for MarkMark.
Provides a powerful command-line interface with full editing capabilities.
"""

import sys
import os
import re
import readline
import argparse
from pathlib import Path
from typing import Optional, List, Callable, Any
from dataclasses import dataclass
from enum import Enum
from io import StringIO


class CommandType(Enum):
    """Types of CLI commands."""
    EDITOR = "editor"
    FILE = "file"
    BUFFER = "buffer"
    SEARCH = "search"
    FORMAT = "format"
    EXPORT = "export"
    SYSTEM = "system"
    HELP = "help"
    CONFIG = "config"


@dataclass
class Command:
    """A CLI command definition."""
    name: str
    aliases: List[str]
    description: str
    usage: str
    handler: Callable
    type: CommandType
    requires_file: bool = False
    arguments: List[dict] = None


class CLIMode:
    """
    Command-line interface mode for MarkMark.
    
    Features:
    - Full editing capabilities from command line
    - Batch file processing
    - Quick formatting and conversion
    - Pipe support
    - Interactive REPL mode
    """
    
    def __init__(self, config=None):
        self.config = config
        self.running = False
        self.current_file: Optional[str] = None
        self.buffer: str = ""
        self.modified: bool = False
        self.output: StringIO = StringIO()
        self.history_file = self._get_history_file()
        
        # Commands
        self.commands: dict = {}
        self._init_commands()
        
        # Color support
        self.colors_enabled = self._detect_color_support()
        
        # Keybindings
        self._init_readline()
    
    def _get_history_file(self) -> str:
        """Get the history file path."""
        config_dir = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        hist_dir = os.path.join(config_dir, "markmark")
        os.makedirs(hist_dir, exist_ok=True)
        return os.path.join(hist_dir, "cli_history")
    
    def _detect_color_support(self) -> bool:
        """Detect if terminal supports colors."""
        if sys.stdout.isatty():
            return os.environ.get("TERM") != "dumb"
        return False
    
    def _init_readline(self) -> None:
        """Initialize readline for history and editing."""
        try:
            readline.parse_and_bind("set editing-mode vi")
            readline.set_completer(self._completer)
            readline.set_completer_delims(" \t\n;")
            
            if os.path.exists(self.history_file):
                readline.read_history_file(self.history_file)
        except Exception:
            pass
    
    def _save_history(self) -> None:
        """Save command history."""
        try:
            readline.write_history_file(self.history_file)
        except Exception:
            pass
    
    def _completer(self, text: str, state: int) -> Optional[str]:
        """Command completion function."""
        options = [cmd for cmd in self.commands if cmd.startswith(text)]
        if state < len(options):
            return options[state]
        return None
    
    def _init_commands(self) -> None:
        """Initialize all CLI commands."""
        
        # File commands
        self._register_command(Command(
            name="open",
            aliases=["o", "e", "edit"],
            description="Open a file for editing",
            usage="open <file>",
            handler=self._cmd_open,
            type=CommandType.FILE,
        ))
        
        self._register_command(Command(
            name="new",
            aliases=["n"],
            description="Create a new file",
            usage="new [filename]",
            handler=self._cmd_new,
            type=CommandType.FILE,
        ))
        
        self._register_command(Command(
            name="save",
            aliases=["w", "write"],
            description="Save the current file",
            usage="save [filename]",
            handler=self._cmd_save,
            type=CommandType.FILE,
            requires_file=True,
        ))
        
        self._register_command(Command(
            name="close",
            aliases=["q", "quit", "bd"],
            description="Close the current file",
            usage="close [force]",
            handler=self._cmd_close,
            type=CommandType.FILE,
        ))
        
        # Editor commands
        self._register_command(Command(
            name="insert",
            aliases=["i"],
            description="Insert text at position",
            usage="insert <line> <text>",
            handler=self._cmd_insert,
            type=CommandType.EDITOR,
            requires_file=True,
        ))
        
        self._register_command(Command(
            name="append",
            aliases=["a"],
            description="Append text to end",
            usage="append <text>",
            handler=self._cmd_append,
            type=CommandType.EDITOR,
            requires_file=True,
        ))
        
        self._register_command(Command(
            name="delete",
            aliases=["d", "del"],
            description="Delete lines",
            usage="delete <start> [end]",
            handler=self._cmd_delete,
            type=CommandType.EDITOR,
            requires_file=True,
        ))
        
        self._register_command(Command(
            name="replace",
            aliases=["r", "sub"],
            description="Replace text",
            usage="replace <pattern> <replacement> [flags]",
            handler=self._cmd_replace,
            type=CommandType.EDITOR,
            requires_file=True,
        ))
        
        self._register_command(Command(
            name="move",
            aliases=["m"],
            description="Move lines",
            usage="move <start> <end> <destination>",
            handler=self._cmd_move,
            type=CommandType.EDITOR,
            requires_file=True,
        ))
        
        self._register_command(Command(
            name="copy",
            aliases=["co", "t"],
            description="Copy lines",
            usage="copy <start> <end> <destination>",
            handler=self._cmd_copy,
            type=CommandType.EDITOR,
            requires_file=True,
        ))
        
        # Buffer commands
        self._register_command(Command(
            name="print",
            aliases=["p", "cat"],
            description="Print buffer contents",
            usage="print [start] [end]",
            handler=self._cmd_print,
            type=CommandType.BUFFER,
        ))
        
        self._register_command(Command(
            name="head",
            aliases=[],
            description="Print first N lines",
            usage="head [n]",
            handler=self._cmd_head,
            type=CommandType.BUFFER,
        ))
        
        self._register_command(Command(
            name="tail",
            aliases=[],
            description="Print last N lines",
            usage="tail [n]",
            handler=self._cmd_tail,
            type=CommandType.BUFFER,
        ))
        
        self._register_command(Command(
            name="lines",
            aliases=["wc", "count"],
            description="Count lines/words/characters",
            usage="lines",
            handler=self._cmd_count,
            type=CommandType.BUFFER,
        ))
        
        # Search commands
        self._register_command(Command(
            name="search",
            aliases=["/", "find", "grep"],
            description="Search for pattern",
            usage="search <pattern>",
            handler=self._cmd_search,
            type=CommandType.SEARCH,
        ))
        
        self._register_command(Command(
            name="match",
            aliases=["glob"],
            description="Find lines matching pattern",
            usage="match <pattern>",
            handler=self._cmd_match,
            type=CommandType.SEARCH,
        ))
        
        # Format commands
        self._register_command(Command(
            name="format",
            aliases=["fmt"],
            description="Format markdown",
            usage="format [options]",
            handler=self._cmd_format,
            type=CommandType.FORMAT,
            requires_file=True,
        ))
        
        self._register_command(Command(
            name="toc",
            aliases=[],
            description="Generate table of contents",
            usage="toc",
            handler=self._cmd_toc,
            type=CommandType.FORMAT,
        ))
        
        self._register_command(Command(
            name="indent",
            aliases=[],
            description="Adjust indentation",
            usage="indent <level>",
            handler=self._cmd_indent,
            type=CommandType.FORMAT,
            requires_file=True,
        ))
        
        self._register_command(Command(
            name="wrap",
            aliases=[],
            description="Set text wrapping",
            usage="wrap <width>",
            handler=self._cmd_wrap,
            type=CommandType.FORMAT,
            requires_file=True,
        ))
        
        # Export commands
        self._register_command(Command(
            name="export",
            aliases=["x"],
            description="Export to format",
            usage="export <format> [file]",
            handler=self._cmd_export,
            type=CommandType.EXPORT,
        ))
        
        self._register_command(Command(
            name="preview",
            aliases=["prev"],
            description="Preview markdown as HTML",
            usage="preview",
            handler=self._cmd_preview,
            type=CommandType.EXPORT,
        ))
        
        # System commands
        self._register_command(Command(
            name="shell",
            aliases=["!", "exec"],
            description="Execute shell command",
            usage="shell <command>",
            handler=self._cmd_shell,
            type=CommandType.SYSTEM,
        ))
        
        self._register_command(Command(
            name="cd",
            aliases=[],
            description="Change directory",
            usage="cd <path>",
            handler=self._cmd_cd,
            type=CommandType.SYSTEM,
        ))
        
        self._register_command(Command(
            name="pwd",
            aliases=[],
            description="Print working directory",
            usage="pwd",
            handler=self._cmd_pwd,
            type=CommandType.SYSTEM,
        ))
        
        self._register_command(Command(
            name="ls",
            aliases=["dir", "files"],
            description="List files",
            usage="ls [path]",
            handler=self._cmd_ls,
            type=CommandType.SYSTEM,
        ))
        
        # Config commands
        self._register_command(Command(
            name="set",
            aliases=[],
            description="Set configuration option",
            usage="set <option> [value]",
            handler=self._cmd_set,
            type=CommandType.CONFIG,
        ))
        
        self._register_command(Command(
            name="get",
            aliases=[],
            description="Get configuration option",
            usage="get <option>",
            handler=self._cmd_get,
            type=CommandType.CONFIG,
        ))
        
        # Help commands
        self._register_command(Command(
            name="help",
            aliases=["h", "?"],
            description="Show help",
            usage="help [command]",
            handler=self._cmd_help,
            type=CommandType.HELP,
        ))
        
        self._register_command(Command(
            name="version",
            aliases=["v", "-v", "--version"],
            description="Show version",
            usage="version",
            handler=self._cmd_version,
            type=CommandType.HELP,
        ))
    
    def _register_command(self, command: Command) -> None:
        """Register a command."""
        self.commands[command.name] = command
        for alias in command.aliases:
            self.commands[alias] = command
    
    # Command handlers
    def _cmd_open(self, args: str) -> str:
        """Open a file."""
        if not args:
            return self._error("Usage: open <file>")
        
        filepath = os.path.expanduser(args.strip())
        
        if not os.path.exists(filepath):
            return self._error(f"File not found: {filepath}")
        
        try:
            with open(filepath, 'r') as f:
                self.buffer = f.read()
            self.current_file = filepath
            self.modified = False
            lines = len(self.buffer.split('\n'))
            return self._success(f"Opened {filepath} ({lines} lines)")
        except Exception as e:
            return self._error(f"Error opening file: {e}")
    
    def _cmd_new(self, args: str) -> str:
        """Create new file."""
        self.buffer = ""
        self.current_file = args.strip() if args else None
        self.modified = False
        return self._success(f"New file{': ' + self.current_file if self.current_file else ''}")
    
    def _cmd_save(self, args: str) -> str:
        """Save file."""
        filepath = args.strip() if args else self.current_file
        
        if not filepath:
            return self._error("No filename specified")
        
        filepath = os.path.expanduser(filepath)
        
        try:
            with open(filepath, 'w') as f:
                f.write(self.buffer)
            self.current_file = filepath
            self.modified = False
            return self._success(f"Saved {filepath}")
        except Exception as e:
            return self._error(f"Error saving file: {e}")
    
    def _cmd_close(self, args: str) -> str:
        """Close file."""
        force = args.strip().lower() in ('force', 'f', '!', '-f')
        
        if self.modified and not force:
            return self._error("File modified. Use 'close force' to discard changes.")
        
        self.buffer = ""
        self.current_file = None
        self.modified = False
        return self._success("File closed")
    
    def _cmd_insert(self, args: str) -> str:
        """Insert text at line."""
        parts = args.split(None, 1)
        if len(parts) < 2:
            return self._error("Usage: insert <line> <text>")
        
        try:
            line_num = int(parts[0])
            text = parts[1]
            
            lines = self.buffer.split('\n')
            if 1 <= line_num <= len(lines) + 1:
                lines.insert(line_num - 1, text)
                self.buffer = '\n'.join(lines)
                self.modified = True
                return self._success(f"Inserted at line {line_num}")
            return self._error(f"Invalid line number: {line_num}")
        except ValueError:
            return self._error("Line number must be an integer")
    
    def _cmd_append(self, args: str) -> str:
        """Append text to buffer."""
        if self.buffer:
            self.buffer += '\n' + args
        else:
            self.buffer = args
        self.modified = True
        return self._success("Text appended")
    
    def _cmd_delete(self, args: str) -> str:
        """Delete lines."""
        parts = args.split()
        if not parts:
            return self._error("Usage: delete <start> [end]")
        
        try:
            start = int(parts[0])
            end = int(parts[1]) if len(parts) > 1 else start
            
            lines = self.buffer.split('\n')
            if 1 <= start <= end <= len(lines):
                deleted = lines[start-1:end]
                del lines[start-1:end]
                self.buffer = '\n'.join(lines)
                self.modified = True
                return self._success(f"Deleted {len(deleted)} line(s)")
            return self._error("Invalid line range")
        except ValueError:
            return self._error("Line numbers must be integers")
    
    def _cmd_replace(self, args: str) -> str:
        """Replace text using regex."""
        # Parse: replace /pattern/replacement/flags
        if not args.startswith('/'):
            parts = args.split(None, 2)
            if len(parts) < 2:
                return self._error("Usage: replace <pattern> <replacement> [flags]")
            pattern, replacement, flags = parts[0], parts[1], parts[2] if len(parts) > 2 else ""
        else:
            # Delimiter format
            parts = args[1:].split('/')
            if len(parts) < 2:
                return self._error("Usage: replace /pattern/replacement/[flags]")
            pattern, replacement, flags = parts[0], parts[1], parts[2] if len(parts) > 2 else ""
        
        try:
            regex_flags = 0
            if 'i' in flags:
                regex_flags |= re.IGNORECASE
            if 'm' in flags:
                regex_flags |= re.MULTILINE
            if 's' in flags:
                regex_flags |= re.DOTALL
            
            count = 0 if 'g' in flags else 1
            new_buffer, num_replacements = re.subn(
                pattern, replacement, self.buffer, count=count, flags=regex_flags
            )
            
            if num_replacements > 0:
                self.buffer = new_buffer
                self.modified = True
                return self._success(f"Replaced {num_replacements} occurrence(s)")
            return self._info("No matches found")
        except re.error as e:
            return self._error(f"Invalid regex: {e}")
    
    def _cmd_move(self, args: str) -> str:
        """Move lines."""
        parts = args.split()
        if len(parts) < 3:
            return self._error("Usage: move <start> <end> <destination>")
        
        try:
            start = int(parts[0])
            end = int(parts[1])
            dest = int(parts[2])
            
            lines = self.buffer.split('\n')
            if 1 <= start <= end <= len(lines) and 1 <= dest <= len(lines) + 1:
                moved = lines[start-1:end]
                del lines[start-1:end]
                
                # Adjust destination if needed
                if dest > start:
                    dest -= (end - start + 1)
                
                for i, line in enumerate(moved):
                    lines.insert(dest - 1 + i, line)
                
                self.buffer = '\n'.join(lines)
                self.modified = True
                return self._success(f"Moved {len(moved)} line(s) to line {dest}")
            return self._error("Invalid line range")
        except ValueError:
            return self._error("Line numbers must be integers")
    
    def _cmd_copy(self, args: str) -> str:
        """Copy lines."""
        parts = args.split()
        if len(parts) < 3:
            return self._error("Usage: copy <start> <end> <destination>")
        
        try:
            start = int(parts[0])
            end = int(parts[1])
            dest = int(parts[2])
            
            lines = self.buffer.split('\n')
            if 1 <= start <= end <= len(lines) and 1 <= dest <= len(lines) + 1:
                copied = lines[start-1:end]
                for i, line in enumerate(copied):
                    lines.insert(dest - 1 + i, line)
                
                self.buffer = '\n'.join(lines)
                self.modified = True
                return self._success(f"Copied {len(copied)} line(s) to line {dest}")
            return self._error("Invalid line range")
        except ValueError:
            return self._error("Line numbers must be integers")
    
    def _cmd_print(self, args: str) -> str:
        """Print buffer contents."""
        parts = args.split()
        lines = self.buffer.split('\n')
        
        if not parts:
            return '\n'.join(f"{i+1:6}  {line}" for i, line in enumerate(lines))
        
        try:
            start = int(parts[0])
            end = int(parts[1]) if len(parts) > 1 else start
            
            if 1 <= start <= end <= len(lines):
                result = []
                for i in range(start - 1, end):
                    result.append(f"{i+1:6}  {lines[i]}")
                return '\n'.join(result)
            return self._error("Invalid line range")
        except ValueError:
            return self._error("Line numbers must be integers")
    
    def _cmd_head(self, args: str) -> str:
        """Print first N lines."""
        try:
            n = int(args) if args else 10
        except ValueError:
            n = 10
        
        lines = self.buffer.split('\n')[:n]
        return '\n'.join(f"{i+1:6}  {line}" for i, line in enumerate(lines))
    
    def _cmd_tail(self, args: str) -> str:
        """Print last N lines."""
        try:
            n = int(args) if args else 10
        except ValueError:
            n = 10
        
        lines = self.buffer.split('\n')
        result_lines = lines[-n:]
        start_num = len(lines) - n + 1
        return '\n'.join(f"{start_num+i:6}  {line}" for i, line in enumerate(result_lines))
    
    def _cmd_count(self, args: str) -> str:
        """Count lines/words/characters."""
        lines = len(self.buffer.split('\n'))
        words = len(self.buffer.split())
        chars = len(self.buffer)
        bytes_count = len(self.buffer.encode('utf-8'))
        
        return f"{lines} lines, {words} words, {chars} characters, {bytes_count} bytes"
    
    def _cmd_search(self, args: str) -> str:
        """Search for pattern."""
        if not args:
            return self._error("Usage: search <pattern>")
        
        try:
            pattern = re.compile(args)
            lines = self.buffer.split('\n')
            results = []
            
            for i, line in enumerate(lines):
                if pattern.search(line):
                    # Highlight match
                    highlighted = pattern.sub(
                        lambda m: self._highlight(m.group(0)),
                        line
                    )
                    results.append(f"{i+1:6}: {highlighted}")
            
            if results:
                return '\n'.join(results)
            return self._info("No matches found")
        except re.error as e:
            return self._error(f"Invalid regex: {e}")
    
    def _cmd_match(self, args: str) -> str:
        """Find matching lines."""
        if not args:
            return self._error("Usage: match <pattern>")
        
        lines = self.buffer.split('\n')
        results = []
        
        for i, line in enumerate(lines):
            if args.lower() in line.lower():
                results.append(f"{i+1:6}: {line}")
        
        if results:
            return '\n'.join(results)
        return self._info("No matches found")
    
    def _cmd_format(self, args: str) -> str:
        """Format markdown."""
        # Simple formatting options
        lines = self.buffer.split('\n')
        formatted = []
        
        # Normalize blank lines
        prev_blank = True
        for line in lines:
            is_blank = not line.strip()
            if is_blank and prev_blank:
                continue
            formatted.append(line)
            prev_blank = is_blank
        
        # Ensure single newline at end
        self.buffer = '\n'.join(formatted).strip() + '\n'
        self.modified = True
        return self._success("Formatted document")
    
    def _cmd_toc(self, args: str) -> str:
        """Generate table of contents."""
        lines = self.buffer.split('\n')
        toc = []
        
        for line in lines:
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                anchor = re.sub(r'[^\w\s-]', '', title.lower())
                anchor = re.sub(r'[\s-]+', '-', anchor)
                indent = '  ' * (level - 1)
                toc.append(f"{indent}- [{title}](#{anchor})")
        
        if toc:
            return '\n'.join(toc)
        return self._info("No headings found")
    
    def _cmd_indent(self, args: str) -> str:
        """Adjust indentation."""
        try:
            level = int(args)
            spaces = ' ' * (level * 4)
            lines = self.buffer.split('\n')
            self.buffer = '\n'.join(spaces + line for line in lines)
            self.modified = True
            return self._success(f"Indented {level} level(s)")
        except ValueError:
            return self._error("Level must be an integer")
    
    def _cmd_wrap(self, args: str) -> str:
        """Wrap text to width."""
        try:
            width = int(args) if args else 80
            import textwrap
            lines = self.buffer.split('\n')
            wrapped = []
            
            for line in lines:
                if line.strip():
                    wrapped.extend(textwrap.wrap(line, width=width))
                else:
                    wrapped.append('')
            
            self.buffer = '\n'.join(wrapped)
            self.modified = True
            return self._success(f"Wrapped to {width} columns")
        except ValueError:
            return self._error("Width must be an integer")
    
    def _cmd_export(self, args: str) -> str:
        """Export to format."""
        parts = args.split(None, 1)
        if not parts:
            return self._error("Usage: export <format> [file]")
        
        fmt = parts[0].lower()
        output_file = parts[1] if len(parts) > 1 else None
        
        if fmt == 'html':
            from .markdown_processor import MarkdownRenderer
            renderer = MarkdownRenderer()
            html = renderer.render(self.buffer)
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(html)
                return self._success(f"Exported to {output_file}")
            return html
        
        return self._error(f"Unknown format: {fmt}")
    
    def _cmd_preview(self, args: str) -> str:
        """Preview markdown as HTML."""
        from .markdown_processor import MarkdownRenderer
        renderer = MarkdownRenderer()
        return renderer.render(self.buffer)
    
    def _cmd_shell(self, args: str) -> str:
        """Execute shell command."""
        import subprocess
        try:
            result = subprocess.run(
                args,
                shell=True,
                capture_output=True,
                text=True
            )
            output = result.stdout
            if result.stderr:
                output += f"\n{result.stderr}"
            return output.strip()
        except Exception as e:
            return self._error(f"Shell error: {e}")
    
    def _cmd_cd(self, args: str) -> str:
        """Change directory."""
        if not args:
            return self._error("Usage: cd <path>")
        
        path = os.path.expanduser(args)
        try:
            os.chdir(path)
            return self._success(f"Changed to {os.getcwd()}")
        except Exception as e:
            return self._error(f"Error: {e}")
    
    def _cmd_pwd(self, args: str) -> str:
        """Print working directory."""
        return os.getcwd()
    
    def _cmd_ls(self, args: str) -> str:
        """List files."""
        path = os.path.expanduser(args) if args else '.'
        try:
            entries = os.listdir(path)
            result = []
            for entry in sorted(entries):
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    result.append(f"{entry}/")
                else:
                    result.append(entry)
            return '\n'.join(result)
        except Exception as e:
            return self._error(f"Error: {e}")
    
    def _cmd_set(self, args: str) -> str:
        """Set configuration option."""
        parts = args.split(None, 1)
        if not parts:
            return self._error("Usage: set <option> [value]")
        
        # TODO: Implement actual config setting
        return self._success(f"Set {parts[0]} = {parts[1] if len(parts) > 1 else 'true'}")
    
    def _cmd_get(self, args: str) -> str:
        """Get configuration option."""
        if not args:
            return self._error("Usage: get <option>")
        
        # TODO: Implement actual config getting
        return f"{args}: not set"
    
    def _cmd_help(self, args: str) -> str:
        """Show help."""
        if args:
            cmd = self.commands.get(args)
            if cmd:
                return f"{cmd.name} - {cmd.description}\nUsage: {cmd.usage}"
            return self._error(f"Unknown command: {args}")
        
        # Show all commands grouped by type
        result = ["MarkMark CLI - Commands\n"]
        
        by_type = {}
        for name, cmd in self.commands.items():
            if name == cmd.name:  # Only show main name
                if cmd.type not in by_type:
                    by_type[cmd.type] = []
                by_type[cmd.type].append(cmd)
        
        for cmd_type, commands in sorted(by_type.items()):
            result.append(f"\n{cmd_type.value.upper()}:")
            for cmd in commands:
                aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
                result.append(f"  {cmd.name}{aliases} - {cmd.description}")
        
        return '\n'.join(result)
    
    def _cmd_version(self, args: str) -> str:
        """Show version."""
        return "MarkMark v1.0.0 - Advanced Markdown Multitool"
    
    # Output formatting
    def _success(self, msg: str) -> str:
        """Format success message."""
        if self.colors_enabled:
            return f"\033[32m✓ {msg}\033[0m"
        return f"✓ {msg}"
    
    def _error(self, msg: str) -> str:
        """Format error message."""
        if self.colors_enabled:
            return f"\033[31m✗ Error: {msg}\033[0m"
        return f"✗ Error: {msg}"
    
    def _info(self, msg: str) -> str:
        """Format info message."""
        if self.colors_enabled:
            return f"\033[34mℹ {msg}\033[0m"
        return f"ℹ {msg}"
    
    def _highlight(self, text: str) -> str:
        """Highlight text."""
        if self.colors_enabled:
            return f"\033[33m{text}\033[0m"
        return text
    
    # Main interface
    def get_prompt(self) -> str:
        """Get the command prompt."""
        if self.current_file:
            name = os.path.basename(self.current_file)
            modified = '*' if self.modified else ''
            prompt = f"markmark:{name}{modified}> "
        else:
            prompt = "markmark> "
        
        if self.colors_enabled:
            return f"\033[36m{prompt}\033[0m"
        return prompt
    
    def execute(self, command_str: str) -> str:
        """Execute a command string."""
        command_str = command_str.strip()
        
        if not command_str:
            return ""
        
        # Parse command
        parts = command_str.split(None, 1)
        cmd_name = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        
        # Look up command
        cmd = self.commands.get(cmd_name)
        if cmd:
            if cmd.requires_file and not self.current_file and not self.buffer:
                return self._error("No file open. Use 'open' or 'new' first.")
            return cmd.handler(args)
        
        return self._error(f"Unknown command: {cmd_name}. Type 'help' for commands.")
    
    def run_repl(self) -> None:
        """Run interactive REPL."""
        self.running = True
        print("MarkMark CLI v1.0.0")
        print("Type 'help' for commands, 'quit' to exit.\n")
        
        try:
            while self.running:
                try:
                    command = input(self.get_prompt())
                    result = self.execute(command)
                    if result:
                        print(result)
                    
                    if command.lower() in ('quit', 'exit', 'q'):
                        self.running = False
                        
                except EOFError:
                    print()
                    break
                except KeyboardInterrupt:
                    print()
                    continue
        finally:
            self._save_history()
    
    def run_batch(self, commands: List[str]) -> str:
        """Run multiple commands in batch mode."""
        results = []
        for cmd in commands:
            results.append(self.execute(cmd))
        return '\n'.join(r for r in results if r)
    
    def process_pipe(self) -> str:
        """Process input from stdin pipe."""
        if not sys.stdin.isatty():
            self.buffer = sys.stdin.read()
            return self.buffer
        return ""


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(
        prog='markmark',
        description='MarkMark - Advanced Markdown Multitool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  markmark file.md              Open file in GUI mode
  markmark -c file.md           Open file in CLI mode
  markmark -e "open file.md; print 1 10"  Execute commands
  markmark -f html file.md      Export file to HTML
  cat file.md | markmark -p     Process from pipe
'''
    )
    
    parser.add_argument('file', nargs='?', help='File to open')
    parser.add_argument('-c', '--cli', action='store_true', help='Run in CLI mode')
    parser.add_argument('-e', '--execute', metavar='COMMANDS', help='Execute commands')
    parser.add_argument('-f', '--format', choices=['html', 'pdf'], help='Export format')
    parser.add_argument('-o', '--output', help='Output file for export')
    parser.add_argument('-p', '--pipe', action='store_true', help='Read from stdin')
    parser.add_argument('-v', '--version', action='version', version='MarkMark v1.0.0')
    parser.add_argument('--vim', action='store_true', help='Enable Vim mode by default')
    parser.add_argument('--zen', action='store_true', help='Start in Zen mode')
    
    return parser


__all__ = ['CLIMode', 'Command', 'CommandType', 'create_parser']
