#!/usr/bin/env python3
"""
MarkMark - Advanced Markdown Multitool
A beautiful, harmonious GTK4-based markdown editor with Vim-mode, Zen-mode, and more.
Designed for writers, developers, and note-takers who appreciate good tools.
"""

import sys
import os

# Add the script directory to Python path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import re
import json
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('GtkSource', '5')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gdk, Gio, GLib, Pango, GObject
try:
    from gi.repository import GtkSource
    HAS_GTKSOURCE = True
except ImportError:
    HAS_GTKSOURCE = False

try:
    from gi.repository import Adw
    HAS_ADW = True
except ImportError:
    HAS_ADW = False

try:
    gi.require_version('Vte', '3.91')
    from gi.repository import Vte
    HAS_VTE = True
except (ImportError, ValueError):
    HAS_VTE = False

# Import our modules
from core.config import ConfigManager, AppConfig, EditorMode, ThemeType
from core.vim_mode import VimMode
from core.helix_mode import HelixFeatures
from core.zen_mode import ZenMode
from core.markdown_processor import MarkdownRenderer
from core.notes import NoteManager
from core.plugin_system import PluginManager, HookType
from core.cli_mode import CLIMode, create_parser


# =============================================================================
# ENHANCED CSS STYLING - Harmonious & Beautiful
# =============================================================================

APP_CSS = '''
/* ===========================================================================
   MARKMARK - Premium Dark Theme
   A harmonious, carefully crafted design system for focused writing
   =========================================================================== */

/* -- Base Window ---------------------------------------------------------- */
window {
    background-color: @bg_color;
    color: @text_color;
}

window.background {
    background-color: @bg_color;
}

/* -- Header Bar ----------------------------------------------------------- */
headerbar {
    background: linear-gradient(to bottom, @headerbar_bg 0%, shade(@headerbar_bg, 0.97) 100%);
    border-bottom: 1px solid @border_color;
    padding: 6px 12px;
    min-height: 46px;
}

headerbar label {
    font-weight: 500;
    color: @text_color;
}

headerbar .title {
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.3px;
    color: @text_color;
}

/* -- Editor Area ---------------------------------------------------------- */
.source-view {
    font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', 'Cascadia Code', Consolas, monospace;
    font-size: 14px;
    line-height: 1.7;
    letter-spacing: 0.2px;
    padding: 20px 24px;
    background-color: @bg_color;
    color: @text_color;
    caret-color: @accent_color;
}

.source-view text {
    background-color: @bg_color;
    color: @text_color;
}

.source-view:selected {
    background-color: @selection_bg;
    color: @selection_fg;
}

.source-view cursor {
    background-color: @accent_color;
    min-width: 2px;
}

/* Current line highlight */
.source-view .current-line-number {
    background-color: @hover_bg;
}

/* Line Numbers - elegant styling */
.source-view gutter {
    background-color: @sidebar_bg;
    padding-right: 4px;
}

.source-view gutter line {
    color: @dim_text;
    font-size: 12px;
    padding-right: 12px;
    padding-left: 12px;
}

/* Gutter renderer */
textview gutter {
    background-color: @sidebar_bg;
}

/* -- Text View Base -------------------------------------------------------- */
textview {
    background-color: @bg_color;
    color: @text_color;
}

textview text {
    background-color: @bg_color;
    color: @text_color;
    font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
}

textview:selected {
    background-color: @selection_bg;
    color: @selection_fg;
}

/* -- Preview - Prose styling ----------------------------------------------─ */
.preview-view {
    background-color: @bg_color;
    color: @text_color;
}

.preview-view text {
    font-family: 'Inter', 'SF Pro Text', 'Segoe UI', 'Noto Sans', sans-serif;
    font-size: 15px;
    line-height: 1.8;
    letter-spacing: 0.1px;
    padding: 32px 40px;
    background-color: @bg_color;
    color: @text_color;
}

.preview-view text selection {
    background-color: @selection_bg;
}

/* -- Sidebar - Elegant panel ----------------------------------------------─ */
.sidebar {
    background: linear-gradient(to right, @sidebar_bg 0%, shade(@sidebar_bg, 0.99) 100%);
    border-right: 1px solid @border_color;
}

.sidebar label {
    color: @text_color;
}

.sidebar .section-title {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: @dim_text;
    padding: 12px 16px 6px 16px;
}

.sidebar .file-item {
    padding: 8px 16px;
    border-radius: 8px;
    margin: 2px 8px;
    color: @text_color;
    transition: background-color 0.15s ease;
}

.sidebar .file-item:hover {
    background-color: @hover_bg;
}

.sidebar entry {
    margin: 8px 12px;
    border-radius: 10px;
    color: @text_color;
    background-color: @bg_color;
    border: 1px solid @border_color;
    padding: 8px 12px;
}

.sidebar entry text {
    color: @text_color;
    background-color: transparent;
}

/* -- ListView - Clean rows ------------------------------------------------─ */
listview {
    background-color: transparent;
    color: @text_color;
}

listview row {
    color: @text_color;
    background-color: transparent;
    padding: 6px 8px;
    border-radius: 6px;
    margin: 1px 4px;
    transition: background-color 0.12s ease;
}

listview row:hover {
    background-color: @hover_bg;
}

listview row:hover active {
    background-color: @accent_color;
}

listview row label {
    color: @text_color;
}

/* -- Status Bar - Informative footer --------------------------------------─ */
.statusbar {
    background: linear-gradient(to top, @statusbar_bg 0%, shade(@statusbar_bg, 1.02) 100%);
    border-top: 1px solid @border_color;
    padding: 6px 16px;
    font-size: 12px;
}

.statusbar label {
    color: @dim_text;
    font-family: 'JetBrains Mono', 'Fira Mono', monospace;
    font-size: 11px;
    font-weight: 500;
}

.statusbar .separator {
    color: @border_color;
    margin: 0 12px;
}

/* Mode indicator - prominent styling */
.mode-label {
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.5px;
    padding: 4px 10px;
    border-radius: 6px;
}

.mode-normal { 
    background: linear-gradient(135deg, alpha(@accent_color, 0.25) 0%, alpha(@accent_color, 0.15) 100%);
    color: @accent_color;
    border: 1px solid alpha(@accent_color, 0.3);
}
.mode-insert { 
    background: linear-gradient(135deg, alpha(@green, 0.25) 0%, alpha(@green, 0.15) 100%);
    color: @green;
    border: 1px solid alpha(@green, 0.3);
}
.mode-visual { 
    background: linear-gradient(135deg, alpha(@purple, 0.25) 0%, alpha(@purple, 0.15) 100%);
    color: @purple;
    border: 1px solid alpha(@purple, 0.3);
}
.mode-command { 
    background: linear-gradient(135deg, alpha(@orange, 0.25) 0%, alpha(@orange, 0.15) 100%);
    color: @orange;
    border: 1px solid alpha(@orange, 0.3);
}

/* -- Buttons - Modern interactive elements ---------------------------------- */
button {
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 500;
    transition: all 0.12s ease;
}

button label {
    color: @text_color;
}

button:hover {
    background-color: @hover_bg;
}

button:active {
    background-color: @accent_color;
    color: @bg_color;
}

button.flat {
    background: transparent;
    border: none;
}

button.flat:hover {
    background-color: @hover_bg;
}

button.suggested-action {
    background: linear-gradient(135deg, @accent_color 0%, shade(@accent_color, 0.9) 100%);
    color: @bg_color;
    border: none;
}

button.suggested-action:hover {
    background: linear-gradient(135deg, shade(@accent_color, 1.1) 0%, @accent_color 100%);
}

/* -- Entry widgets --------------------------------------------------------─ */
entry {
    color: @text_color;
    background-color: @bg_color;
    border: 1px solid @border_color;
    border-radius: 8px;
    padding: 8px 12px;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

entry:focus {
    border-color: @accent_color;
    box-shadow: 0 0 0 2px alpha(@accent_color, 0.15);
}

entry text {
    color: @text_color;
    background-color: transparent;
}

/* -- Labels ---------------------------------------------------------------- */
label {
    color: @text_color;
}

.title-1 {
    font-size: 24px;
    font-weight: 700;
    color: @text_color;
}

.title-2 {
    font-size: 18px;
    font-weight: 600;
    color: @text_color;
}

.title-3 {
    font-size: 16px;
    font-weight: 600;
    color: @text_color;
}

.title-4 {
    font-size: 14px;
    font-weight: 600;
    color: @text_color;
}

.heading {
    font-weight: 600;
    color: @text_color;
}

.caption {
    font-size: 12px;
    color: @dim_text;
}

/* -- Command Palette - Spotlight-style overlay ----------------------------─ */
.command-palette {
    background-color: @popover_bg;
    border-radius: 16px;
    border: 1px solid @border_color;
    box-shadow: 0 24px 48px rgba(0, 0, 0, 0.4), 0 8px 16px rgba(0, 0, 0, 0.2);
    padding: 0;
}

.command-palette entry {
    font-size: 16px;
    padding: 16px 20px;
    border: none;
    border-bottom: 1px solid @border_color;
    border-radius: 16px 16px 0 0;
    background-color: @popover_bg;
    color: @text_color;
}

.command-palette entry:focus {
    border-color: @border_color;
    box-shadow: none;
}

.command-palette listview {
    padding: 8px;
    max-height: 400px;
}

.command-palette row {
    padding: 12px 16px;
    border-radius: 10px;
    margin: 2px 0;
}

.command-palette row:hover {
    background-color: @hover_bg;
}

.command-palette row:selected {
    background-color: alpha(@accent_color, 0.15);
}

.command-palette .command-shortcut {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: @dim_text;
    background-color: alpha(@dim_text, 0.1);
    padding: 3px 8px;
    border-radius: 4px;
}

/* -- Scrollbar - Minimal, elegant ------------------------------------------─ */
scrollbar {
    background-color: transparent;
}

scrollbar slider {
    background-color: @scrollbar_bg;
    border-radius: 4px;
    min-width: 10px;
    min-height: 10px;
    margin: 2px;
}

scrollbar slider:hover {
    background-color: @scrollbar_hover;
}

/* -- Paned separator ------------------------------------------------------─ */
paned > separator {
    background-color: @border_color;
    min-width: 1px;
}

paned > separator:hover {
    background-color: @accent_color;
}

/* -- Tab Bar --------------------------------------------------------------─ */
notebook tab {
    padding: 10px 18px;
    border-radius: 8px 8px 0 0;
}

notebook tab label {
    color: @dim_text;
}

notebook tab:checked {
    background-color: @bg_color;
}

notebook tab:checked label {
    color: @text_color;
    font-weight: 600;
}

/* -- Popover - Elevated surface --------------------------------------------─ */
popover {
    background-color: @popover_bg;
    border-radius: 12px;
    border: 1px solid @border_color;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

popover label {
    color: @text_color;
}

popover menuitem {
    padding: 8px 12px;
    border-radius: 6px;
}

popover menuitem:hover {
    background-color: @hover_bg;
}

/* -- Separator ------------------------------------------------------------─ */
separator {
    background-color: @border_color;
    min-height: 1px;
    min-width: 1px;
}

separator.horizontal {
    margin: 8px 0;
}

separator.vertical {
    margin: 0 8px;
}

/* -- Zen Mode - Distraction-free writing ----------------------------------─ */
.zen-mode {
    background-color: @bg_color;
}

.zen-mode .source-view {
    font-size: 17px;
    line-height: 2.0;
    letter-spacing: 0.3px;
    padding: 80px 15%;  /* Centered with percentage padding */
}

.zen-mode headerbar {
    opacity: 0;
    transition: opacity 0.3s ease;
}

.zen-mode headerbar:hover {
    opacity: 1;
}

.zen-mode .statusbar {
    opacity: 0;
    transition: opacity 0.3s ease;
}

.zen-mode .statusbar:hover {
    opacity: 1;
}

/* -- Centered Editor Mode --------------------------------------------------─ */
.centered-editor {
    padding-left: 12%;
    padding-right: 12%;
}

.centered-editor text {
    padding-left: 0;
    padding-right: 0;
}

/* -- Terminal Panel -------------------------------------------------------- */
.terminal-panel {
    background-color: @sidebar_bg;
    border-top: 1px solid @border_color;
}

.terminal-header {
    background: linear-gradient(to bottom, @statusbar_bg 0%, shade(@statusbar_bg, 0.98) 100%);
    border-bottom: 1px solid @border_color;
    padding: 6px 12px;
}

.terminal-header label {
    color: @dim_text;
    font-size: 12px;
    font-weight: 600;
}

.terminal-widget {
    background-color: #0a0a0f;
    color: #e8e8e8;
    font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
    font-size: 13px;
    padding: 8px;
}

/* -- File type badges - Colorful indicators -------------------------------- */
.file-badge {
    font-size: 10px;
    padding: 3px 8px;
    border-radius: 6px;
    font-weight: 600;
    letter-spacing: 0.3px;
}

.badge-md { 
    background: linear-gradient(135deg, alpha(@blue, 0.25) 0%, alpha(@blue, 0.15) 100%);
    color: @blue;
    border: 1px solid alpha(@blue, 0.2);
}
.badge-py { 
    background: linear-gradient(135deg, alpha(@green, 0.25) 0%, alpha(@green, 0.15) 100%);
    color: @green;
    border: 1px solid alpha(@green, 0.2);
}
.badge-js { 
    background: linear-gradient(135deg, alpha(@yellow, 0.3) 0%, alpha(@yellow, 0.2) 100%);
    color: @yellow;
    border: 1px solid alpha(@yellow, 0.2);
}
.badge-html { 
    background: linear-gradient(135deg, alpha(@red, 0.25) 0%, alpha(@red, 0.15) 100%);
    color: @red;
    border: 1px solid alpha(@red, 0.2);
}
.badge-css { 
    background: linear-gradient(135deg, alpha(@accent_color, 0.25) 0%, alpha(@accent_color, 0.15) 100%);
    color: @accent_color;
    border: 1px solid alpha(@accent_color, 0.2);
}
.badge-json { 
    background: linear-gradient(135deg, alpha(@dim_text, 0.3) 0%, alpha(@dim_text, 0.2) 100%);
    color: @text_color;
    border: 1px solid alpha(@dim_text, 0.15);
}
.badge-sh { 
    background: linear-gradient(135deg, alpha(@green, 0.2) 0%, alpha(@green, 0.1) 100%);
    color: @green;
    border: 1px solid alpha(@green, 0.15);
}
.badge-rs { 
    background: linear-gradient(135deg, alpha(@orange, 0.3) 0%, alpha(@orange, 0.2) 100%);
    color: @orange;
    border: 1px solid alpha(@orange, 0.2);
}
.badge-go { 
    background: linear-gradient(135deg, alpha(@accent_color, 0.35) 0%, alpha(@accent_color, 0.25) 100%);
    color: @accent_color;
    border: 1px solid alpha(@accent_color, 0.25);
}

/* -- Resizable paned ------------------------------------------------------─ */
.bottom-paned > separator {
    background-color: @border_color;
    min-height: 4px;
}

.bottom-paned > separator:hover {
    background-color: @accent_color;
}

/* -- Terminal tabs ---------------------------------------------------------- */
.terminal-tabs button {
    padding: 6px 14px;
    min-height: 30px;
    border-radius: 6px;
}

.terminal-tabs button:checked {
    background-color: @hover_bg;
}

/* -- Toast/Notification styling --------------------------------------------─ */
.toast {
    background: linear-gradient(135deg, shade(@popover_bg, 1.05) 0%, @popover_bg 100%);
    border: 1px solid @border_color;
    border-radius: 10px;
    padding: 12px 16px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}

/* -- Modified indicator - Subtle but visible -------------------------------- */
.modified-indicator {
    color: @orange;
    font-size: 10px;
}

/* -- Icon styling ----------------------------------------------------------─ */
image {
    color: @dim_text;
}

button:hover image {
    color: @text_color;
}

/* -- Menu styling ----------------------------------------------------------─ */
menu menuitem label {
    color: @text_color;
}

menu menuitem {
    padding: 8px 12px;
    border-radius: 6px;
}

menu menuitem:hover {
    background-color: @hover_bg;
}

/* -- Tooltip styling -------------------------------------------------------- */
tooltip {
    background-color: @popover_bg;
    border: 1px solid @border_color;
    border-radius: 8px;
    padding: 8px 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

tooltip label {
    color: @text_color;
    font-size: 12px;
}

/* -- Focus ring for accessibility ------------------------------------------─ */
*:focus-visible {
    outline: 2px solid @accent_color;
    outline-offset: 2px;
}

/* -- Writing focus indicator ------------------------------------------------ */
.writing-focus {
    background-color: alpha(@accent_color, 0.03);
}
'''

# ===============================================================================
# THEME COLORS - Carefully crafted palettes
# ===============================================================================

# Dark theme - Catppuccin Mocha inspired with enhanced contrast
DARK_THEME = {
    'bg_color': '#1e1e2e',
    'sidebar_bg': '#181825',
    'headerbar_bg': '#1e1e2e',
    'statusbar_bg': '#181825',
    'text_color': '#e4e4ef',      # Soft white for comfortable reading
    'dim_text': '#7f849c',        # Muted but readable
    'accent_color': '#89b4fa',    # Soft blue
    'border_color': '#313244',
    'selection_bg': '#45475a',
    'selection_fg': '#ffffff',
    'hover_bg': '#313244',
    'popover_bg': '#1e1e2e',
    'scrollbar_bg': '#45475a',
    'scrollbar_hover': '#6c7086',
    'green': '#a6e3a1',
    'blue': '#89b4fa',
    'orange': '#fab387',
    'red': '#f38ba8',
    'yellow': '#f9e2af',
    'purple': '#cba6f7',
    'teal': '#94e2d5',
}

# Light theme - Clean and bright
LIGHT_THEME = {
    'bg_color': '#ffffff',
    'sidebar_bg': '#f8f9fa',
    'headerbar_bg': '#ffffff',
    'statusbar_bg': '#f8f9fa',
    'text_color': '#1e1e2e',
    'dim_text': '#6c7086',
    'accent_color': '#1e66f5',
    'border_color': '#e5e7eb',
    'selection_bg': '#bfdbfe',
    'selection_fg': '#1e1e2e',
    'hover_bg': '#f3f4f6',
    'popover_bg': '#ffffff',
    'scrollbar_bg': '#d1d5db',
    'scrollbar_hover': '#9ca3af',
    'green': '#059669',
    'blue': '#1e66f5',
    'orange': '#ea580c',
    'red': '#dc2626',
    'yellow': '#ca8a04',
    'purple': '#7c3aed',
    'teal': '#0d9488',
}


def apply_theme(widget, dark: bool = True):
    """Apply color theme to application with proper variable substitution."""
    theme = DARK_THEME if dark else LIGHT_THEME
    
    css = APP_CSS
    for key, value in theme.items():
        # Replace all variants of @variable (work with strings)
        css = css.replace(f'@{key};', f'{value};')
        css = css.replace(f'@{key} ', f'{value} ')
        css = css.replace(f'@{key},', f'{value},')
        css = css.replace(f'@{key})', f'{value})')
    
    provider = Gtk.CssProvider()
    # GTK4 requires bytes for load_from_data
    provider.load_from_data(css.encode('utf-8'))
    
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


# ===============================================================================
# FILE TYPE DETECTION
# ===============================================================================

FILE_TYPE_MAP = {
    # Markdown and text
    '.md': ('markdown', 'Markdown', 'text-x-generic-symbolic', 'badge-md'),
    '.markdown': ('markdown', 'Markdown', 'text-x-generic-symbolic', 'badge-md'),
    '.mdown': ('markdown', 'Markdown', 'text-x-generic-symbolic', 'badge-md'),
    '.mkd': ('markdown', 'Markdown', 'text-x-generic-symbolic', 'badge-md'),
    '.txt': ('text', 'Plain Text', 'text-x-generic-symbolic', None),
    '.rst': ('rst', 'reStructuredText', 'text-x-generic-symbolic', None),
    '.tex': ('latex', 'LaTeX', 'text-x-generic-symbolic', None),
    
    # Python
    '.py': ('python', 'Python', 'text-x-python-symbolic', 'badge-py'),
    '.pyw': ('python', 'Python', 'text-x-python-symbolic', 'badge-py'),
    '.pyi': ('python', 'Python', 'text-x-python-symbolic', 'badge-py'),
    '.pyx': ('cython', 'Cython', 'text-x-python-symbolic', 'badge-py'),
    
    # JavaScript/TypeScript
    '.js': ('javascript', 'JavaScript', 'text-x-javascript-symbolic', 'badge-js'),
    '.jsx': ('javascript', 'JSX', 'text-x-javascript-symbolic', 'badge-js'),
    '.ts': ('typescript', 'TypeScript', 'text-x-javascript-symbolic', 'badge-js'),
    '.tsx': ('typescript', 'TSX', 'text-x-javascript-symbolic', 'badge-js'),
    '.mjs': ('javascript', 'ES Module', 'text-x-javascript-symbolic', 'badge-js'),
    '.cjs': ('javascript', 'CommonJS', 'text-x-javascript-symbolic', 'badge-js'),
    
    # Web
    '.html': ('html', 'HTML', 'text-html-symbolic', 'badge-html'),
    '.htm': ('html', 'HTML', 'text-html-symbolic', 'badge-html'),
    '.css': ('css', 'CSS', 'text-css-symbolic', 'badge-css'),
    '.scss': ('scss', 'SCSS', 'text-css-symbolic', 'badge-css'),
    '.sass': ('sass', 'Sass', 'text-css-symbolic', 'badge-css'),
    '.less': ('less', 'Less', 'text-css-symbolic', 'badge-css'),
    '.vue': ('vue', 'Vue', 'text-html-symbolic', 'badge-html'),
    '.svelte': ('svelte', 'Svelte', 'text-html-symbolic', 'badge-html'),
    
    # Data formats
    '.json': ('json', 'JSON', 'application-json-symbolic', 'badge-json'),
    '.yaml': ('yaml', 'YAML', 'text-x-generic-symbolic', 'badge-json'),
    '.yml': ('yaml', 'YAML', 'text-x-generic-symbolic', 'badge-json'),
    '.toml': ('toml', 'TOML', 'text-x-generic-symbolic', 'badge-json'),
    '.xml': ('xml', 'XML', 'text-html-symbolic', 'badge-json'),
    '.csv': ('csv', 'CSV', 'text-x-generic-symbolic', None),
    
    # Shell and scripts
    '.sh': ('sh', 'Shell', 'text-x-script-symbolic', 'badge-sh'),
    '.bash': ('sh', 'Bash', 'text-x-script-symbolic', 'badge-sh'),
    '.zsh': ('sh', 'Zsh', 'text-x-script-symbolic', 'badge-sh'),
    '.fish': ('fish', 'Fish', 'text-x-script-symbolic', 'badge-sh'),
    '.ps1': ('powershell', 'PowerShell', 'text-x-script-symbolic', 'badge-sh'),
    '.lua': ('lua', 'Lua', 'text-x-script-symbolic', 'badge-sh'),
    '.php': ('php', 'PHP', 'text-x-php-symbolic', 'badge-sh'),
    '.rb': ('ruby', 'Ruby', 'text-x-ruby-symbolic', 'badge-sh'),
    '.pl': ('perl', 'Perl', 'text-x-script-symbolic', 'badge-sh'),
    '.pm': ('perl', 'Perl', 'text-x-script-symbolic', 'badge-sh'),
    
    # Systems programming
    '.c': ('c', 'C', 'text-x-c-symbolic', None),
    '.h': ('c', 'C Header', 'text-x-chdr-symbolic', None),
    '.cpp': ('cpp', 'C++', 'text-x-c++-symbolic', None),
    '.hpp': ('cpp', 'C++ Header', 'text-x-c++hdr-symbolic', None),
    '.cc': ('cpp', 'C++', 'text-x-c++-symbolic', None),
    '.cxx': ('cpp', 'C++', 'text-x-c++-symbolic', None),
    '.rs': ('rust', 'Rust', 'text-x-rust-symbolic', 'badge-rs'),
    '.go': ('go', 'Go', 'text-x-go-symbolic', 'badge-go'),
    '.zig': ('zig', 'Zig', 'text-x-generic-symbolic', 'badge-rs'),
    '.nim': ('nim', 'Nim', 'text-x-generic-symbolic', None),
    
    # Java/JVM
    '.java': ('java', 'Java', 'text-x-java-symbolic', None),
    '.kt': ('kotlin', 'Kotlin', 'text-x-java-symbolic', None),
    '.kts': ('kotlin', 'Kotlin Script', 'text-x-java-symbolic', None),
    '.scala': ('scala', 'Scala', 'text-x-java-symbolic', None),
    '.groovy': ('groovy', 'Groovy', 'text-x-java-symbolic', None),
    
    # Other languages
    '.ex': ('elixir', 'Elixir', 'text-x-generic-symbolic', None),
    '.exs': ('elixir', 'Elixir Script', 'text-x-generic-symbolic', None),
    '.erl': ('erlang', 'Erlang', 'text-x-generic-symbolic', None),
    '.hs': ('haskell', 'Haskell', 'text-x-generic-symbolic', None),
    '.ml': ('ocaml', 'OCaml', 'text-x-generic-symbolic', None),
    '.clj': ('clojure', 'Clojure', 'text-x-generic-symbolic', None),
    '.lisp': ('lisp', 'Lisp', 'text-x-generic-symbolic', None),
    '.r': ('r', 'R', 'text-x-generic-symbolic', None),
    '.R': ('r', 'R', 'text-x-generic-symbolic', None),
    '.swift': ('swift', 'Swift', 'text-x-generic-symbolic', None),
    '.dart': ('dart', 'Dart', 'text-x-generic-symbolic', None),
    
    # Config files
    '.ini': ('ini', 'INI', 'text-x-generic-symbolic', None),
    '.cfg': ('ini', 'Config', 'text-x-generic-symbolic', None),
    '.conf': ('ini', 'Config', 'text-x-generic-symbolic', None),
    '.env': ('ini', 'Environment', 'text-x-generic-symbolic', None),
    '.gitignore': ('gitignore', 'Git Ignore', 'text-x-generic-symbolic', None),
    '.dockerignore': ('dockerignore', 'Docker Ignore', 'text-x-generic-symbolic', None),
    'Dockerfile': ('dockerfile', 'Dockerfile', 'text-x-generic-symbolic', None),
    'Makefile': ('makefile', 'Makefile', 'text-x-generic-symbolic', None),
    
    # Markup
    '.svg': ('xml', 'SVG', 'image-svg-symbolic', None),
    '.qmd': ('markdown', 'Quarto', 'text-x-generic-symbolic', 'badge-md'),
    '.rmd': ('markdown', 'R Markdown', 'text-x-generic-symbolic', 'badge-md'),
    
    # Misc
    '.sql': ('sql', 'SQL', 'text-x-generic-symbolic', None),
    '.graphql': ('graphql', 'GraphQL', 'text-x-generic-symbolic', None),
    '.gql': ('graphql', 'GraphQL', 'text-x-generic-symbolic', None),
    '.proto': ('proto', 'Protocol Buffer', 'text-x-generic-symbolic', None),
    '.diff': ('diff', 'Diff', 'text-x-generic-symbolic', None),
    '.patch': ('diff', 'Patch', 'text-x-generic-symbolic', None),
}


def detect_file_type(filepath: str) -> Tuple[str, str, str, Optional[str]]:
    """Detect file type from path.
    
    Returns: (language_id, display_name, icon_name, badge_class)
    """
    if not filepath:
        return ('text', 'Plain Text', 'text-x-generic-symbolic', None)
    
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filepath)[1].lower()
    
    # Check for special filenames first
    if filename in FILE_TYPE_MAP:
        return FILE_TYPE_MAP[filename]
    
    # Check extension
    if ext in FILE_TYPE_MAP:
        return FILE_TYPE_MAP[ext]
    
    # Unknown file type
    return ('text', 'Plain Text', 'text-x-generic-symbolic', None)


# ===============================================================================
# COMMAND PALETTE
# ===============================================================================

class Command:
    """Represents a command in the palette."""
    
    def __init__(self, name: str, description: str, shortcut: str, callback, icon: str = None):
        self.name = name
        self.description = description
        self.shortcut = shortcut
        self.callback = callback
        self.icon = icon or 'system-run-symbolic'


class CommandPalette(Gtk.Box):
    """Spotlight-style command palette for quick actions."""
    
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.add_css_class('command-palette')
        self.set_size_request(480, -1)
        
        self.commands: List[Command] = []
        self._setup_commands()
        
        # Search entry
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Search commands...")
        self.search_entry.connect("changed", self._on_search_changed)
        self.search_entry.connect("activate", self._on_activate)
        self.append(self.search_entry)
        
        # Results list
        self.results_model = Gtk.StringList()
        self.results_list = Gtk.ListView()
        
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._setup_item)
        factory.connect("bind", self._bind_item)
        self.results_list.set_factory(factory)
        
        # Selection model
        self.selection = Gtk.SingleSelection(model=self.results_model)
        self.results_list.set_model(self.selection)
        
        # Scroll container
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(300)
        scroll.set_child(self.results_list)
        self.append(scroll)
        
        # Key controller for navigation
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_controller)
        
        # Initial population
        self._populate_results("")
        
        # Focus entry when shown
        self.connect("map", lambda _: self.search_entry.grab_focus())
    
    def _setup_commands(self):
        """Setup available commands."""
        # File commands
        self.add_command(Command(
            "New File", "Create a new file", "Ctrl+N",
            lambda: self.app._on_new(None, None), "document-new-symbolic"
        ))
        self.add_command(Command(
            "Open File", "Open an existing file", "Ctrl+O",
            lambda: self.app.open_file_dialog(), "folder-open-symbolic"
        ))
        self.add_command(Command(
            "Save File", "Save the current file", "Ctrl+S",
            lambda: self.app.save_file(), "document-save-symbolic"
        ))
        self.add_command(Command(
            "Save As", "Save file with a new name", "Ctrl+Shift+S",
            lambda: self.app.save_file_as_dialog(), "document-save-as-symbolic"
        ))
        
        # View commands
        self.add_command(Command(
            "Toggle Sidebar", "Show/hide the sidebar", "Ctrl+B",
            lambda: self.app._on_toggle_sidebar(None, None), "sidebar-show-symbolic"
        ))
        self.add_command(Command(
            "Toggle Preview", "Show/hide the preview panel", "",
            lambda: self.app._on_toggle_preview(None, None), "view-paged-symbolic"
        ))
        self.add_command(Command(
            "Toggle Terminal", "Show/hide the terminal", "Ctrl+Alt+T",
            lambda: self.app._on_toggle_terminal(None, None), "utilities-terminal-symbolic"
        ))
        self.add_command(Command(
            "Zen Mode", "Enter distraction-free writing", "F11",
            lambda: self.app._on_zen_mode(None, None), "preferences-desktop-screensaver-symbolic"
        ))
        
        # Edit commands
        self.add_command(Command(
            "Undo", "Undo last action", "Ctrl+Z",
            lambda: self.app._on_undo(None, None), "edit-undo-symbolic"
        ))
        self.add_command(Command(
            "Redo", "Redo last undone action", "Ctrl+Shift+Z",
            lambda: self.app._on_redo(None, None), "edit-redo-symbolic"
        ))
        
        # Vim commands
        self.add_command(Command(
            "Toggle Vim Mode", "Enable/disable Vim keybindings", "",
            self._toggle_vim_mode, "input-keyboard-symbolic"
        ))
        
        # Theme commands
        self.add_command(Command(
            "Toggle Theme", "Switch between dark and light theme", "",
            self._toggle_theme, "weather-clear-symbolic"
        ))
    
    def add_command(self, command: Command):
        """Add a command to the palette."""
        self.commands.append(command)
    
    def _populate_results(self, query: str):
        """Populate results based on search query."""
        self.results_model.splice(0, self.results_model.get_n_items(), [])
        self._filtered_commands = []
        
        query = query.lower().strip()
        for cmd in self.commands:
            if not query or query in cmd.name.lower() or query in cmd.description.lower():
                self.results_model.append(cmd.name)
                self._filtered_commands.append(cmd)
    
    def _setup_item(self, factory, item):
        """Setup a result item."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.set_spacing(12)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Icon
        icon = Gtk.Image()
        icon.set_pixel_size(20)
        box.append(icon)
        
        # Name and description
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        text_box.set_hexpand(True)
        
        name = Gtk.Label()
        name.set_halign(Gtk.Align.START)
        text_box.append(name)
        
        desc = Gtk.Label()
        desc.set_halign(Gtk.Align.START)
        desc.add_css_class('caption')
        text_box.append(desc)
        
        box.append(text_box)
        
        # Shortcut badge
        shortcut = Gtk.Label()
        shortcut.add_css_class('command-shortcut')
        box.append(shortcut)
        
        item.set_child(box)
    
    def _bind_item(self, factory, item):
        """Bind data to a result item."""
        box = item.get_child()
        icon = box.get_first_child()
        text_box = icon.get_next_sibling()
        name = text_box.get_first_child()
        desc = name.get_next_sibling()
        shortcut = box.get_last_child()
        
        idx = item.get_position()
        if idx < len(self._filtered_commands):
            cmd = self._filtered_commands[idx]
            icon.set_from_icon_name(cmd.icon)
            name.set_label(cmd.name)
            desc.set_label(cmd.description)
            shortcut.set_label(cmd.shortcut)
    
    def _on_search_changed(self, entry):
        """Handle search text change."""
        self._populate_results(entry.get_text())
    
    def _on_activate(self, entry):
        """Handle activation (Enter key)."""
        self._execute_selected()
    
    def _on_key_pressed(self, controller, keyval, keycode, state):
        """Handle key navigation."""
        key = Gdk.keyval_name(keyval)
        
        if key == "Escape":
            self.app._hide_command_palette()
            return True
        elif key == "Down" or key == "j" and state & Gdk.ModifierType.CONTROL_MASK:
            pos = self.selection.get_selected()
            if pos < self.results_model.get_n_items() - 1:
                self.selection.set_selected(pos + 1)
            return True
        elif key == "Up" or key == "k" and state & Gdk.ModifierType.CONTROL_MASK:
            pos = self.selection.get_selected()
            if pos > 0:
                self.selection.set_selected(pos - 1)
            return True
        elif key == "Return":
            self._execute_selected()
            return True
        
        return False
    
    def _execute_selected(self):
        """Execute the selected command."""
        pos = self.selection.get_selected()
        if pos < len(self._filtered_commands):
            cmd = self._filtered_commands[pos]
            self.app._hide_command_palette()
            if cmd.callback:
                cmd.callback()
    
    def _toggle_vim_mode(self):
        """Toggle Vim mode."""
        if self.app.config:
            self.app.config.vim.enabled = not self.app.config.vim.enabled
            self.app.config_manager.save()
    
    def _toggle_theme(self):
        """Toggle between dark and light theme."""
        if self.app.config:
            if self.app.config.theme == ThemeType.DARK:
                self.app.config.theme = ThemeType.LIGHT
            else:
                self.app.config.theme = ThemeType.DARK
            apply_theme(self.app.window, self.app.config.theme == ThemeType.DARK)
            self.app.config_manager.save()


# ===============================================================================
# TERMINAL PANEL
# ===============================================================================

class TerminalPanel(Gtk.Box):
    """Embedded terminal panel with multiple tabs support."""
    
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.add_css_class('terminal-panel')
        self.terminals = []
        self.current_terminal = None
        self.default_cwd = os.getcwd()
        
        # Header with tabs
        self.header = self._create_header()
        self.append(self.header)
        
        # Terminal container
        self.terminal_stack = Gtk.Stack()
        self.terminal_stack.set_vexpand(True)
        self.append(self.terminal_stack)
        
        # Add initial terminal
        self.add_terminal()
    
    def _create_header(self) -> Gtk.Widget:
        """Create terminal header with controls."""
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.add_css_class('terminal-header')
        header.set_spacing(4)
        
        # Tab switcher
        self.tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.tab_box.add_css_class('terminal-tabs')
        self.tab_box.set_spacing(2)
        header.append(self.tab_box)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header.append(spacer)
        
        # Add terminal button
        add_btn = Gtk.Button()
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.set_tooltip_text("New Terminal")
        add_btn.add_css_class('flat')
        add_btn.connect("clicked", lambda _: self.add_terminal())
        header.append(add_btn)
        
        # Clear button
        clear_btn = Gtk.Button()
        clear_btn.set_icon_name("edit-clear-symbolic")
        clear_btn.set_tooltip_text("Clear Terminal")
        clear_btn.add_css_class('flat')
        clear_btn.connect("clicked", self._on_clear_terminal)
        header.append(clear_btn)
        
        # Close button
        close_btn = Gtk.Button()
        close_btn.set_icon_name("window-close-symbolic")
        close_btn.set_tooltip_text("Close Terminal")
        close_btn.add_css_class('flat')
        close_btn.connect("clicked", self._on_close_terminal)
        header.append(close_btn)
        
        return header
    
    def add_terminal(self, working_dir: Optional[str] = None):
        """Add a new terminal tab."""
        # Create terminal widget
        if HAS_VTE:
            terminal = Vte.Terminal()
            terminal.add_css_class('terminal-widget')
            
            # Set font
            font_desc = Pango.FontDescription.from_string("JetBrains Mono 13")
            terminal.set_font(font_desc)
            
            # Set colors for dark theme
            terminal.set_color_background(Gdk.RGBA(0.04, 0.04, 0.06, 1.0))
            terminal.set_color_foreground(Gdk.RGBA(0.91, 0.91, 0.91, 1.0))
            
            # Spawn shell
            shell = os.environ.get('SHELL', '/bin/bash')
            cwd = working_dir or self.default_cwd
            
            try:
                terminal.spawn_async(
                    Vte.PtyFlags.DEFAULT,
                    cwd,
                    [shell],
                    None,
                    GLib.SpawnFlags.SEARCH_PATH_FROM_ENVP,
                    None,
                    -1,
                    None,
                    None
                )
            except Exception as e:
                print(f"Failed to spawn terminal: {e}")
        else:
            # Fallback: create a text view as placeholder
            terminal = Gtk.TextView()
            terminal.set_editable(True)
            terminal.set_wrap_mode(Gtk.WrapMode.WORD)
            terminal.add_css_class('terminal-widget')
            
            buf = terminal.get_buffer()
            buf.set_text("VTE terminal not available. Install libvte-2.91-gtk4 for terminal support.\n"
                        f"Working directory: {working_dir or self.default_cwd}\n")
        
        # Create scroll container
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(terminal)
        
        # Create terminal info
        terminal_id = f"terminal-{len(self.terminals)}"
        term_info = {
            'id': terminal_id,
            'widget': terminal,
            'scroll': scroll,
            'label': f"Terminal {len(self.terminals) + 1}"
        }
        self.terminals.append(term_info)
        
        # Add to stack
        self.terminal_stack.add_named(scroll, terminal_id)
        
        # Create tab button
        self._create_tab_button(term_info)
        
        # Switch to new terminal
        self.terminal_stack.set_visible_child_name(terminal_id)
        self.current_terminal = term_info
        
        # Focus terminal
        terminal.grab_focus()
    
    def _create_tab_button(self, term_info: dict):
        """Create tab button for terminal."""
        btn = Gtk.Button(label=term_info['label'])
        btn.add_css_class('flat')
        btn.connect("clicked", lambda _, t=term_info: self._switch_terminal(t))
        
        term_info['button'] = btn
        self.tab_box.append(btn)
    
    def _switch_terminal(self, term_info: dict):
        """Switch to a specific terminal."""
        self.terminal_stack.set_visible_child_name(term_info['id'])
        self.current_terminal = term_info
        term_info['widget'].grab_focus()
    
    def _on_clear_terminal(self, button):
        """Clear current terminal."""
        if self.current_terminal and HAS_VTE:
            terminal = self.current_terminal['widget']
            terminal.reset(True, True)
    
    def _on_close_terminal(self, button):
        """Close current terminal tab."""
        if len(self.terminals) <= 1:
            return  # Don't close the last terminal
        
        if self.current_terminal:
            term_info = self.current_terminal
            self.terminal_stack.remove(term_info['scroll'])
            self.tab_box.remove(term_info['button'])
            self.terminals.remove(term_info)
            
            # Switch to first terminal
            if self.terminals:
                self._switch_terminal(self.terminals[0])
    
    def set_working_directory(self, directory: str):
        """Set working directory for new terminals."""
        self.default_cwd = directory
    
    def focus(self):
        """Focus the current terminal."""
        if self.current_terminal:
            self.current_terminal['widget'].grab_focus()


# ===============================================================================
# EDITOR BUFFER
# ===============================================================================

class EditorBuffer:
    """Wrapper around text buffer with extended functionality."""
    
    def __init__(self, buffer: Gtk.TextBuffer):
        self.buffer = buffer
        self.file_path: Optional[str] = None
        self.modified: bool = False
        self.last_save_time: Optional[datetime] = None
    
    def get_text(self) -> str:
        """Get all buffer text."""
        start, end = self.buffer.get_bounds()
        return self.buffer.get_text(start, end, False)
    
    def set_text(self, text: str):
        """Set buffer text."""
        self.buffer.set_text(text)
    
    def get_cursor_position(self) -> int:
        """Get cursor position as character offset."""
        return self.buffer.props.cursor_position
    
    def set_cursor_position(self, position: int):
        """Set cursor position."""
        start = self.buffer.get_start_iter()
        start.forward_chars(min(position, self.buffer.get_char_count()))
        self.buffer.place_cursor(start)
    
    def insert_at_cursor(self, text: str):
        """Insert text at cursor position."""
        self.buffer.insert_at_cursor(text, len(text))
    
    def get_line_column(self) -> Tuple[int, int]:
        """Get current line and column (1-indexed)."""
        pos = self.get_cursor_position()
        text = self.get_text()[:pos]
        line = text.count('\n') + 1
        last_newline = text.rfind('\n')
        column = pos - last_newline if last_newline != -1 else pos + 1
        return line, column
    
    def goto_line(self, line: int):
        """Go to a specific line."""
        line = max(1, line)
        iterator = self.buffer.get_start_iter()
        iterator.forward_lines(line - 1)
        self.buffer.place_cursor(iterator)
        self.buffer.scroll_to_iter(iterator, 0.0, True, 0.5, 0.5)


# ===============================================================================
# MARKDOWN PREVIEW
# ===============================================================================

class MarkdownPreview(Gtk.Box):
    """Beautiful markdown preview widget with prose styling."""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.renderer = MarkdownRenderer()
        
        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.set_margin_start(16)
        header.set_margin_end(16)
        header.set_margin_top(12)
        header.set_margin_bottom(8)
        
        icon = Gtk.Image.new_from_icon_name("view-paged-symbolic")
        icon.set_pixel_size(18)
        header.append(icon)
        
        title = Gtk.Label(label="  Preview")
        title.add_css_class('title-4')
        header.append(title)
        
        self.append(header)
        
        # Separator
        self.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        
        # Preview area
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.preview = Gtk.TextView()
        self.preview.set_editable(False)
        self.preview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.preview.set_margin_start(32)
        self.preview.set_margin_end(32)
        self.preview.set_margin_top(24)
        self.preview.set_margin_bottom(24)
        self.preview.add_css_class('preview-view')
        
        scroll.set_child(self.preview)
        self.append(scroll)
    
    def render(self, markdown: str):
        """Render markdown to preview."""
        html_content = self.renderer.render(markdown)
        self.preview.get_buffer().set_text(html_content)


# ===============================================================================
# EDITOR VIEW
# ===============================================================================

class EditorView(Gtk.Box):
    """Main editor view with beautiful, focused styling."""
    
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.current_file_type = ('text', 'Plain Text', 'text-x-generic-symbolic', None)
        self.lang_manager = None
        
        # Expand to fill available space
        self.set_vexpand(True)
        self.set_hexpand(True)
        
        # Create paned layout for editor and preview
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.paned.set_position(700)
        self.paned.set_wide_handle(False)
        self.paned.set_vexpand(True)
        self.paned.set_hexpand(True)
        
        # Editor side
        editor_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        editor_box.set_vexpand(True)
        editor_box.set_hexpand(True)
        
        # Editor header
        editor_header = self._create_editor_header()
        editor_box.append(editor_header)
        
        # Editor scroll
        editor_scroll = Gtk.ScrolledWindow()
        editor_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        editor_scroll.set_vexpand(True)
        editor_scroll.set_hexpand(True)
        
        # Create source view
        if HAS_GTKSOURCE:
            self.source_buffer = GtkSource.Buffer()
            self.source_view = GtkSource.View(buffer=self.source_buffer)
            self.source_view.set_show_line_numbers(True)
            self.source_view.set_highlight_current_line(True)
            self.source_view.set_auto_indent(True)
            self.source_view.set_indent_width(4)
            self.source_view.set_tab_width(4)
            self.source_view.set_insert_spaces_instead_of_tabs(True)
            self.source_view.set_smart_backspace(True)
            self.source_view.set_monospace(True)
            
            # Store language manager
            self.lang_manager = GtkSource.LanguageManager.get_default()
            
            # Setup style scheme
            style_manager = GtkSource.StyleSchemeManager.get_default()
            is_dark = app.config.theme == ThemeType.DARK
            dark_schemes = ["builder-dark", "oblivion", "solarized-dark", "kate-dark", "Adwaita-dark"]
            scheme_name = "Adwaita"
            if is_dark:
                for scheme in dark_schemes:
                    if style_manager.get_scheme(scheme):
                        scheme_name = scheme
                        break
            style = style_manager.get_scheme(scheme_name)
            if style:
                self.source_buffer.set_style_scheme(style)
        else:
            self.source_buffer = Gtk.TextBuffer()
            self.source_view = Gtk.TextView(buffer=self.source_buffer)
            self.source_view.set_monospace(True)
        
        self.source_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.source_view.set_vexpand(True)
        self.source_view.set_hexpand(True)
        self.source_view.add_css_class('source-view')
        self.source_view.set_size_request(400, 300)
        
        # Connect signals
        self.source_buffer.connect("changed", self._on_buffer_changed)
        
        # Setup key event controller for GTK4
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.source_view.add_controller(key_controller)
        
        editor_scroll.set_child(self.source_view)
        editor_box.append(editor_scroll)
        
        # Preview side - hidden by default
        self.preview = MarkdownPreview()
        self.preview.set_visible(False)
        
        # Add to paned
        self.paned.set_start_child(editor_box)
        self.paned.set_end_child(self.preview)
        self.paned.set_resize_start_child(True)
        self.paned.set_resize_end_child(False)
        self.paned.set_shrink_start_child(False)
        self.paned.set_shrink_end_child(True)
        
        self.append(self.paned)
        
        # Create buffer wrapper
        self.editor_buffer = EditorBuffer(self.source_buffer)
    
    def _create_editor_header(self) -> Gtk.Widget:
        """Create editor header with file info."""
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.set_margin_start(16)
        header.set_margin_end(16)
        header.set_margin_top(10)
        header.set_margin_bottom(10)
        header.set_spacing(10)
        
        # File icon
        self.file_icon = Gtk.Image.new_from_icon_name("text-x-generic-symbolic")
        self.file_icon.set_pixel_size(18)
        header.append(self.file_icon)
        
        # File name label
        self.file_label = Gtk.Label(label="Untitled")
        self.file_label.add_css_class('heading')
        header.append(self.file_label)
        
        # File type badge
        self.file_type_badge = Gtk.Label(label="Plain Text")
        self.file_type_badge.add_css_class('file-badge')
        header.append(self.file_type_badge)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header.append(spacer)
        
        # Modified indicator
        self.modified_dot = Gtk.Label(label="●")
        self.modified_dot.add_css_class('modified-indicator')
        self.modified_dot.set_visible(False)
        header.append(self.modified_dot)
        
        return header
    
    def _on_buffer_changed(self, buffer):
        """Handle buffer changes."""
        self.editor_buffer.modified = True
        self.modified_dot.set_visible(True)
        
        # Update preview
        if self.app.config.markdown.live_preview:
            text = self.editor_buffer.get_text()
            self.preview.render(text)
        
        # Update status bar
        self.app.update_status()
        
        # Trigger auto-save
        if self.app.config.editor.auto_save:
            self._schedule_auto_save()
    
    def _schedule_auto_save(self):
        """Schedule auto-save."""
        if hasattr(self, '_auto_save_id'):
            GLib.source_remove(self._auto_save_id)
        
        self._auto_save_id = GLib.timeout_add(
            self.app.config.editor.auto_save_delay_ms,
            self._auto_save
        )
    
    def _auto_save(self) -> bool:
        """Perform auto-save."""
        if self.editor_buffer.file_path and self.editor_buffer.modified:
            self.app.save_file()
        return False
    
    def _on_key_pressed(self, controller, keyval, keycode, state) -> bool:
        """Handle key press events."""
        # Command palette shortcut (Ctrl+Shift+P or Ctrl+P)
        key = Gdk.keyval_name(keyval)
        if key == "p" and state & Gdk.ModifierType.CONTROL_MASK:
            if state & Gdk.ModifierType.SHIFT_MASK:
                self.app._show_command_palette()
                return True
        
        # Vim mode handling
        if self.app.vim_mode and self.app.vim_mode.config.enabled:
            return self._handle_vim_key(keyval, state)
        return False
    
    def _handle_vim_key(self, keyval, state) -> bool:
        """Handle key press in Vim mode."""
        key = Gdk.keyval_name(keyval)
        
        # Build key string
        key_str = ""
        if state & Gdk.ModifierType.CONTROL_MASK:
            key_str += "Ctrl+"
        if state & Gdk.ModifierType.MOD1_MASK:
            key_str += "Alt+"
        if state & Gdk.ModifierType.SHIFT_MASK and len(key) == 1:
            key = key.upper()
        
        key_str += key
        
        # Handle through Vim mode
        action = self.app.vim_mode.handle_key(key_str, {
            'ctrl': bool(state & Gdk.ModifierType.CONTROL_MASK),
            'alt': bool(state & Gdk.ModifierType.MOD1_MASK),
            'shift': bool(state & Gdk.ModifierType.SHIFT_MASK),
        })
        
        if action:
            return self._execute_vim_action(action)
        
        return False
    
    def _execute_vim_action(self, action: dict) -> bool:
        """Execute a Vim action."""
        action_name = action.get('action')
        
        if action_name == 'enter_insert_mode':
            self.app.vim_mode.enter_insert_mode()
            return True
        elif action_name == 'enter_normal_mode':
            self.app.vim_mode.enter_normal_mode()
            return True
        elif action_name == 'enter_command_mode':
            self.app.vim_mode.enter_command_mode()
            self.app.show_command_entry()
            return True
        elif action_name == 'insert_char':
            self.editor_buffer.insert_at_cursor(action['char'])
            return True
        elif action_name == 'save_file':
            self.app.save_file()
            return True
        elif action_name == 'open_file':
            self.app.open_file_dialog()
            return True
        elif action_name == 'quit':
            self.app.quit()
            return True
        elif action_name == 'goto_first_line':
            self.editor_buffer.goto_line(1)
            return True
        elif action_name == 'goto_file_end':
            line_count = self.source_buffer.get_line_count()
            self.editor_buffer.goto_line(line_count)
            return True
        
        return False
    
    def get_text(self) -> str:
        """Get editor text."""
        return self.editor_buffer.get_text()
    
    def set_text(self, text: str, filename: str = "Untitled", filepath: Optional[str] = None):
        """Set editor text and detect file type."""
        self.editor_buffer.set_text(text)
        self.file_label.set_label(filename)
        self.modified_dot.set_visible(False)
        self.editor_buffer.modified = False
        
        # Detect and set file type
        if filepath:
            self._set_file_type(filepath)
        else:
            self._set_file_type_from_name(filename)
        
        # Show preview for markdown files
        is_markdown = self.current_file_type[0] in ('markdown', 'text')
        if is_markdown and self.app.config.markdown.live_preview:
            self.preview.render(text)
            self.preview.set_visible(True)
        else:
            self.preview.set_visible(False)
    
    def _set_file_type(self, filepath: str):
        """Set file type from file path."""
        lang_id, display_name, icon_name, badge_class = detect_file_type(filepath)
        self.current_file_type = (lang_id, display_name, icon_name, badge_class)
        
        # Update UI
        self.file_icon.set_from_icon_name(icon_name)
        self.file_type_badge.set_label(display_name)
        
        # Update badge styling
        for cls in ['badge-md', 'badge-py', 'badge-js', 'badge-html', 'badge-css', 
                    'badge-json', 'badge-sh', 'badge-rs', 'badge-go']:
            self.file_type_badge.remove_css_class(cls)
        if badge_class:
            self.file_type_badge.add_css_class(badge_class)
        
        # Set syntax highlighting
        if HAS_GTKSOURCE and self.lang_manager:
            lang = self.lang_manager.get_language(lang_id)
            if lang:
                self.source_buffer.set_language(lang)
        
        # Update status bar file type
        if self.app.status_bar:
            self.app.status_bar.file_type_label.set_label(display_name)
    
    def _set_file_type_from_name(self, filename: str):
        """Set file type from filename only."""
        self._set_file_type(filename)


# ===============================================================================
# STATUS BAR
# ===============================================================================

class StatusBar(Gtk.Box):
    """Beautiful status bar with mode indicator and statistics."""
    
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.app = app
        self.add_css_class('statusbar')
        
        self.set_margin_start(8)
        self.set_margin_end(8)
        self.set_margin_top(4)
        self.set_margin_bottom(4)
        
        # Mode indicator
        self.mode_label = Gtk.Label(label="-- NORMAL --")
        self.mode_label.add_css_class('mode-label')
        self.mode_label.add_css_class('mode-normal')
        self.append(self.mode_label)
        
        # Separator
        sep1 = Gtk.Label(label="  │  ")
        sep1.add_css_class('separator')
        self.append(sep1)
        
        # Position indicator
        self.position_label = Gtk.Label(label="Ln 1, Col 1")
        self.append(self.position_label)
        
        # Separator
        sep2 = Gtk.Label(label="  │  ")
        sep2.add_css_class('separator')
        self.append(sep2)
        
        # Word count
        self.word_count_label = Gtk.Label(label="0 words")
        self.append(self.word_count_label)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        self.append(spacer)
        
        # File encoding
        self.encoding_label = Gtk.Label(label="UTF-8")
        self.append(self.encoding_label)
        
        # Separator
        sep3 = Gtk.Label(label="  │  ")
        sep3.add_css_class('separator')
        self.append(sep3)
        
        # File type
        self.file_type_label = Gtk.Label(label="Markdown")
        self.append(self.file_type_label)
    
    def update_mode(self, mode: EditorMode):
        """Update mode indicator with styling."""
        mode_names = {
            EditorMode.NORMAL: "NORMAL",
            EditorMode.INSERT: "INSERT",
            EditorMode.VISUAL: "VISUAL",
            EditorMode.VISUAL_LINE: "VISUAL LINE",
            EditorMode.VISUAL_BLOCK: "VISUAL BLOCK",
            EditorMode.COMMAND: "COMMAND",
            EditorMode.REPLACE: "REPLACE",
        }
        
        mode_styles = {
            EditorMode.NORMAL: 'mode-normal',
            EditorMode.INSERT: 'mode-insert',
            EditorMode.VISUAL: 'mode-visual',
            EditorMode.VISUAL_LINE: 'mode-visual',
            EditorMode.VISUAL_BLOCK: 'mode-visual',
            EditorMode.COMMAND: 'mode-command',
            EditorMode.REPLACE: 'mode-insert',
        }
        
        mode_name = mode_names.get(mode, "NORMAL")
        self.mode_label.set_label(f"-- {mode_name} --")
        
        # Remove old style classes
        for style in ['mode-normal', 'mode-insert', 'mode-visual', 'mode-command']:
            self.mode_label.remove_css_class(style)
        
        # Add new style class
        self.mode_label.add_css_class(mode_styles.get(mode, 'mode-normal'))
    
    def update_position(self, line: int, column: int):
        """Update position indicator."""
        self.position_label.set_label(f"Ln {line}, Col {column}")
    
    def update_word_count(self, words: int, chars: int):
        """Update word count display."""
        self.word_count_label.set_label(f"{words} words, {chars} chars")


# ===============================================================================
# SIDEBAR
# ===============================================================================

class Sidebar(Gtk.Box):
    """Beautiful sidebar with file browser, notes, and outline."""
    
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.add_css_class('sidebar')
        
        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.set_margin_start(16)
        header.set_margin_end(16)
        header.set_margin_top(16)
        header.set_margin_bottom(12)
        
        # App logo/icon
        icon = Gtk.Image.new_from_icon_name("accessories-text-editor-symbolic")
        icon.set_pixel_size(24)
        header.append(icon)
        
        title = Gtk.Label(label="  MarkMark")
        title.add_css_class('title-2')
        header.append(title)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header.append(spacer)
        
        # New file button
        new_btn = Gtk.Button()
        new_btn.set_icon_name("document-new-symbolic")
        new_btn.add_css_class('flat')
        new_btn.set_tooltip_text("New File (Ctrl+N)")
        new_btn.connect("clicked", self._on_new_file)
        header.append(new_btn)
        
        self.append(header)
        
        # Separator
        self.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        
        # Create scrollable content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Quick Actions section
        content.append(self._create_section("Quick Actions", [
            ("folder-open-symbolic", "Open File...", self._on_open_file),
            ("document-save-symbolic", "Save File", self._on_save_file),
            ("utilities-terminal-symbolic", "Toggle Terminal", self._on_toggle_terminal),
        ]))
        
        # Separator
        content.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        
        # Recent Files section
        self.recent_section = self._create_recent_section()
        content.append(self.recent_section)
        
        # Separator
        content.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        
        # Outline section
        self.outline_section = self._create_outline_section()
        content.append(self.outline_section)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_child(content)
        scroll.set_vexpand(True)
        
        self.append(scroll)
    
    def _create_section(self, title: str, items: list) -> Gtk.Widget:
        """Create a section with buttons."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        
        # Section title
        title_label = Gtk.Label(label=title)
        title_label.add_css_class('section-title')
        title_label.set_halign(Gtk.Align.START)
        box.append(title_label)
        
        # Section items
        for icon_name, label_text, callback in items:
            btn = self._create_item(icon_name, label_text, callback)
            box.append(btn)
        
        return box
    
    def _create_item(self, icon_name: str, label_text: str, callback) -> Gtk.Widget:
        """Create a clickable item."""
        btn = Gtk.Button()
        btn.add_css_class('flat')
        
        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        content.set_spacing(10)
        content.set_margin_start(8)
        content.set_margin_end(8)
        content.set_margin_top(4)
        content.set_margin_bottom(4)
        
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(16)
        content.append(icon)
        
        text = Gtk.Label(label=label_text)
        text.set_halign(Gtk.Align.START)
        content.append(text)
        
        btn.set_child(content)
        btn.connect("clicked", callback)
        
        return btn
    
    def _create_recent_section(self) -> Gtk.Widget:
        """Create recent files section."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        
        title_label = Gtk.Label(label="Recent Files")
        title_label.add_css_class('section-title')
        title_label.set_halign(Gtk.Align.START)
        box.append(title_label)
        
        # Recent files list
        self.recent_model = Gtk.StringList()
        self.recent_list = Gtk.ListView()
        
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._setup_recent_item)
        factory.connect("bind", self._bind_recent_item)
        self.recent_list.set_factory(factory)
        self.recent_list.set_model(Gtk.NoSelection(model=self.recent_model))
        
        box.append(self.recent_list)
        
        return box
    
    def _setup_recent_item(self, factory, item):
        """Setup recent file item."""
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        label.set_margin_start(32)
        label.set_margin_top(4)
        label.set_margin_bottom(4)
        label.add_css_class('caption')
        item.set_child(label)
    
    def _bind_recent_item(self, factory, item):
        """Bind recent file item."""
        label = item.get_child()
        text = item.get_item().get_string()
        label.set_text(text)
    
    def _create_outline_section(self) -> Gtk.Widget:
        """Create outline section."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        
        title_label = Gtk.Label(label="Outline")
        title_label.add_css_class('section-title')
        title_label.set_halign(Gtk.Align.START)
        box.append(title_label)
        
        # Outline list
        self.outline_model = Gtk.StringList()
        self.outline_list = Gtk.ListView()
        
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._setup_outline_item)
        factory.connect("bind", self._bind_outline_item)
        self.outline_list.set_factory(factory)
        self.outline_list.set_model(Gtk.NoSelection(model=self.outline_model))
        
        box.append(self.outline_list)
        
        return box
    
    def _setup_outline_item(self, factory, item):
        """Setup outline item."""
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        label.set_margin_start(32)
        label.set_margin_top(2)
        label.set_margin_bottom(2)
        label.add_css_class('caption')
        item.set_child(label)
    
    def _bind_outline_item(self, factory, item):
        """Bind outline item."""
        label = item.get_child()
        text = item.get_item().get_string()
        label.set_text(text)
    
    def _on_new_file(self, button=None):
        """Handle new file action."""
        self.app._on_new(None, None)
    
    def _on_open_file(self, button=None):
        """Handle open file action."""
        self.app.open_file_dialog()
    
    def _on_save_file(self, button=None):
        """Handle save file action."""
        self.app.save_file()
    
    def _on_toggle_terminal(self, button=None):
        """Handle toggle terminal action."""
        self.app._on_toggle_terminal(None, None)
    
    def update_outline(self, content: str):
        """Update outline from content."""
        self.outline_model.splice(0, self.outline_model.get_n_items(), [])
        
        for line in content.split('\n'):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                title = match.group(2)
                indent = "  " * (level - 1)
                prefix = "•" if level > 1 else "◆"
                self.outline_model.append(f"{indent}{prefix} {title}")
    
    def update_recent_files(self, files: list):
        """Update recent files list."""
        self.recent_model.splice(0, self.recent_model.get_n_items(), [])
        for filepath in files[:10]:
            self.recent_model.append(os.path.basename(filepath))


# ===============================================================================
# MAIN APPLICATION
# ===============================================================================

class MarkMarkApplication(Gtk.Application):
    """Main application class with beautiful, harmonious UI."""
    
    def __init__(self):
        super().__init__(
            application_id='com.markmark.MarkMark',
            flags=Gio.ApplicationFlags.HANDLES_OPEN
        )
        
        self.config_manager: Optional[ConfigManager] = None
        self.config: Optional[AppConfig] = None
        self.vim_mode: Optional[VimMode] = None
        self.zen_mode: Optional[ZenMode] = None
        self.note_manager: Optional[NoteManager] = None
        self.plugin_manager: Optional[PluginManager] = None
        
        self.window: Optional[Gtk.ApplicationWindow] = None
        self.editor: Optional[EditorView] = None
        self.sidebar: Optional[Sidebar] = None
        self.status_bar: Optional[StatusBar] = None
        self.command_palette: Optional[CommandPalette] = None
        self.command_popover: Optional[Gtk.Popover] = None
    
    def do_startup(self):
        """Application startup."""
        Gtk.Application.do_startup(self)
        
        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        
        # Initialize components
        self.vim_mode = VimMode(self.config.vim)
        self.zen_mode = ZenMode(self.config.zen)
        self.note_manager = NoteManager(
            notes_dir=self.config.notes.notes_directory,
            config=self.config
        )
        self.plugin_manager = PluginManager()
        
        # Setup Vim mode callbacks
        self.vim_mode.on_mode_change = self._on_vim_mode_change
        
        # Setup Zen mode callbacks
        self.zen_mode.on_toggle = self._on_zen_mode_toggle
        
        # Setup actions
        self._setup_actions()
        
        # Setup shortcuts
        self._setup_shortcuts()
    
    def _setup_actions(self):
        """Setup application actions."""
        # File actions
        self.add_action(Gio.SimpleAction.new("new", None))
        self.lookup_action("new").connect("activate", self._on_new)
        
        self.add_action(Gio.SimpleAction.new("open", None))
        self.lookup_action("open").connect("activate", self._on_open)
        
        self.add_action(Gio.SimpleAction.new("save", None))
        self.lookup_action("save").connect("activate", self._on_save)
        
        self.add_action(Gio.SimpleAction.new("save-as", None))
        self.lookup_action("save-as").connect("activate", self._on_save_as)
        
        self.add_action(Gio.SimpleAction.new("quit", None))
        self.lookup_action("quit").connect("activate", self._on_quit)
        
        # Edit actions
        self.add_action(Gio.SimpleAction.new("undo", None))
        self.lookup_action("undo").connect("activate", self._on_undo)
        
        self.add_action(Gio.SimpleAction.new("redo", None))
        self.lookup_action("redo").connect("activate", self._on_redo)
        
        # View actions
        self.add_action(Gio.SimpleAction.new("toggle-sidebar", None))
        self.lookup_action("toggle-sidebar").connect("activate", self._on_toggle_sidebar)
        
        self.add_action(Gio.SimpleAction.new("toggle-preview", None))
        self.lookup_action("toggle-preview").connect("activate", self._on_toggle_preview)
        
        self.add_action(Gio.SimpleAction.new("toggle-terminal", None))
        self.lookup_action("toggle-terminal").connect("activate", self._on_toggle_terminal)
        
        self.add_action(Gio.SimpleAction.new("zen-mode", None))
        self.lookup_action("zen-mode").connect("activate", self._on_zen_mode)
        
        self.add_action(Gio.SimpleAction.new("command-palette", None))
        self.lookup_action("command-palette").connect("activate", self._on_command_palette)
        
        # Vim mode toggle
        state = GLib.Variant.new_boolean(self.config.vim.enabled)
        action = Gio.SimpleAction.new_stateful("vim-mode", None, state)
        action.connect("change-state", self._on_toggle_vim_mode)
        self.add_action(action)
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        self.set_accels_for_action("app.new", ["<Control>n"])
        self.set_accels_for_action("app.open", ["<Control>o"])
        self.set_accels_for_action("app.save", ["<Control>s"])
        self.set_accels_for_action("app.save-as", ["<Control><Shift>s"])
        self.set_accels_for_action("app.quit", ["<Control>q"])
        self.set_accels_for_action("app.undo", ["<Control>z"])
        self.set_accels_for_action("app.redo", ["<Control><Shift>z"])
        self.set_accels_for_action("app.toggle-sidebar", ["<Control>b"])
        self.set_accels_for_action("app.toggle-terminal", ["<Control><Alt>t"])
        self.set_accels_for_action("app.zen-mode", ["F11"])
        self.set_accels_for_action("app.command-palette", ["<Control><Shift>p", "<Control>p"])
    
    def do_activate(self):
        """Application activation."""
        if not self.window:
            self._create_window()
        
        self.window.present()
    
    def do_open(self, files, hint, data):
        """Handle file open."""
        if files:
            self._open_file(files[0].get_path())
        self.do_activate()
    
    def _create_window(self):
        """Create main window with beautiful UI."""
        # Create window
        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_title("MarkMark")
        self.window.set_default_size(1400, 900)
        
        # Apply theme
        apply_theme(self.window, dark=self.config.theme == ThemeType.DARK)
        
        if self.config.window_maximized:
            self.window.maximize()
        
        # Create main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_vexpand(True)
        main_box.set_hexpand(True)
        
        # Create header bar
        self._create_header_bar()
        
        # Create main content area with terminal at bottom
        main_paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        main_paned.add_css_class('bottom-paned')
        main_paned.set_vexpand(True)
        main_paned.set_hexpand(True)
        main_paned.set_position(800)
        
        # Create main content
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        content_box.set_vexpand(True)
        content_box.set_hexpand(True)
        
        # Create sidebar
        self.sidebar = Sidebar(self)
        self.sidebar.set_size_request(140, -1)  # Smaller sidebar minimum width
        self.sidebar.set_vexpand(True)
        
        # Sidebar reveal controller
        self.sidebar_revealer = Gtk.Revealer()
        self.sidebar_revealer.set_child(self.sidebar)
        self.sidebar_revealer.set_reveal_child(True)
        self.sidebar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_RIGHT)
        self.sidebar_revealer.set_vexpand(True)
        
        content_box.append(self.sidebar_revealer)
        
        # Create editor
        self.editor = EditorView(self)
        self.editor.set_hexpand(True)
        self.editor.set_vexpand(True)
        content_box.append(self.editor)
        
        # Add content to main paned
        main_paned.set_start_child(content_box)
        main_paned.set_resize_start_child(True)
        main_paned.set_shrink_start_child(False)
        
        # Create terminal panel (bottom)
        self.terminal_panel = TerminalPanel(self)
        self.terminal_panel.set_size_request(-1, 200)
        self.terminal_revealer = Gtk.Revealer()
        self.terminal_revealer.set_child(self.terminal_panel)
        self.terminal_revealer.set_reveal_child(False)
        self.terminal_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        
        main_paned.set_end_child(self.terminal_revealer)
        main_paned.set_resize_end_child(True)
        main_paned.set_shrink_end_child(True)
        
        main_box.append(main_paned)
        
        # Create status bar
        self.status_bar = StatusBar(self)
        main_box.append(self.status_bar)
        
        self.window.set_child(main_box)
        
        # Connect window events
        self.window.connect("close-request", self._on_window_close)
        
        # Update status bar
        self.update_status()
        
        # Update recent files
        self.sidebar.update_recent_files(self.config.recent_files)
    
    def _create_header_bar(self):
        """Create beautiful header bar."""
        header = Gtk.HeaderBar()
        
        # Title with icon
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title_box.set_spacing(8)
        
        icon = Gtk.Image.new_from_icon_name("accessories-text-editor-symbolic")
        icon.set_pixel_size(20)
        title_box.append(icon)
        
        title = Gtk.Label(label="MarkMark")
        title.add_css_class('title')
        title_box.append(title)
        
        header.set_title_widget(title_box)
        
        # Menu button
        menu = Gio.Menu()
        
        # File section
        file_section = Gio.Menu()
        file_section.append("New File", "app.new")
        file_section.append("Open...", "app.open")
        file_section.append("Save", "app.save")
        file_section.append("Save As...", "app.save-as")
        menu.append_section("File", file_section)
        
        # Edit section
        edit_section = Gio.Menu()
        edit_section.append("Undo", "app.undo")
        edit_section.append("Redo", "app.redo")
        menu.append_section("Edit", edit_section)
        
        # View section
        view_section = Gio.Menu()
        view_section.append("Toggle Sidebar", "app.toggle-sidebar")
        view_section.append("Toggle Preview", "app.toggle-preview")
        view_section.append("Toggle Terminal", "app.toggle-terminal")
        view_section.append("Zen Mode", "app.zen-mode")
        view_section.append("Command Palette", "app.command-palette")
        menu.append_section("View", view_section)
        
        # Vim section
        vim_section = Gio.Menu()
        vim_section.append("Toggle Vim Mode", "app.vim-mode")
        menu.append_section("Vim", vim_section)
        
        menu_btn = Gtk.MenuButton()
        menu_btn.set_icon_name("open-menu-symbolic")
        menu_btn.set_menu_model(menu)
        header.pack_end(menu_btn)
        
        self.window.set_titlebar(header)
    
    # -- Command Palette --------------------------------------------------------
    
    def _on_command_palette(self, action, param):
        """Handle command palette action."""
        self._show_command_palette()
    
    def _show_command_palette(self):
        """Show the command palette."""
        if not self.command_palette:
            self.command_palette = CommandPalette(self)
            
            # Create popover
            self.command_popover = Gtk.Popover()
            self.command_popover.set_child(self.command_palette)
            self.command_popover.set_position(Gtk.PositionType.BOTTOM)
            self.command_popover.set_has_arrow(False)
            self.command_popover.connect("closed", lambda _: None)
            
            # Set parent to header bar area
            self.command_popover.set_parent(self.window.get_titlebar())
        
        self.command_popover.popup()
    
    def _hide_command_palette(self):
        """Hide the command palette."""
        if self.command_popover:
            self.command_popover.popdown()
    
    # -- Action Handlers --------------------------------------------------------
    
    def _on_new(self, action, param):
        """Handle new file action."""
        self.editor.set_text("")
        self.editor.editor_buffer.file_path = None
        self.editor.editor_buffer.modified = False
        self.status_bar.update_mode(EditorMode.NORMAL)
        # Reset file type badge
        self.editor.file_type_badge.set_label("Plain Text")
        for cls in ['badge-md', 'badge-py', 'badge-js', 'badge-html', 'badge-css', 
                    'badge-json', 'badge-sh', 'badge-rs', 'badge-go']:
            self.editor.file_type_badge.remove_css_class(cls)
    
    def _on_open(self, action, param):
        """Handle open file action."""
        self.open_file_dialog()
    
    def _on_save(self, action, param):
        """Handle save file action."""
        self.save_file()
    
    def _on_save_as(self, action, param):
        """Handle save as action."""
        self.save_file_as_dialog()
    
    def _on_quit(self, action, param):
        """Handle quit action."""
        self.quit()
    
    def _on_undo(self, action, param):
        """Handle undo action."""
        if self.editor:
            self.editor.source_buffer.undo()
    
    def _on_redo(self, action, param):
        """Handle redo action."""
        if self.editor:
            self.editor.source_buffer.redo()
    
    def _on_toggle_sidebar(self, action, param):
        """Handle toggle sidebar action - also centers editor when hidden."""
        if self.sidebar_revealer:
            current = self.sidebar_revealer.get_reveal_child()
            self.sidebar_revealer.set_reveal_child(not current)
            # Center editor when sidebar is hidden
            if self.editor and self.editor.source_view:
                if current:  # Sidebar was visible, now hiding
                    self.editor.source_view.add_css_class('centered-editor')
                else:  # Sidebar was hidden, now showing
                    self.editor.source_view.remove_css_class('centered-editor')
    
    def _on_toggle_preview(self, action, param):
        """Handle toggle preview action."""
        if self.editor:
            preview = self.editor.preview
            preview.set_visible(not preview.get_visible())
    
    def _on_toggle_terminal(self, action, param):
        """Handle toggle terminal action."""
        if self.terminal_revealer:
            current = self.terminal_revealer.get_reveal_child()
            self.terminal_revealer.set_reveal_child(not current)
            if not current:
                self.terminal_panel.focus()
    
    def _on_zen_mode(self, action, param):
        """Handle zen mode action."""
        self.zen_mode.toggle()
    
    def _on_toggle_vim_mode(self, action, state):
        """Handle vim mode toggle."""
        action.set_state(state)
        self.config.vim.enabled = state.get_boolean()
        self.config_manager.save()
    
    # -- File Operations --------------------------------------------------------
    
    def open_file_dialog(self):
        """Show file open dialog with comprehensive file type support."""
        dialog = Gtk.FileDialog()
        dialog.set_title("Open File")
        
        # All supported files
        filter_all_supported = Gtk.FileFilter()
        filter_all_supported.set_name("All Supported Files")
        for ext in FILE_TYPE_MAP.keys():
            if ext.startswith('.'):
                filter_all_supported.add_pattern(f"*{ext}")
            else:
                filter_all_supported.add_pattern(ext)
        
        # Markdown files
        filter_md = Gtk.FileFilter()
        filter_md.set_name("Markdown Files")
        filter_md.add_pattern("*.md")
        filter_md.add_pattern("*.markdown")
        filter_md.add_pattern("*.mdown")
        filter_md.add_pattern("*.mkd")
        filter_md.add_pattern("*.qmd")
        filter_md.add_pattern("*.rmd")
        
        # Text files
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text Files")
        filter_text.add_pattern("*.txt")
        filter_text.add_pattern("*.rst")
        filter_text.add_pattern("*.tex")
        
        # Programming files
        filter_code = Gtk.FileFilter()
        filter_code.set_name("Programming Files")
        filter_code.add_pattern("*.py")
        filter_code.add_pattern("*.js")
        filter_code.add_pattern("*.ts")
        filter_code.add_pattern("*.jsx")
        filter_code.add_pattern("*.tsx")
        filter_code.add_pattern("*.html")
        filter_code.add_pattern("*.css")
        filter_code.add_pattern("*.scss")
        filter_code.add_pattern("*.json")
        filter_code.add_pattern("*.yaml")
        filter_code.add_pattern("*.yml")
        filter_code.add_pattern("*.xml")
        filter_code.add_pattern("*.c")
        filter_code.add_pattern("*.cpp")
        filter_code.add_pattern("*.h")
        filter_code.add_pattern("*.rs")
        filter_code.add_pattern("*.go")
        filter_code.add_pattern("*.java")
        filter_code.add_pattern("*.rb")
        filter_code.add_pattern("*.php")
        filter_code.add_pattern("*.sh")
        filter_code.add_pattern("*.bash")
        filter_code.add_pattern("*.sql")
        
        # Config files
        filter_config = Gtk.FileFilter()
        filter_config.set_name("Config Files")
        filter_config.add_pattern("*.toml")
        filter_config.add_pattern("*.ini")
        filter_config.add_pattern("*.cfg")
        filter_config.add_pattern("*.conf")
        filter_config.add_pattern("*.env")
        filter_config.add_pattern(".gitignore")
        filter_config.add_pattern("Dockerfile")
        filter_config.add_pattern("Makefile")
        
        # All files
        filter_all = Gtk.FileFilter()
        filter_all.set_name("All Files")
        filter_all.add_pattern("*")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_all_supported)
        filters.append(filter_md)
        filters.append(filter_text)
        filters.append(filter_code)
        filters.append(filter_config)
        filters.append(filter_all)
        dialog.set_filters(filters)
        
        dialog.open(self.window, None, self._on_file_opened)
    
    def _on_file_opened(self, dialog, result):
        """Handle file opened callback."""
        try:
            file = dialog.open_finish(result)
            if file:
                self._open_file(file.get_path())
        except Exception:
            pass
    
    def _open_file(self, filepath: str):
        """Open a file."""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            filename = os.path.basename(filepath)
            self.editor.set_text(content, filename, filepath)
            self.editor.editor_buffer.file_path = filepath
            self.editor.editor_buffer.modified = False
            
            # Update recent files
            self.config_manager.add_recent_file(filepath)
            self.sidebar.update_recent_files(self.config.recent_files)
            
            # Update sidebar outline
            self.sidebar.update_outline(content)
            
            # Set terminal working directory
            file_dir = os.path.dirname(filepath)
            if file_dir and os.path.isdir(file_dir):
                self.terminal_panel.set_working_directory(file_dir)
            
        except Exception as e:
            self._show_error(f"Error opening file: {e}")
    
    def save_file(self) -> bool:
        """Save current file."""
        if not self.editor.editor_buffer.file_path:
            return self.save_file_as_dialog()
        
        return self._save_to_path(self.editor.editor_buffer.file_path)
    
    def save_file_as_dialog(self) -> bool:
        """Show save as dialog."""
        dialog = Gtk.FileDialog()
        dialog.set_title("Save File As")
        
        # All supported files
        filter_all_supported = Gtk.FileFilter()
        filter_all_supported.set_name("All Supported Files")
        for ext in FILE_TYPE_MAP.keys():
            if ext.startswith('.'):
                filter_all_supported.add_pattern(f"*{ext}")
        
        # Markdown files (default)
        filter_md = Gtk.FileFilter()
        filter_md.set_name("Markdown Files")
        filter_md.add_pattern("*.md")
        filter_md.add_pattern("*.markdown")
        
        # Text files
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text Files")
        filter_text.add_pattern("*.txt")
        
        # Programming files
        filter_code = Gtk.FileFilter()
        filter_code.set_name("Programming Files")
        filter_code.add_pattern("*.py")
        filter_code.add_pattern("*.js")
        filter_code.add_pattern("*.ts")
        filter_code.add_pattern("*.html")
        filter_code.add_pattern("*.css")
        filter_code.add_pattern("*.json")
        filter_code.add_pattern("*.yaml")
        filter_code.add_pattern("*.yml")
        filter_code.add_pattern("*.sh")
        
        # All files
        filter_all = Gtk.FileFilter()
        filter_all.set_name("All Files")
        filter_all.add_pattern("*")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_all_supported)
        filters.append(filter_md)
        filters.append(filter_text)
        filters.append(filter_code)
        filters.append(filter_all)
        dialog.set_filters(filters)
        
        dialog.save(self.window, None, self._on_file_saved)
        return True
    
    def _on_file_saved(self, dialog, result):
        """Handle file saved callback."""
        try:
            file = dialog.save_finish(result)
            if file:
                self._save_to_path(file.get_path())
        except Exception:
            pass
    
    def _save_to_path(self, filepath: str) -> bool:
        """Save to a specific path."""
        try:
            content = self.editor.get_text()
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            filename = os.path.basename(filepath)
            self.editor.editor_buffer.file_path = filepath
            self.editor.editor_buffer.modified = False
            self.editor.file_label.set_label(filename)
            self.editor.modified_dot.set_visible(False)
            
            # Update file type based on saved filename
            self.editor._set_file_type(filepath)
            
            # Update recent files
            self.config_manager.add_recent_file(filepath)
            
            return True
            
        except Exception as e:
            self._show_error(f"Error saving file: {e}")
            return False
    
    # -- Callbacks --------------------------------------------------------------
    
    def _on_vim_mode_change(self, mode: EditorMode):
        """Handle Vim mode change."""
        if self.status_bar:
            self.status_bar.update_mode(mode)
    
    def _on_zen_mode_toggle(self, active: bool):
        """Handle Zen mode toggle - hides UI and centers content."""
        if active:
            if self.sidebar_revealer:
                self.sidebar_revealer.set_reveal_child(False)
            if self.terminal_revealer:
                self.terminal_revealer.set_reveal_child(False)
            if self.editor:
                self.editor.add_css_class('zen-mode')
                # Zen mode has its own centering via CSS
        else:
            if self.sidebar_revealer:
                self.sidebar_revealer.set_reveal_child(True)
            if self.editor:
                self.editor.remove_css_class('zen-mode')
    
    def _on_window_close(self, window) -> bool:
        """Handle window close."""
        # Check for unsaved changes
        if self.editor and self.editor.editor_buffer.modified:
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Save changes before closing?"
            )
            
            response = dialog.choose()
            dialog.destroy()
            
            if response == 1:  # YES
                if not self.save_file():
                    return True  # Prevent close
            elif response != 0:  # Not NO
                return True  # Prevent close
        
        # Save window state
        self.config.window_width = window.get_width()
        self.config.window_height = window.get_height()
        self.config.window_maximized = window.is_maximized()
        self.config_manager.save()
        
        return False
    
    def show_command_entry(self):
        """Show command entry for Vim command mode."""
        # TODO: Implement command entry
        pass
    
    def update_status(self):
        """Update status bar."""
        if self.editor and self.status_bar:
            line, col = self.editor.editor_buffer.get_line_column()
            self.status_bar.update_position(line, col)
            
            text = self.editor.get_text()
            words = len(text.split())
            chars = len(text)
            self.status_bar.update_word_count(words, chars)
    
    def _show_error(self, message: str):
        """Show error dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.choose()
        dialog.destroy()


# ===============================================================================
# MAIN ENTRY POINT
# ===============================================================================

def main():
    """Main entry point."""
    # Check for CLI mode
    parser = create_parser()
    args = parser.parse_args()
    
    if args.cli or args.execute:
        # Run in CLI mode
        cli = CLIMode()
        
        if args.execute:
            result = cli.run_batch(args.execute.split(';'))
            print(result)
            return 0
        
        if args.file:
            cli._cmd_open(args.file)
        
        if args.pipe:
            cli.process_pipe()
        
        cli.run_repl()
        return 0
    
    # Run GUI mode
    app = MarkMarkApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
