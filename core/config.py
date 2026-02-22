"""
Configuration management for MarkMark.
Handles user preferences, keybindings, themes, and editor settings.
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from enum import Enum


class EditorMode(Enum):
    NORMAL = "normal"
    INSERT = "insert"
    VISUAL = "visual"
    VISUAL_LINE = "visual_line"
    VISUAL_BLOCK = "visual_block"
    COMMAND = "command"
    REPLACE = "replace"


class ThemeType(Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


@dataclass
class VimConfig:
    """Vim-mode specific configuration."""
    enabled: bool = True
    relative_line_numbers: bool = True
    show_mode_indicator: bool = True
    hjkl_navigation: bool = True
    esc_escape: bool = True
    leader_key: str = "space"
    timeout_ms: int = 1000
    show_command_buffer: bool = True
    highlight_search: bool = True
    incremental_search: bool = True
    smart_case: bool = True
    ignore_case: bool = True
    wrap_scan: bool = True
    
    # Movement settings
    scrolloff: int = 5
    sidescrolloff: int = 5
    
    # Indentation
    autoindent: bool = True
    expandtab: bool = True
    shiftwidth: int = 4
    tabstop: int = 4
    softtabstop: int = 4


@dataclass
class ZenConfig:
    """Zen-mode specific configuration."""
    enabled: bool = False
    hide_menu_bar: bool = True
    hide_status_bar: bool = True
    hide_sidebar: bool = True
    hide_line_numbers: bool = False
    hide_minimap: bool = True
    center_text: bool = True
    max_line_width: int = 80
    background_opacity: float = 1.0
    typography_mode: bool = True
    focus_current_paragraph: bool = True
    ambient_typography: bool = True


@dataclass
class EditorConfig:
    """General editor configuration."""
    font_family: str = "JetBrains Mono"
    font_size: int = 12
    line_height: float = 1.5
    show_line_numbers: bool = True
    show_minimap: bool = True
    minimap_width: int = 100
    word_wrap: bool = True
    tab_width: int = 4
    indent_with_spaces: bool = True
    auto_save: bool = True
    auto_save_delay_ms: int = 2000
    highlight_current_line: bool = True
    show_whitespace: bool = False
    bracket_matching: bool = True
    auto_brackets: bool = True
    spell_check: bool = True
    spell_language: str = "en_US"
    show_indent_guides: bool = True
    cursor_blink: bool = True
    cursor_blink_timeout: int = 1200
    
    # File handling
    encoding: str = "utf-8"
    backup_enabled: bool = True
    backup_suffix: str = "~"
    swap_file_enabled: bool = True
    
    # Undo/Redo
    undo_limit: int = 1000
    undo_memory_limit_mb: int = 100


@dataclass
class MarkdownConfig:
    """Markdown-specific configuration."""
    live_preview: bool = True
    preview_side: str = "right"  # left, right, bottom
    syntax_highlight_code_blocks: bool = True
    render_math: bool = True
    math_engine: str = "katex"  # katex, mathjax
    render_mermaid: bool = True
    render_diagrams: bool = True
    auto_complete_links: bool = True
    smart_paste: bool = True
    toc_enabled: bool = True
    toc_depth: int = 3
    
    # Export options
    export_format: str = "html"
    pdf_engine: str = "wkhtmltopdf"
    include_css_in_export: bool = True


@dataclass
class HelixConfig:
    """Helix-inspired features configuration."""
    multi_cursor_enabled: bool = True
    object_selection: bool = True  # ci", di", etc.
    surround_enabled: bool = True
    textobjects_enabled: bool = True
    
    # Multiple cursors
    primary_cursor_style: str = "block"
    secondary_cursor_style: str = "underline"
    
    # Selection
    extend_line: bool = True
    keep_primary_selection: bool = True


@dataclass
class NeovimConfig:
    """Neovim-inspired features configuration."""
    lsp_enabled: bool = True
    treesitter_enabled: bool = True
    completion_enabled: bool = True
    completion_trigger_delay: int = 300
    
    # Lua scripting
    lua_enabled: bool = True
    
    # Status line
    status_line_style: str = "fancy"  # simple, fancy
    
    # Floating windows
    floating_border: str = "rounded"  # single, double, rounded, solid


@dataclass
class NoteConfig:
    """Note-taking system configuration."""
    notes_directory: str = ""
    auto_organize: bool = True
    organize_by: str = "date"  # date, category, tag
    default_category: str = "General"
    
    # Search
    search_in_content: bool = True
    fuzzy_search: bool = True
    search_history_limit: int = 50
    
    # Tags
    tag_format: str = "#tag"
    tag_completion: bool = True
    
    # Links
    wiki_links: bool = True
    wiki_link_format: str = "[[note-name]]"
    
    # Templates
    default_template: str = ""
    auto_insert_date: bool = True
    date_format: str = "%Y-%m-%d %H:%M"


@dataclass
class CLIConfig:
    """CLI mode configuration."""
    colors_enabled: bool = True
    pager: str = "less"
    editor_fallback: str = "nano"
    prompt_style: str = "fancy"  # simple, fancy
    history_file: str = ""
    history_limit: int = 1000
    
    # Keybindings
    emacs_bindings: bool = False
    vi_bindings: bool = True


@dataclass
class PluginConfig:
    """Plugin system configuration."""
    enabled: bool = True
    auto_load: bool = True
    plugin_directory: str = ""
    disabled_plugins: List[str] = field(default_factory=list)


@dataclass
class KeyBinding:
    """A single keybinding definition."""
    key: str
    action: str
    mode: str = "all"  # all, normal, insert, visual
    description: str = ""


@dataclass
class AppConfig:
    """Main application configuration."""
    vim: VimConfig = field(default_factory=VimConfig)
    zen: ZenConfig = field(default_factory=ZenConfig)
    editor: EditorConfig = field(default_factory=EditorConfig)
    markdown: MarkdownConfig = field(default_factory=MarkdownConfig)
    helix: HelixConfig = field(default_factory=HelixConfig)
    neovim: NeovimConfig = field(default_factory=NeovimConfig)
    notes: NoteConfig = field(default_factory=NoteConfig)
    cli: CLIConfig = field(default_factory=CLIConfig)
    plugins: PluginConfig = field(default_factory=PluginConfig)
    
    # Keybindings
    keybindings: Dict[str, Any] = field(default_factory=dict)
    
    # Window state
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    sidebar_visible: bool = True
    sidebar_width: int = 250
    panel_height: int = 200
    
    # Session
    restore_session: bool = True
    recent_files_limit: int = 20
    recent_files: List[str] = field(default_factory=list)
    
    # Theme
    theme: ThemeType = ThemeType.DARK
    custom_theme_path: str = ""


class ConfigManager:
    """Manages application configuration persistence."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or self._get_default_config_dir()
        self.config_file = self.config_dir / "config.json"
        self.config: AppConfig = AppConfig()
        self._ensure_config_dir()
        self.load()
        self._init_default_keybindings()
    
    def _get_default_config_dir(self) -> Path:
        """Get the default configuration directory."""
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "markmark"
        return Path.home() / ".config" / "markmark"
    
    def _ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_default_keybindings(self) -> None:
        """Initialize default keybindings."""
        if self.config.keybindings:
            return
            
        self.config.keybindings = {
            # Global
            "global": {
                "Ctrl+n": "new_file",
                "Ctrl+o": "open_file",
                "Ctrl+s": "save_file",
                "Ctrl+Shift+s": "save_file_as",
                "Ctrl+q": "quit",
                "Ctrl+w": "close_tab",
                "Ctrl+Tab": "next_tab",
                "Ctrl+Shift+Tab": "prev_tab",
                "Ctrl+z": "undo",
                "Ctrl+Shift+z": "redo",
                "Ctrl+f": "find",
                "Ctrl+h": "find_replace",
                "Ctrl+g": "goto_line",
                "F11": "toggle_fullscreen",
                "Ctrl+Shift+P": "command_palette",
                "Ctrl+`": "toggle_terminal",
            },
            # Vim Normal mode
            "normal": {
                "i": "enter_insert_mode",
                "a": "insert_after",
                "I": "insert_line_start",
                "A": "insert_line_end",
                "o": "insert_line_below",
                "O": "insert_line_above",
                "v": "enter_visual_mode",
                "V": "enter_visual_line_mode",
                "Ctrl+v": "enter_visual_block_mode",
                "d": "delete",
                "dd": "delete_line",
                "D": "delete_to_end",
                "c": "change",
                "cc": "change_line",
                "C": "change_to_end",
                "y": "yank",
                "yy": "yank_line",
                "Y": "yank_to_end",
                "p": "paste_after",
                "P": "paste_before",
                "x": "delete_char",
                "X": "delete_char_before",
                "r": "replace_char",
                "R": "enter_replace_mode",
                "u": "undo",
                "Ctrl+r": "redo",
                ":": "enter_command_mode",
                "/": "search_forward",
                "?": "search_backward",
                "n": "search_next",
                "N": "search_prev",
                "*": "search_word_under_cursor",
                "#": "search_word_under_cursor_backward",
                "w": "word_forward",
                "W": "WORD_forward",
                "b": "word_backward",
                "B": "WORD_backward",
                "e": "word_end",
                "E": "WORD_end",
                "0": "line_start",
                "^": "first_non_whitespace",
                "$": "line_end",
                "gg": "file_start",
                "G": "file_end",
                "{": "paragraph_prev",
                "}": "paragraph_next",
                "%": "match_bracket",
                ">>": "indent_line",
                "<<": "unindent_line",
                "==": "auto_indent_line",
                "J": "join_lines",
                "zz": "center_cursor",
                "zt": "cursor_top",
                "zb": "cursor_bottom",
                "H": "screen_top",
                "M": "screen_middle",
                "L": "screen_bottom",
                "Ctrl+u": "half_page_up",
                "Ctrl+d": "half_page_down",
                "Ctrl+b": "page_up",
                "Ctrl+f": "page_down",
                "m": "set_mark",
                "'": "goto_mark_line",
                "`": "goto_mark_exact",
                ".": "repeat_last_command",
                ";": "repeat_find_forward",
                ",": "repeat_find_backward",
            },
            # Helix-inspired
            "helix": {
                "Ctrl+c": "copy_selection",
                "Ctrl+x": "cut_selection",
                "Ctrl+v": "paste_selection",
                "s": "select_mode",
                "S": "split_selection",
                "Ctrl+s": "split_selection_on_newline",
                ";": "collapse_selection",
                "Alt+;": "flip_selections",
                "%": "select_all",
                "x": "select_line",
                "X": "extend_line",
                "Alt+x": "select_line_above",
                "m": "match_mode",
                "M": "match_mode_inverse",
                "[": "object_select_start",
                "]": "object_select_end",
                "Alt+.": "object_select_inside",
                "Alt+,": "object_select_around",
            },
            # Markdown specific
            "markdown": {
                "Ctrl+b": "bold",
                "Ctrl+i": "italic",
                "Ctrl+k": "insert_link",
                "Ctrl+Shift+i": "insert_image",
                "Ctrl+Shift+c": "insert_code_block",
                "Ctrl+Shift+t": "insert_table",
                "Ctrl+1": "heading_1",
                "Ctrl+2": "heading_2",
                "Ctrl+3": "heading_3",
                "Ctrl+4": "heading_4",
                "Ctrl+5": "heading_5",
                "Ctrl+6": "heading_6",
                "Ctrl+p": "toggle_preview",
                "Ctrl+Shift+m": "toggle_minimap",
            },
        }
    
    def load(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                self._apply_config_data(data)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load config file: {e}")
    
    def _apply_config_data(self, data: dict) -> None:
        """Apply loaded configuration data."""
        for section, values in data.items():
            if hasattr(self.config, section):
                config_section = getattr(self.config, section)
                if hasattr(config_section, '__dataclass_fields__'):
                    for key, value in values.items():
                        if hasattr(config_section, key):
                            setattr(config_section, key, value)
                else:
                    setattr(self.config, section, values)
    
    def save(self) -> None:
        """Save configuration to file."""
        data = self._serialize_config()
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _serialize_config(self) -> dict:
        """Serialize configuration to dictionary."""
        data = {}
        for section in ['vim', 'zen', 'editor', 'markdown', 'helix', 
                       'neovim', 'notes', 'cli', 'plugins', 'keybindings',
                       'window_width', 'window_height', 'window_maximized',
                       'sidebar_visible', 'sidebar_width', 'panel_height',
                       'restore_session', 'recent_files_limit', 'recent_files']:
            value = getattr(self.config, section)
            if hasattr(value, '__dataclass_fields__'):
                data[section] = asdict(value)
            else:
                data[section] = value
        
        data['theme'] = self.config.theme.value
        return data
    
    def get_keybinding(self, context: str, action: str) -> Optional[str]:
        """Get the keybinding for an action in a context."""
        context_bindings = self.config.keybindings.get(context, {})
        for key, act in context_bindings.items():
            if act == action:
                return key
        return None
    
    def set_keybinding(self, context: str, key: str, action: str) -> None:
        """Set a keybinding."""
        if context not in self.config.keybindings:
            self.config.keybindings[context] = {}
        self.config.keybindings[context][key] = action
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self.config = AppConfig()
        self._init_default_keybindings()
        self.save()
    
    def add_recent_file(self, filepath: str) -> None:
        """Add a file to recent files list."""
        if filepath in self.config.recent_files:
            self.config.recent_files.remove(filepath)
        self.config.recent_files.insert(0, filepath)
        if len(self.config.recent_files) > self.config.recent_files_limit:
            self.config.recent_files = self.config.recent_files[:self.config.recent_files_limit]
    
    def get_notes_directory(self) -> Path:
        """Get the notes directory, creating it if necessary."""
        notes_dir = self.config.notes.notes_directory
        if not notes_dir:
            notes_dir = str(self.config_dir / "notes")
            self.config.notes.notes_directory = notes_dir
            self.save()
        
        path = Path(notes_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
