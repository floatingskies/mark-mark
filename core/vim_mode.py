"""
Vim-mode implementation for MarkMark.
Provides full modal editing with Normal, Insert, Visual, and Command modes.
"""

import re
from enum import Enum
from typing import Optional, List, Callable, Tuple, Set
from dataclasses import dataclass, field
from .config import EditorMode, VimConfig


@dataclass
class Register:
    """Vim register for storing yanked/deleted text."""
    content: str = ""
    linewise: bool = False
    
    def __init__(self, content: str = "", linewise: bool = False):
        self.content = content
        self.linewise = linewise


@dataclass
class Mark:
    """Vim mark for position bookmarking."""
    line: int
    column: int
    filepath: str = ""


@dataclass
class SearchState:
    """Current search state."""
    pattern: str = ""
    direction: int = 1  # 1 for forward, -1 for backward
    highlights: List[Tuple[int, int, int, int]] = field(default_factory=list)


@dataclass 
class CommandState:
    """State for command mode."""
    buffer: str = ""
    cursor_pos: int = 0
    history: List[str] = field(default_factory=list)
    history_index: int = -1


class VimMode:
    """
    Implements Vim-style modal editing.
    
    Modes:
    - NORMAL: Default mode for navigation and manipulation
    - INSERT: Text insertion mode
    - VISUAL: Character-wise selection
    - VISUAL_LINE: Line-wise selection
    - VISUAL_BLOCK: Block-wise selection
    - COMMAND: Ex command mode (:)
    - REPLACE: Character replacement mode
    """
    
    def __init__(self, config: VimConfig):
        self.config = config
        self.mode = EditorMode.NORMAL
        self.previous_mode: Optional[EditorMode] = None
        
        # Registers (a-z, 0-9, unnamed "")
        self.registers: dict = {"": Register()}
        for i in range(26):
            self.registers[chr(ord('a') + i)] = Register()
        for i in range(10):
            self.registers[str(i)] = Register()
        
        # Marks (a-z, A-Z, 0-9, special)
        self.marks: dict = {}
        
        # Motion counts
        self.count_buffer: str = ""
        self.operator_pending: Optional[str] = None
        self.motion_buffer: str = ""
        
        # Command buffer
        self.command_state = CommandState()
        
        # Search state
        self.search_state = SearchState()
        self.last_search_pattern: str = ""
        
        # Macros
        self.macro_recording: Optional[str] = None
        self.macro_buffer: str = ""
        self.macros: dict = {}
        
        # Last command for dot (.) repeat
        self.last_edit_command: Optional[Tuple[str, dict]] = None
        
        # Key sequence buffer for multi-key commands
        self.key_sequence: str = ""
        self.key_timeout_id: Optional[int] = None
        
        # Selection anchor for visual modes
        self.selection_anchor: Optional[Tuple[int, int]] = None
        
        # Callbacks
        self.on_mode_change: Optional[Callable[[EditorMode], None]] = None
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.on_search: Optional[Callable[[str, int], None]] = None
        self.on_command: Optional[Callable[[str], None]] = None
        
        # Motion and operator handlers (set by editor)
        self.motion_handlers: dict = {}
        self.operator_handlers: dict = {}
        self.action_handlers: dict = {}
        
        # Command definitions
        self._init_commands()
    
    def _init_commands(self) -> None:
        """Initialize Ex command definitions."""
        self.ex_commands = {
            "w": self._cmd_write,
            "wq": self._cmd_write_quit,
            "q": self._cmd_quit,
            "q!": self._cmd_force_quit,
            "qa": self._cmd_quit_all,
            "qa!": self._cmd_force_quit_all,
            "e": self._cmd_edit,
            "bn": self._cmd_buffer_next,
            "bp": self._cmd_buffer_prev,
            "bd": self._cmd_buffer_close,
            "ls": self._cmd_list_buffers,
            "s": self._cmd_substitute,
            "%s": self._cmd_substitute_all,
            "g": self._cmd_global,
            "v": self._cmd_global_inverse,
            "d": self._cmd_delete,
            "y": self._cmd_yank,
            "pu": self._cmd_put,
            "co": self._cmd_copy,
            "t": self._cmd_copy,
            "m": self._cmd_move,
            "j": self._cmd_join,
            "r": self._cmd_read,
            "!": self._cmd_shell,
            "so": self._cmd_source,
            "set": self._cmd_set,
            "let": self._cmd_let,
            "map": self._cmd_map,
            "nmap": self._cmd_nmap,
            "imap": self._cmd_imap,
            "vmap": self._cmd_vmap,
            "unmap": self._cmd_unmap,
            "noh": self._cmd_nohlsearch,
            "syn": self._cmd_syntax,
            "hi": self._cmd_highlight,
            "colorscheme": self._cmd_colorscheme,
            "tabnew": self._cmd_tabnew,
            "tabc": self._cmd_tabclose,
            "tabn": self._cmd_tabnext,
            "tabp": self._cmd_tabprev,
            "vsp": self._cmd_vsplit,
            "sp": self._cmd_split,
            "clo": self._cmd_close,
            "on": self._cmd_only,
            "res": self._cmd_resize,
            "vert": self._cmd_vertical_resize,
            "cd": self._cmd_cd,
            "pwd": self._cmd_pwd,
            "mkdir": self._cmd_mkdir,
            "help": self._cmd_help,
            "version": self._cmd_version,
        }
    
    # Mode transitions
    def enter_mode(self, mode: EditorMode) -> None:
        """Transition to a new mode."""
        if mode == self.mode:
            return
            
        self.previous_mode = self.mode
        self.mode = mode
        
        # Reset state on mode change
        self.count_buffer = ""
        self.operator_pending = None
        self.key_sequence = ""
        self.motion_buffer = ""
        
        if self.on_mode_change:
            self.on_mode_change(mode)
        
        self._update_status()
    
    def enter_insert_mode(self) -> None:
        """Enter insert mode."""
        self.enter_mode(EditorMode.INSERT)
    
    def enter_normal_mode(self) -> None:
        """Return to normal mode."""
        self.enter_mode(EditorMode.NORMAL)
        if self.selection_anchor:
            self.selection_anchor = None
    
    def enter_visual_mode(self, line_wise: bool = False, block: bool = False) -> None:
        """Enter visual mode."""
        if block:
            self.enter_mode(EditorMode.VISUAL_BLOCK)
        elif line_wise:
            self.enter_mode(EditorMode.VISUAL_LINE)
        else:
            self.enter_mode(EditorMode.VISUAL)
    
    def enter_command_mode(self) -> None:
        """Enter command mode."""
        self.command_state = CommandState()
        self.enter_mode(EditorMode.COMMAND)
    
    def enter_replace_mode(self) -> None:
        """Enter replace mode."""
        self.enter_mode(EditorMode.REPLACE)
    
    # Key handling
    def handle_key(self, key: str, modifiers: dict = None) -> Optional[dict]:
        """
        Handle a key press in the current mode.
        Returns an action dict if an action should be performed.
        """
        modifiers = modifiers or {}
        
        if self.mode == EditorMode.INSERT:
            return self._handle_insert_key(key, modifiers)
        elif self.mode == EditorMode.NORMAL:
            return self._handle_normal_key(key, modifiers)
        elif self.mode in (EditorMode.VISUAL, EditorMode.VISUAL_LINE, EditorMode.VISUAL_BLOCK):
            return self._handle_visual_key(key, modifiers)
        elif self.mode == EditorMode.COMMAND:
            return self._handle_command_key(key, modifiers)
        elif self.mode == EditorMode.REPLACE:
            return self._handle_replace_key(key, modifiers)
        
        return None
    
    def _handle_normal_key(self, key: str, modifiers: dict) -> Optional[dict]:
        """Handle keys in normal mode."""
        # Handle Ctrl+key combinations
        ctrl = modifiers.get('ctrl', False)
        if ctrl:
            return self._handle_ctrl_key(key, modifiers)
        
        # Handle count prefix
        if key.isdigit() and (self.count_buffer or key != '0'):
            self.count_buffer += key
            self._update_status()
            return None
        
        # Append to key sequence
        self.key_sequence += key
        
        # Check for complete commands
        action = self._lookup_action(self.key_sequence)
        if action is not None:
            result = self._execute_action(action)
            self.key_sequence = ""
            self.count_buffer = ""
            return result
        
        # Check for operator-pending mode
        if self._is_operator(key):
            self.operator_pending = key
            self._update_status()
            return None
        
        # Check for partial command match
        if self._has_partial_match(self.key_sequence):
            return None
        
        # No match - reset
        self.key_sequence = ""
        self.count_buffer = ""
        self.operator_pending = None
        return None
    
    def _handle_insert_key(self, key: str, modifiers: dict) -> Optional[dict]:
        """Handle keys in insert mode."""
        ctrl = modifiers.get('ctrl', False)
        
        if ctrl:
            # Ctrl-o for single normal mode command
            if key == 'o':
                return {"action": "single_normal_command"}
            # Ctrl-w for delete word
            elif key == 'w':
                return {"action": "delete_word_before"}
            # Ctrl-u for delete to line start
            elif key == 'u':
                return {"action": "delete_to_line_start"}
            # Ctrl-t for indent
            elif key == 't':
                return {"action": "indent_line"}
            # Ctrl-d for unindent
            elif key == 'd':
                return {"action": "unindent_line"}
            # Ctrl-n for completion next
            elif key == 'n':
                return {"action": "completion_next"}
            # Ctrl-p for completion prev
            elif key == 'p':
                return {"action": "completion_prev"}
        
        # Escape to normal mode
        if key == 'Escape' or (ctrl and key == 'c'):
            self.enter_normal_mode()
            return {"action": "exit_insert_mode"}
        
        # Regular character insertion
        return {"action": "insert_char", "char": key}
    
    def _handle_visual_key(self, key: str, modifiers: dict) -> Optional[dict]:
        """Handle keys in visual mode."""
        ctrl = modifiers.get('ctrl', False)
        
        # Escape to normal mode
        if key == 'Escape' or (ctrl and key == 'c'):
            self.enter_normal_mode()
            return {"action": "clear_selection"}
        
        # Movement keys extend selection
        if key in 'hjkl':
            return {"action": f"extend_{self._key_to_motion(key)}"}
        
        # Operators act on selection
        if key in ('d', 'x'):
            return self._execute_action("delete_selection")
        elif key == 'y':
            return self._execute_action("yank_selection")
        elif key == 'c':
            return self._execute_action("change_selection")
        elif key == 'r':
            self.enter_mode(EditorMode.NORMAL)
            return {"action": "replace_selection", "await_char": True}
        
        # Other visual mode commands
        action_map = {
            'o': "move_to_other_end",
            'O': "move_to_other_end_block",
            'gv': "reselect_last",
            'J': "join_selection_lines",
            'u': "selection_to_lowercase",
            'U': "selection_to_uppercase",
            '>': "indent_selection",
            '<': "unindent_selection",
            '=': "auto_indent_selection",
        }
        
        if key in action_map:
            return {"action": action_map[key]}
        
        return None
    
    def _handle_command_key(self, key: str, modifiers: dict) -> Optional[dict]:
        """Handle keys in command mode."""
        ctrl = modifiers.get('ctrl', False)
        
        if key == 'Escape' or (ctrl and key == 'c'):
            self.enter_normal_mode()
            return None
        
        if key == 'Return':
            return self._execute_command()
        
        if key == 'BackSpace':
            if self.command_state.cursor_pos > 0:
                pos = self.command_state.cursor_pos
                self.command_state.buffer = (
                    self.command_state.buffer[:pos-1] + 
                    self.command_state.buffer[pos:]
                )
                self.command_state.cursor_pos -= 1
            elif not self.command_state.buffer:
                self.enter_normal_mode()
            self._update_status()
            return None
        
        if key == 'Left':
            if self.command_state.cursor_pos > 0:
                self.command_state.cursor_pos -= 1
            return None
        
        if key == 'Right':
            if self.command_state.cursor_pos < len(self.command_state.buffer):
                self.command_state.cursor_pos += 1
            return None
        
        if key == 'Up':
            # Command history navigation
            if self.command_state.history:
                if self.command_state.history_index < len(self.command_state.history) - 1:
                    self.command_state.history_index += 1
                    self.command_state.buffer = self.command_state.history[
                        self.command_state.history_index
                    ]
                    self.command_state.cursor_pos = len(self.command_state.buffer)
            return None
        
        if key == 'Down':
            if self.command_state.history_index > 0:
                self.command_state.history_index -= 1
                self.command_state.buffer = self.command_state.history[
                    self.command_state.history_index
                ]
            elif self.command_state.history_index == 0:
                self.command_state.history_index = -1
                self.command_state.buffer = ""
            self.command_state.cursor_pos = len(self.command_state.buffer)
            return None
        
        # Tab completion
        if key == 'Tab':
            return {"action": "command_complete"}
        
        # Insert character
        if len(key) == 1:
            pos = self.command_state.cursor_pos
            self.command_state.buffer = (
                self.command_state.buffer[:pos] + key + 
                self.command_state.buffer[pos:]
            )
            self.command_state.cursor_pos += 1
        
        self._update_status()
        return None
    
    def _handle_replace_key(self, key: str, modifiers: dict) -> Optional[dict]:
        """Handle keys in replace mode."""
        if key == 'Escape':
            self.enter_normal_mode()
            return None
        
        return {"action": "replace_char", "char": key}
    
    def _handle_ctrl_key(self, key: str, modifiers: dict) -> Optional[dict]:
        """Handle Ctrl+key combinations."""
        ctrl_map = {
            'f': {"action": "page_down"},
            'b': {"action": "page_up"},
            'd': {"action": "half_page_down"},
            'u': {"action": "half_page_up"},
            'e': {"action": "scroll_line_down"},
            'y': {"action": "scroll_line_up"},
            'r': {"action": "redo"},
            'a': {"action": "increment_number"},
            'x': {"action": "decrement_number"},
            'v': {"action": "enter_visual_block_mode"},
            'o': {"action": "insert_line_above_and_enter"},
            'n': {"action": "search_next_word"},
        }
        
        if key in ctrl_map:
            return ctrl_map[key]
        
        return None
    
    def _lookup_action(self, sequence: str) -> Optional[str]:
        """Look up an action for a key sequence."""
        # Single character commands
        single_char_map = {
            'i': 'enter_insert_mode',
            'I': 'insert_line_start',
            'a': 'insert_after',
            'A': 'insert_line_end',
            'o': 'insert_line_below',
            'O': 'insert_line_above',
            'v': 'enter_visual_mode',
            'V': 'enter_visual_line_mode',
            's': 'substitute_char',
            'S': 'substitute_line',
            'x': 'delete_char',
            'X': 'delete_char_before',
            'r': 'replace_char_prompt',
            'R': 'enter_replace_mode',
            'p': 'paste_after',
            'P': 'paste_before',
            'J': 'join_lines',
            '~': 'toggle_case_and_move',
            'u': 'undo',
            'U': 'undo_line',
            '.': 'repeat_last_edit',
            '@': 'execute_macro',
            'q': 'record_macro',
            'm': 'set_mark',
            "'": "goto_mark_line",
            '`': 'goto_mark_exact',
            ':': 'enter_command_mode',
            '/': 'search_forward',
            '?': 'search_backward',
            'n': 'search_next',
            'N': 'search_prev',
            '*': 'search_word_forward',
            '#': 'search_word_backward',
            '%': 'match_bracket',
            'zz': 'center_cursor',
            'zt': 'cursor_top',
            'zb': 'cursor_bottom',
            'z.': 'center_cursor_first_char',
            'z-': 'cursor_bottom_first_char',
            'z<CR>': 'cursor_top_first_char',
            'zz': 'center_view',
            'zj': 'next_fold',
            'zk': 'prev_fold',
            'zo': 'open_fold',
            'zc': 'close_fold',
            'za': 'toggle_fold',
            'zr': 'open_all_folds',
            'zm': 'close_all_folds',
        }
        
        if sequence in single_char_map:
            return single_char_map[sequence]
        
        # Two-character commands
        two_char_map = {
            'dd': 'delete_line',
            'cc': 'change_line',
            'yy': 'yank_line',
            'Y': 'yank_to_end',  # Actually single char but different
            'D': 'delete_to_end',
            'C': 'change_to_end',
            'gg': 'goto_file_start',
            'G': 'goto_file_end',
            '>>': 'indent_line',
            '<<': 'unindent_line',
            '==': 'auto_indent_line',
            'gd': 'goto_definition',
            'gD': 'goto_definition_global',
            'gf': 'goto_file',
            'ga': 'show_ascii',
            'g8': 'show_utf8',
            'gg': 'goto_first_line',
            'gi': 'goto_last_insert',
            'gI': 'insert_line_start',
            'gh': 'select_mode',
            'gn': 'select_next_match',
            'gN': 'select_prev_match',
            'ge': 'word_end_backward',
            'gE': 'WORD_end_backward',
            'gu': 'make_lowercase_motion',
            'gU': 'make_uppercase_motion',
            'g~': 'toggle_case_motion',
            'gq': 'format_motion',
            'gw': 'format_motion_keep_cursor',
            'gx': 'open_url',
            '[[': 'prev_section',
            ']]': 'next_section',
            '[]': 'prev_section_end',
            '][': 'next_section_end',
            '[(': 'prev_unmatched_open_brace',
            '])': 'next_unmatched_close_brace',
            '[{': 'prev_unmatched_open_brace',
            ']}': 'next_unmatched_close_brace',
            '[m': 'prev_method_start',
            ']m': 'next_method_start',
            '[M': 'prev_method_end',
            ']M': 'next_method_end',
            '[*': 'prev_comment',
            ']*': 'next_comment',
            '[(]': 'prev_open_paren',
            '])': 'next_close_paren',
        }
        
        if sequence in two_char_map:
            return two_char_map[sequence]
        
        # Text object commands (ci", di", etc.)
        if len(sequence) >= 2:
            # Check for text object operations
            if sequence[0] in 'cdy':
                inner = sequence[1] == 'i' if len(sequence) > 2 else False
                around = sequence[1] == 'a' if len(sequence) > 2 else False
                
                # Text objects
                objects = {
                    '"': 'double_quote',
                    "'": 'single_quote',
                    '`': 'backtick',
                    '(': 'parentheses',
                    ')': 'parentheses',
                    '[': 'brackets',
                    ']': 'brackets',
                    '{': 'braces',
                    '}': 'braces',
                    '<': 'angle_brackets',
                    '>': 'angle_brackets',
                    't': 'tag',
                    'w': 'word',
                    'W': 'WORD',
                    's': 'sentence',
                    'p': 'paragraph',
                    'b': 'block',  # alias for (
                    'B': 'block',  # alias for {
                    'i': 'indent',
                }
                
                # Simple two-char commands with operator
                if len(sequence) == 2 and sequence[1] in 'wWebB$0^':
                    motion_map = {
                        'w': 'word', 'W': 'WORD',
                        'e': 'word_end', 'E': 'WORD_end',
                        'b': 'word_back', 'B': 'WORD_back',
                        '$': 'line_end', '0': 'line_start', '^': 'first_non_whitespace',
                    }
                    return f"{sequence[0]}_motion_{motion_map.get(sequence[1], sequence[1])}"
                
                # Text object commands (ci", da{, etc.)
                if len(sequence) == 3 and sequence[1] in 'ia':
                    obj = sequence[2]
                    if obj in objects:
                        inner_outer = 'inner' if sequence[1] == 'i' else 'around'
                        return f"{sequence[0]}_{inner_outer}_{objects[obj]}"
        
        return None
    
    def _is_operator(self, key: str) -> bool:
        """Check if key is an operator."""
        return key in 'cdy><g~gu gUgqgwg!?'
    
    def _has_partial_match(self, sequence: str) -> bool:
        """Check if sequence is a prefix of any command."""
        # Check all commands that start with this sequence
        all_sequences = [
            'gg', 'gd', 'gD', 'gf', 'ga', 'g8', 'gi', 'gI', 'gh', 'gn', 'gN',
            'ge', 'gE', 'gu', 'gU', 'g~', 'gq', 'gw', 'gx',
            'dd', 'cc', 'yy', '>>', '<<', '==',
            'ci', 'ca', 'di', 'da', 'yi', 'ya',
            '[[', ']]', '[]', '][',
            '[(', '])', '[{', ']}', '[m', ']m', '[M', ']M',
            'zj', 'zk', 'zo', 'zc', 'za', 'zr', 'zm',
        ]
        
        for seq in all_sequences:
            if seq.startswith(sequence) and seq != sequence:
                return True
        return False
    
    def _execute_action(self, action: str) -> dict:
        """Execute an action and return the result."""
        count = int(self.count_buffer) if self.count_buffer else 1
        
        return {
            "action": action,
            "count": count,
            "operator": self.operator_pending,
        }
    
    def _execute_command(self) -> Optional[dict]:
        """Execute the command buffer."""
        cmd = self.command_state.buffer.strip()
        
        if not cmd:
            self.enter_normal_mode()
            return None
        
        # Add to history
        if cmd not in self.command_state.history:
            self.command_state.history.insert(0, cmd)
            if len(self.command_state.history) > 100:
                self.command_state.history.pop()
        self.command_state.history_index = -1
        
        # Parse command
        parts = cmd.split(None, 1)
        cmd_name = parts[0]
        cmd_args = parts[1] if len(parts) > 1 else ""
        
        # Look up and execute command
        result = None
        if cmd_name in self.ex_commands:
            result = self.ex_commands[cmd_name](cmd_args)
        else:
            # Try range commands
            range_match = re.match(r'^(\d+|\$|\.)?(?:,(\d+|\$|\.))?(\w+)(.*)$', cmd)
            if range_match:
                start, end, name, args = range_match.groups()
                if name in self.ex_commands:
                    result = self.ex_commands[name](args, start=start, end=end)
        
        self.enter_normal_mode()
        return result or {"action": "command_executed", "command": cmd}
    
    # Ex command implementations
    def _cmd_write(self, args: str, **kwargs) -> dict:
        """Write file."""
        return {"action": "save_file", "path": args}
    
    def _cmd_write_quit(self, args: str, **kwargs) -> dict:
        """Write and quit."""
        return {"action": "save_and_quit", "path": args}
    
    def _cmd_quit(self, args: str, **kwargs) -> dict:
        """Quit."""
        return {"action": "quit"}
    
    def _cmd_force_quit(self, args: str, **kwargs) -> dict:
        """Force quit."""
        return {"action": "force_quit"}
    
    def _cmd_quit_all(self, args: str, **kwargs) -> dict:
        """Quit all buffers."""
        return {"action": "quit_all"}
    
    def _cmd_force_quit_all(self, args: str, **kwargs) -> dict:
        """Force quit all."""
        return {"action": "force_quit_all"}
    
    def _cmd_edit(self, args: str, **kwargs) -> dict:
        """Edit file."""
        return {"action": "open_file", "path": args}
    
    def _cmd_buffer_next(self, args: str, **kwargs) -> dict:
        """Next buffer."""
        return {"action": "next_buffer"}
    
    def _cmd_buffer_prev(self, args: str, **kwargs) -> dict:
        """Previous buffer."""
        return {"action": "prev_buffer"}
    
    def _cmd_buffer_close(self, args: str, **kwargs) -> dict:
        """Close buffer."""
        return {"action": "close_buffer"}
    
    def _cmd_list_buffers(self, args: str, **kwargs) -> dict:
        """List buffers."""
        return {"action": "list_buffers"}
    
    def _cmd_substitute(self, args: str, start: str = None, end: str = None, **kwargs) -> dict:
        """Substitute command."""
        # Parse s/pattern/replacement/flags
        match = re.match(r'^s(.)(.*?)\1(.*?)(?:\1([giI]+))?$', args)
        if match:
            delim, pattern, replacement, flags = match.groups()
            return {
                "action": "substitute",
                "pattern": pattern,
                "replacement": replacement,
                "flags": flags or "",
                "start": start,
                "end": end,
            }
        return {"action": "error", "message": "Invalid substitute syntax"}
    
    def _cmd_substitute_all(self, args: str, **kwargs) -> dict:
        """Substitute in entire file."""
        return self._cmd_substitute(args, start="1", end="$", **kwargs)
    
    def _cmd_global(self, args: str, **kwargs) -> dict:
        """Global command - execute command on matching lines."""
        match = re.match(r'^(.)(.*?)\1(.*)$', args)
        if match:
            delim, pattern, cmd = match.groups()
            return {"action": "global", "pattern": pattern, "command": cmd, "inverse": False}
        return {"action": "error", "message": "Invalid global syntax"}
    
    def _cmd_global_inverse(self, args: str, **kwargs) -> dict:
        """Inverse global command."""
        result = self._cmd_global(args, **kwargs)
        if isinstance(result, dict) and result.get("action") == "global":
            result["inverse"] = True
        return result
    
    def _cmd_delete(self, args: str, start: str = None, end: str = None, **kwargs) -> dict:
        """Delete lines."""
        return {"action": "delete_lines", "start": start, "end": end}
    
    def _cmd_yank(self, args: str, start: str = None, end: str = None, **kwargs) -> dict:
        """Yank lines."""
        return {"action": "yank_lines", "start": start, "end": end, "register": args.strip()}
    
    def _cmd_put(self, args: str, **kwargs) -> dict:
        """Put from register."""
        return {"action": "put", "register": args.strip()}
    
    def _cmd_copy(self, args: str, start: str = None, end: str = None, **kwargs) -> dict:
        """Copy lines."""
        try:
            dest = int(args.strip())
            return {"action": "copy_lines", "start": start, "end": end, "destination": dest}
        except ValueError:
            return {"action": "error", "message": "Invalid destination"}
    
    def _cmd_move(self, args: str, start: str = None, end: str = None, **kwargs) -> dict:
        """Move lines."""
        try:
            dest = int(args.strip())
            return {"action": "move_lines", "start": start, "end": end, "destination": dest}
        except ValueError:
            return {"action": "error", "message": "Invalid destination"}
    
    def _cmd_join(self, args: str, start: str = None, end: str = None, **kwargs) -> dict:
        """Join lines."""
        return {"action": "join_lines_range", "start": start, "end": end}
    
    def _cmd_read(self, args: str, **kwargs) -> dict:
        """Read file into buffer."""
        return {"action": "read_file", "path": args.strip()}
    
    def _cmd_shell(self, args: str, **kwargs) -> dict:
        """Execute shell command."""
        return {"action": "shell_command", "command": args}
    
    def _cmd_source(self, args: str, **kwargs) -> dict:
        """Source a configuration file."""
        return {"action": "source_config", "path": args.strip()}
    
    def _cmd_set(self, args: str, **kwargs) -> dict:
        """Set option."""
        parts = args.split(None, 1)
        if len(parts) == 1:
            # Toggle or show option
            return {"action": "set_option", "option": parts[0]}
        else:
            return {"action": "set_option", "option": parts[0], "value": parts[1]}
    
    def _cmd_let(self, args: str, **kwargs) -> dict:
        """Set variable."""
        match = re.match(r'^(\w+)\s*=\s*(.*)$', args)
        if match:
            return {"action": "set_variable", "name": match.group(1), "value": match.group(2)}
        return {"action": "error", "message": "Invalid let syntax"}
    
    def _cmd_map(self, args: str, **kwargs) -> dict:
        """Create key mapping."""
        parts = args.split(None, 1)
        if len(parts) == 2:
            return {"action": "map_key", "key": parts[0], "command": parts[1], "mode": "normal"}
        return {"action": "error", "message": "Invalid map syntax"}
    
    def _cmd_nmap(self, args: str, **kwargs) -> dict:
        """Normal mode mapping."""
        result = self._cmd_map(args, **kwargs)
        if isinstance(result, dict) and result.get("action") == "map_key":
            result["mode"] = "normal"
        return result
    
    def _cmd_imap(self, args: str, **kwargs) -> dict:
        """Insert mode mapping."""
        result = self._cmd_map(args, **kwargs)
        if isinstance(result, dict) and result.get("action") == "map_key":
            result["mode"] = "insert"
        return result
    
    def _cmd_vmap(self, args: str, **kwargs) -> dict:
        """Visual mode mapping."""
        result = self._cmd_map(args, **kwargs)
        if isinstance(result, dict) and result.get("action") == "map_key":
            result["mode"] = "visual"
        return result
    
    def _cmd_unmap(self, args: str, **kwargs) -> dict:
        """Remove key mapping."""
        return {"action": "unmap_key", "key": args.strip()}
    
    def _cmd_nohlsearch(self, args: str, **kwargs) -> dict:
        """Clear search highlights."""
        return {"action": "clear_search_highlights"}
    
    def _cmd_syntax(self, args: str, **kwargs) -> dict:
        """Syntax commands."""
        return {"action": "syntax_command", "args": args}
    
    def _cmd_highlight(self, args: str, **kwargs) -> dict:
        """Highlight commands."""
        return {"action": "highlight_command", "args": args}
    
    def _cmd_colorscheme(self, args: str, **kwargs) -> dict:
        """Set colorscheme."""
        return {"action": "set_colorscheme", "name": args.strip()}
    
    def _cmd_tabnew(self, args: str, **kwargs) -> dict:
        """Open new tab."""
        return {"action": "new_tab", "path": args.strip() if args else None}
    
    def _cmd_tabclose(self, args: str, **kwargs) -> dict:
        """Close tab."""
        return {"action": "close_tab"}
    
    def _cmd_tabnext(self, args: str, **kwargs) -> dict:
        """Next tab."""
        return {"action": "next_tab"}
    
    def _cmd_tabprev(self, args: str, **kwargs) -> dict:
        """Previous tab."""
        return {"action": "prev_tab"}
    
    def _cmd_vsplit(self, args: str, **kwargs) -> dict:
        """Vertical split."""
        return {"action": "vsplit", "path": args.strip() if args else None}
    
    def _cmd_split(self, args: str, **kwargs) -> dict:
        """Horizontal split."""
        return {"action": "hsplit", "path": args.strip() if args else None}
    
    def _cmd_close(self, args: str, **kwargs) -> dict:
        """Close window."""
        return {"action": "close_window"}
    
    def _cmd_only(self, args: str, **kwargs) -> dict:
        """Close other windows."""
        return {"action": "close_other_windows"}
    
    def _cmd_resize(self, args: str, **kwargs) -> dict:
        """Resize window."""
        return {"action": "resize_window", "size": args.strip()}
    
    def _cmd_vertical_resize(self, args: str, **kwargs) -> dict:
        """Vertical resize."""
        return {"action": "vertical_resize", "size": args.strip()}
    
    def _cmd_cd(self, args: str, **kwargs) -> dict:
        """Change directory."""
        return {"action": "change_directory", "path": args.strip()}
    
    def _cmd_pwd(self, args: str, **kwargs) -> dict:
        """Print working directory."""
        return {"action": "show_directory"}
    
    def _cmd_mkdir(self, args: str, **kwargs) -> dict:
        """Create directory."""
        return {"action": "make_directory", "path": args.strip()}
    
    def _cmd_help(self, args: str, **kwargs) -> dict:
        """Show help."""
        return {"action": "show_help", "topic": args.strip() if args else None}
    
    def _cmd_version(self, args: str, **kwargs) -> dict:
        """Show version."""
        return {"action": "show_version"}
    
    # Utility methods
    def _key_to_motion(self, key: str) -> str:
        """Convert h/j/k/l to motion name."""
        return {'h': 'left', 'j': 'down', 'k': 'up', 'l': 'right'}.get(key, key)
    
    def get_count(self) -> int:
        """Get the current count, defaulting to 1."""
        return int(self.count_buffer) if self.count_buffer else 1
    
    def get_mode_string(self) -> str:
        """Get a string representation of the current mode."""
        mode_strings = {
            EditorMode.NORMAL: "NORMAL",
            EditorMode.INSERT: "INSERT",
            EditorMode.VISUAL: "VISUAL",
            EditorMode.VISUAL_LINE: "VISUAL LINE",
            EditorMode.VISUAL_BLOCK: "VISUAL BLOCK",
            EditorMode.COMMAND: "COMMAND",
            EditorMode.REPLACE: "REPLACE",
        }
        return mode_strings.get(self.mode, "NORMAL")
    
    def _update_status(self) -> None:
        """Update the status line."""
        if self.on_status_update:
            status_parts = [f"-- {self.get_mode_string()} --"]
            
            if self.count_buffer:
                status_parts.append(f"Count: {self.count_buffer}")
            
            if self.operator_pending:
                status_parts.append(f"Operator: {self.operator_pending}")
            
            if self.mode == EditorMode.COMMAND:
                status_parts.append(f":{self.command_state.buffer}")
            
            self.on_status_update(" ".join(status_parts))
    
    # Register operations
    def set_register(self, name: str, content: str, linewise: bool = False) -> None:
        """Set register content."""
        if name in self.registers:
            self.registers[name] = Register(content, linewise)
        # Also set unnamed register
        if name != "":
            self.registers[""] = Register(content, linewise)
    
    def get_register(self, name: str) -> Optional[Register]:
        """Get register content."""
        return self.registers.get(name, self.registers.get(""))
    
    # Mark operations
    def set_mark(self, name: str, line: int, column: int, filepath: str = "") -> None:
        """Set a mark."""
        self.marks[name] = Mark(line, column, filepath)
    
    def get_mark(self, name: str) -> Optional[Mark]:
        """Get a mark."""
        return self.marks.get(name)
    
    # Macro operations
    def start_macro(self, register: str) -> None:
        """Start recording a macro."""
        self.macro_recording = register
        self.macro_buffer = ""
    
    def stop_macro(self) -> None:
        """Stop recording macro."""
        if self.macro_recording:
            self.macros[self.macro_recording] = self.macro_buffer
            self.macro_recording = None
            self.macro_buffer = ""
    
    def play_macro(self, register: str) -> str:
        """Get macro content for playback."""
        return self.macros.get(register, "")
    
    # Search operations
    def set_search_pattern(self, pattern: str, direction: int = 1) -> None:
        """Set the current search pattern."""
        self.search_state.pattern = pattern
        self.search_state.direction = direction
        self.last_search_pattern = pattern
    
    def get_search_pattern(self) -> str:
        """Get the current search pattern."""
        return self.search_state.pattern or self.last_search_pattern
