"""
Helix/Neovim inspired features for MarkMark.
Provides multi-cursor editing, text objects, object selection, and advanced editing features.
"""

import re
from typing import List, Tuple, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum


class SelectionDirection(Enum):
    FORWARD = 1
    BACKWARD = -1


@dataclass
class Selection:
    """Represents a selection/cursor in the editor."""
    anchor: int  # Start position
    head: int    # End position (cursor position)
    primary: bool = False
    
    @property
    def start(self) -> int:
        """Get the start position (smaller of anchor/head)."""
        return min(self.anchor, self.head)
    
    @property
    def end(self) -> int:
        """Get the end position (larger of anchor/head)."""
        return max(self.anchor, self.head)
    
    @property
    def direction(self) -> SelectionDirection:
        """Get selection direction."""
        return SelectionDirection.FORWARD if self.head >= self.anchor else SelectionDirection.BACKWARD
    
    @property
    def is_reversed(self) -> bool:
        """Check if selection is reversed (anchor > head)."""
        return self.anchor > self.head
    
    @property
    def is_empty(self) -> bool:
        """Check if selection is empty (cursor only)."""
        return self.anchor == self.head
    
    def __len__(self) -> int:
        """Get selection length."""
        return abs(self.head - self.anchor)


@dataclass
class TextObject:
    """Definition of a text object."""
    name: str
    start_pattern: str
    end_pattern: str
    start_inclusive: bool = False
    end_inclusive: bool = False
    nested: bool = False  # Allow nested instances
    match_balanced: bool = True  # Match balanced pairs like (), [], {}


class TextObjectFinder:
    """Find text objects in buffer content."""
    
    # Standard text object definitions
    TEXT_OBJECTS = {
        # Pairs
        '(': TextObject('parentheses', r'\(', r'\)', match_balanced=True),
        ')': TextObject('parentheses', r'\(', r'\)', match_balanced=True),
        '[': TextObject('brackets', r'\[', r'\]', match_balanced=True),
        ']': TextObject('brackets', r'\[', r'\]', match_balanced=True),
        '{': TextObject('braces', r'\{', r'\}', match_balanced=True),
        '}': TextObject('braces', r'\{', r'\}', match_balanced=True),
        '<': TextObject('angle', r'<', r'>', match_balanced=True),
        '>': TextObject('angle', r'<', r'>', match_balanced=True),
        
        # Quotes
        '"': TextObject('double_quote', r'"', r'"', match_balanced=False),
        "'": TextObject('single_quote', r"'", r"'", match_balanced=False),
        '`': TextObject('backtick', r'`', r'`', match_balanced=False),
        
        # Structural
        'w': TextObject('word', r'\b\w', r'\w\b', match_balanced=False),
        'W': TextObject('WORD', r'\S+', r'\S+', match_balanced=False),
        's': TextObject('sentence', r'[.!?]\s+', r'[.!?]', match_balanced=False),
        'p': TextObject('paragraph', r'\n\s*\n', r'\n\s*\n', match_balanced=False),
        
        # Code structures
        'f': TextObject('function', r'\b(def|function|fn|func|fun)\b', r'\}', match_balanced=True, nested=True),
        'c': TextObject('class', r'\b(class|struct|interface|impl)\b', r'\}', match_balanced=True, nested=True),
        't': TextObject('tag', r'<[^/!][^>]*>', r'</[^>]*>', match_balanced=True, nested=True),
        'i': TextObject('indent', r'^\s*$', r'^\S', match_balanced=False),
        
        # Markdown specific
        'h': TextObject('heading', r'^#+\s+', r'\n', match_balanced=False),
        'l': TextObject('link', r'\[', r'\)', match_balanced=True),
        'k': TextObject('code_block', r'```', r'```', match_balanced=False),
    }
    
    def __init__(self):
        self.custom_objects: dict = {}
    
    def find_object(self, content: str, cursor_pos: int, obj_type: str, inner: bool = True) -> Optional[Tuple[int, int]]:
        """
        Find a text object around the cursor position.
        
        Args:
            content: The buffer content
            cursor_pos: Current cursor position
            obj_type: Type of object to find
            inner: If True, find inner object (exclude delimiters); if False, include delimiters
        
        Returns:
            Tuple of (start, end) positions, or None if not found
        """
        obj = self.TEXT_OBJECTS.get(obj_type) or self.custom_objects.get(obj_type)
        if not obj:
            return None
        
        if obj.match_balanced and obj_type in '()[]{}':
            return self._find_balanced_pair(content, cursor_pos, obj_type, inner)
        elif obj_type in '"\'`':
            return self._find_quote(content, cursor_pos, obj_type, inner)
        elif obj_type in 'wW':
            return self._find_word(content, cursor_pos, obj_type == 'W', inner)
        elif obj_type == 'p':
            return self._find_paragraph(content, cursor_pos, inner)
        elif obj_type == 's':
            return self._find_sentence(content, cursor_pos, inner)
        elif obj_type == 't':
            return self._find_tag(content, cursor_pos, inner)
        elif obj_type == 'l':
            return self._find_markdown_link(content, cursor_pos, inner)
        elif obj_type == 'k':
            return self._find_code_block(content, cursor_pos, inner)
        
        return None
    
    def _find_balanced_pair(self, content: str, pos: int, pair_char: str, inner: bool) -> Optional[Tuple[int, int]]:
        """Find balanced pair like (), [], {}."""
        pairs = {'(': ')', '[': ']', '{': '}', ')': '(', ']': '[', '}': '{'}
        open_chars = '([{'
        close_chars = ')]}'
        
        open_char = pair_char if pair_char in open_chars else pairs.get(pair_char, pair_char)
        close_char = pairs.get(open_char, open_char)
        
        # Find opening bracket
        depth = 0
        start = -1
        
        # Search backward for opening
        for i in range(pos, -1, -1):
            if content[i] == close_char and i != pos:
                depth += 1
            elif content[i] == open_char:
                if depth == 0:
                    start = i
                    break
                depth -= 1
        
        if start == -1:
            return None
        
        # Search forward for closing
        depth = 0
        end = -1
        for i in range(start, len(content)):
            if content[i] == open_char:
                depth += 1
            elif content[i] == close_char:
                depth -= 1
                if depth == 0:
                    end = i
                    break
        
        if end == -1:
            return None
        
        if inner:
            return (start + 1, end)
        return (start, end + 1)
    
    def _find_quote(self, content: str, pos: int, quote: str, inner: bool) -> Optional[Tuple[int, int]]:
        """Find quoted string."""
        # Find start of quote
        start = -1
        for i in range(pos, -1, -1):
            if content[i] == quote:
                # Check if it's escaped
                if i > 0 and content[i-1] == '\\':
                    continue
                start = i
                break
        
        if start == -1:
            return None
        
        # Find end of quote
        end = -1
        for i in range(start + 1, len(content)):
            if content[i] == quote and content[i-1] != '\\':
                end = i
                break
        
        if end == -1:
            return None
        
        if inner:
            return (start + 1, end)
        return (start, end + 1)
    
    def _find_word(self, content: str, pos: int, big_word: bool, inner: bool) -> Optional[Tuple[int, int]]:
        """Find word boundaries."""
        if pos >= len(content):
            return None
        
        # Define word boundaries
        if big_word:
            # WORD: non-whitespace
            word_chars = lambda c: not c.isspace()
        else:
            # word: alphanumeric + underscore
            word_chars = lambda c: c.isalnum() or c == '_'
        
        # Find start
        start = pos
        while start > 0 and word_chars(content[start - 1]):
            start -= 1
        
        # Find end
        end = pos
        while end < len(content) and word_chars(content[end]):
            end += 1
        
        if start == end:
            return None
        
        return (start, end)
    
    def _find_paragraph(self, content: str, pos: int, inner: bool) -> Optional[Tuple[int, int]]:
        """Find paragraph boundaries."""
        lines = content[:pos].count('\n')
        all_lines = content.split('\n')
        
        # Find paragraph start
        start_line = lines
        while start_line > 0 and all_lines[start_line - 1].strip():
            start_line -= 1
        
        # Find paragraph end
        end_line = lines
        while end_line < len(all_lines) - 1 and all_lines[end_line + 1].strip():
            end_line += 1
        
        # Convert to character positions
        start_pos = sum(len(all_lines[i]) + 1 for i in range(start_line))
        end_pos = sum(len(all_lines[i]) + 1 for i in range(end_line + 1)) - 1
        
        return (start_pos, end_pos)
    
    def _find_sentence(self, content: str, pos: int, inner: bool) -> Optional[Tuple[int, int]]:
        """Find sentence boundaries."""
        # Find sentence end pattern
        end_pattern = r'[.!?]+\s+'
        
        # Search backward for sentence start
        start = 0
        for match in re.finditer(r'[.!?]+\s+', content[:pos]):
            start = match.end()
        
        # Search forward for sentence end
        end = len(content)
        match = re.search(r'[.!?]+\s+', content[pos:])
        if match:
            end = pos + match.end()
        
        return (start, end)
    
    def _find_tag(self, content: str, pos: int, inner: bool) -> Optional[Tuple[int, int]]:
        """Find HTML/XML tag content."""
        # Find opening tag
        open_pattern = r'<([^/!>][^>]*)>'
        close_pattern = r'</([^>]+)>'
        
        # Search backward for opening tag
        start = -1
        tag_name = ""
        for match in re.finditer(open_pattern, content[:pos + 1]):
            tag_name = match.group(1).split()[0]
            start = match.end()
        
        if start == -1:
            return None
        
        # Find matching closing tag
        close_tag = f'</{tag_name}>'
        depth = 1
        end = -1
        
        for i in range(start, len(content)):
            if content[i:].startswith(f'<{tag_name}'):
                depth += 1
            elif content[i:].startswith(close_tag):
                depth -= 1
                if depth == 0:
                    end = i
                    break
        
        if end == -1:
            return None
        
        if inner:
            return (start, end)
        return (start - len(f'<{tag_name}>'), end + len(close_tag))
    
    def _find_markdown_link(self, content: str, pos: int, inner: bool) -> Optional[Tuple[int, int]]:
        """Find markdown link [text](url)."""
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
        for match in re.finditer(pattern, content):
            if match.start() <= pos <= match.end():
                if inner:
                    # Return just the text part
                    text_start = match.start() + 1
                    text_end = match.start() + 1 + len(match.group(1))
                    return (text_start, text_end)
                return (match.start(), match.end())
        
        return None
    
    def _find_code_block(self, content: str, pos: int, inner: bool) -> Optional[Tuple[int, int]]:
        """Find markdown code block."""
        pattern = r'```.*?\n(.*?)```'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            if match.start() <= pos <= match.end():
                if inner:
                    # Find content between backticks
                    start = content.find('\n', match.start()) + 1
                    end = match.end() - 3
                    return (start, end)
                return (match.start(), match.end())
        
        return None
    
    def add_custom_object(self, obj: TextObject) -> None:
        """Add a custom text object."""
        self.custom_objects[obj.name] = obj


class MultiCursorManager:
    """Manages multiple cursors/selections."""
    
    def __init__(self):
        self.selections: List[Selection] = [Selection(0, 0, primary=True)]
        self.text_object_finder = TextObjectFinder()
    
    @property
    def primary_selection(self) -> Selection:
        """Get the primary selection."""
        for sel in self.selections:
            if sel.primary:
                return sel
        return self.selections[0] if self.selections else Selection(0, 0, primary=True)
    
    @property
    def cursor_positions(self) -> List[int]:
        """Get all cursor positions."""
        return [sel.head for sel in self.selections]
    
    def add_selection(self, anchor: int, head: int, primary: bool = False) -> None:
        """Add a new selection."""
        if primary:
            # Remove primary from others
            for sel in self.selections:
                sel.primary = False
        self.selections.append(Selection(anchor, head, primary))
    
    def remove_selection(self, index: int) -> None:
        """Remove a selection by index."""
        if 0 <= index < len(self.selections):
            was_primary = self.selections[index].primary
            del self.selections[index]
            if was_primary and self.selections:
                self.selections[0].primary = True
    
    def clear_selections(self) -> None:
        """Clear all but the primary selection."""
        primary = self.primary_selection
        self.selections = [Selection(primary.head, primary.head, primary=True)]
    
    def select_all(self, content_length: int) -> None:
        """Select entire document."""
        self.selections = [Selection(0, content_length, primary=True)]
    
    def split_selection_by_line(self, content: str) -> None:
        """Split selection into one selection per line."""
        new_selections = []
        lines = content.split('\n')
        pos = 0
        
        for i, line in enumerate(lines):
            line_end = pos + len(line)
            
            # Check if this line intersects with any selection
            for sel in self.selections:
                if sel.start <= line_end and sel.end >= pos:
                    new_selections.append(Selection(pos, line_end, i == 0))
            pos = line_end + 1
        
        if new_selections:
            # Ensure one is primary
            for sel in new_selections:
                sel.primary = False
            new_selections[0].primary = True
            self.selections = new_selections
    
    def split_selection_by_regex(self, content: str, pattern: str) -> None:
        """Split selection by regex matches."""
        new_selections = []
        
        for sel in self.selections:
            for match in re.finditer(pattern, content[sel.start:sel.end]):
                new_selections.append(Selection(
                    sel.start + match.start(),
                    sel.start + match.end(),
                    len(new_selections) == 0
                ))
        
        if new_selections:
            self.selections = new_selections
    
    def extend_to_word_boundary(self, content: str, forward: bool = True) -> None:
        """Extend all selections to word boundaries."""
        for sel in self.selections:
            pos = sel.head
            
            if forward:
                while pos < len(content) and content[pos].isalnum():
                    pos += 1
                while pos < len(content) and not content[pos].isalnum():
                    pos += 1
            else:
                while pos > 0 and content[pos-1].isalnum():
                    pos -= 1
                while pos > 0 and not content[pos-1].isalnum():
                    pos -= 1
            
            sel.head = pos
    
    def select_text_object(self, content: str, obj_type: str, inner: bool = True) -> None:
        """Select text object at each cursor position."""
        new_selections = []
        
        for sel in self.selections:
            bounds = self.text_object_finder.find_object(content, sel.head, obj_type, inner)
            if bounds:
                new_selections.append(Selection(bounds[0], bounds[1], len(new_selections) == 0))
        
        if new_selections:
            self.selections = new_selections
    
    def add_cursor_above(self, content: str) -> None:
        """Add cursor on the line above (Helix C-o)."""
        primary = self.primary_selection
        
        # Find current line start
        line_start = content.rfind('\n', 0, primary.head)
        if line_start == -1:
            return
        
        # Find previous line start
        prev_line_start = content.rfind('\n', 0, line_start)
        if prev_line_start == -1:
            prev_line_start = 0
        else:
            prev_line_start += 1
        
        # Calculate column offset
        line_end = content.find('\n', line_start + 1)
        if line_end == -1:
            line_end = len(content)
        column = primary.head - line_start - 1
        
        # Add cursor at same column on previous line
        prev_line_end = content.find('\n', prev_line_start)
        if prev_line_end == -1:
            prev_line_end = len(content)
        
        new_pos = min(prev_line_start + column, prev_line_end - 1)
        self.add_selection(new_pos, new_pos)
    
    def add_cursor_below(self, content: str) -> None:
        """Add cursor on the line below (Helix C-n)."""
        primary = self.primary_selection
        
        # Find current line end
        line_end = content.find('\n', primary.head)
        if line_end == -1:
            return
        
        # Find next line start and end
        next_line_start = line_end + 1
        next_line_end = content.find('\n', next_line_start)
        if next_line_end == -1:
            next_line_end = len(content)
        
        # Calculate column offset
        line_start = content.rfind('\n', 0, primary.head)
        if line_start == -1:
            line_start = 0
        else:
            line_start += 1
        column = primary.head - line_start
        
        # Add cursor at same column on next line
        new_pos = min(next_line_start + column, next_line_end - 1)
        self.add_selection(new_pos, new_pos)
    
    def flip_selections(self) -> None:
        """Flip anchor and head of all selections."""
        for sel in self.selections:
            sel.anchor, sel.head = sel.head, sel.anchor
    
    def merge_consecutive_selections(self) -> None:
        """Merge overlapping or consecutive selections."""
        if len(self.selections) < 2:
            return
        
        # Sort by start position
        sorted_sels = sorted(self.selections, key=lambda s: s.start)
        merged = [sorted_sels[0]]
        
        for sel in sorted_sels[1:]:
            last = merged[-1]
            if sel.start <= last.end:
                # Merge
                merged[-1] = Selection(
                    last.start,
                    max(last.end, sel.end),
                    last.primary or sel.primary
                )
            else:
                merged.append(sel)
        
        # Ensure one primary
        has_primary = any(s.primary for s in merged)
        if not has_primary and merged:
            merged[0].primary = True
        
        self.selections = merged


class SurroundManager:
    """Manage surround operations (add, change, delete surrounds)."""
    
    PAIRS = {
        '(': ('(', ')'),
        ')': ('(', ')'),
        '[': ('[', ']'),
        ']': ('[', ']'),
        '{': ('{', '}'),
        '}': ('{', '}'),
        '<': ('<', '>'),
        '>': ('<', '>'),
        '"': ('"', '"'),
        "'": ("'", "'"),
        '`': ('`', '`'),
        't': ('<', '>'),  # HTML tag
    }
    
    def __init__(self):
        self.text_object_finder = TextObjectFinder()
    
    def add_surround(self, content: str, selection: Selection, surround_char: str) -> str:
        """Add surrounding characters around selection."""
        if surround_char not in self.PAIRS:
            # Use the character directly for both sides
            open_char = close_char = surround_char
        else:
            open_char, close_char = self.PAIRS[surround_char]
        
        # Handle tag specially
        if surround_char == 't':
            tag_content = content[selection.start:selection.end]
            return (
                content[:selection.start] +
                f'<tag>{tag_content}</tag>' +
                content[selection.end:]
            )
        
        return (
            content[:selection.start] +
            open_char +
            content[selection.start:selection.end] +
            close_char +
            content[selection.end:]
        )
    
    def delete_surround(self, content: str, selection: Selection, surround_char: str) -> str:
        """Delete surrounding characters."""
        # Find the surrounding pair
        bounds = self.text_object_finder.find_object(
            content, selection.head, surround_char, inner=False
        )
        
        if not bounds:
            return content
        
        # Remove the delimiters
        return (
            content[:bounds[0]] +
            content[bounds[0] + 1:bounds[1] - 1] +
            content[bounds[1]:]
        )
    
    def change_surround(self, content: str, selection: Selection, 
                       old_char: str, new_char: str) -> str:
        """Change surrounding characters."""
        # Find the old surround
        bounds = self.text_object_finder.find_object(
            content, selection.head, old_char, inner=False
        )
        
        if not bounds:
            return content
        
        # Get new surround chars
        if new_char not in self.PAIRS:
            new_open = new_close = new_char
        else:
            new_open, new_close = self.PAIRS[new_char]
        
        # Replace
        inner_content = content[bounds[0] + 1:bounds[1] - 1]
        return (
            content[:bounds[0]] +
            new_open +
            inner_content +
            new_close +
            content[bounds[1]:]
        )


class HelixFeatures:
    """
    Helix-inspired editor features.
    
    Features:
    - Multiple cursors with C-n/C-o navigation
    - Selection-first editing model
    - Object selection (m, M, etc.)
    - Split selection (S)
    - Rotate selections
    - Extended selection operations
    """
    
    def __init__(self):
        self.multi_cursor = MultiCursorManager()
        self.surround = SurroundManager()
        self.text_objects = TextObjectFinder()
    
    def select_object(self, content: str, obj_type: str, inner: bool = True) -> None:
        """Select text object."""
        self.multi_cursor.select_text_object(content, obj_type, inner)
    
    def split_selection(self, content: str, pattern: str = r'\s+') -> None:
        """Split selection by pattern."""
        self.multi_cursor.split_selection_by_regex(content, pattern)
    
    def split_selection_lines(self, content: str) -> None:
        """Split selection by lines."""
        self.multi_cursor.split_selection_by_line(content)
    
    def add_cursor_vertical(self, content: str, direction: int = 1) -> None:
        """Add cursor above (direction=-1) or below (direction=1)."""
        if direction > 0:
            self.multi_cursor.add_cursor_below(content)
        else:
            self.multi_cursor.add_cursor_above(content)
    
    def get_selection_contents(self, content: str) -> List[str]:
        """Get content of all selections."""
        return [content[sel.start:sel.end] for sel in self.multi_cursor.selections]
    
    def apply_to_selections(self, content: str, transform: Callable[[str], str]) -> str:
        """Apply a transformation to all selections."""
        # Sort selections by position (descending) to avoid offset issues
        sorted_sels = sorted(
            self.multi_cursor.selections,
            key=lambda s: s.start,
            reverse=True
        )
        
        for sel in sorted_sels:
            old_text = content[sel.start:sel.end]
            new_text = transform(old_text)
            content = content[:sel.start] + new_text + content[sel.end:]
            
            # Update selection end position
            sel.head = sel.start + len(new_text)
        
        return content


class NeovimFeatures:
    """
    Neovim-inspired editor features.
    
    Features:
    - LSP integration support
    - Tree-sitter based highlighting
    - Lua scripting support
    - Floating windows
    - Status line integration
    - Completion framework
    """
    
    def __init__(self):
        self.lsp_clients: dict = {}
        self.treesitter_parsers: dict = {}
        self.lua_state = None
        self.completion_items: List[dict] = []
        self.diagnostics: List[dict] = []
        self.status_line_components: List[Callable] = []
    
    def get_status_line(self) -> str:
        """Generate status line string."""
        components = []
        for comp in self.status_line_components:
            components.append(comp())
        return " | ".join(components)
    
    def add_diagnostic(self, line: int, col: int, message: str, severity: str = "error") -> None:
        """Add a diagnostic message."""
        self.diagnostics.append({
            "line": line,
            "col": col,
            "message": message,
            "severity": severity,
        })
    
    def clear_diagnostics(self) -> None:
        """Clear all diagnostics."""
        self.diagnostics.clear()
    
    def get_diagnostics_for_line(self, line: int) -> List[dict]:
        """Get diagnostics for a specific line."""
        return [d for d in self.diagnostics if d["line"] == line]
    
    def set_completion_items(self, items: List[dict]) -> None:
        """Set completion items."""
        self.completion_items = items
    
    def filter_completions(self, prefix: str) -> List[dict]:
        """Filter completion items by prefix."""
        if not prefix:
            return self.completion_items
        return [
            item for item in self.completion_items
            if item.get("label", "").lower().startswith(prefix.lower())
        ]


# Export classes
__all__ = [
    'Selection',
    'SelectionDirection', 
    'TextObject',
    'TextObjectFinder',
    'MultiCursorManager',
    'SurroundManager',
    'HelixFeatures',
    'NeovimFeatures',
]
