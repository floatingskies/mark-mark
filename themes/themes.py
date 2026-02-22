"""
Themes system for MarkMark.
Provides syntax highlighting and UI themes.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class ThemeType(Enum):
    """Theme type (light/dark)."""
    LIGHT = "light"
    DARK = "dark"


@dataclass
class SyntaxColors:
    """Colors for syntax highlighting."""
    foreground: str = "#d4d4d4"
    background: str = "#1e1e1e"
    cursor: str = "#ffffff"
    selection: str = "#264f78"
    line_number: str = "#858585"
    line_number_active: str = "#c6c6c6"
    
    # Syntax colors
    comment: str = "#6a9955"
    keyword: str = "#569cd6"
    string: str = "#ce9178"
    number: str = "#b5cea8"
    operator: str = "#d4d4d4"
    function: str = "#dcdcaa"
    variable: str = "#9cdcfe"
    constant: str = "#4fc1ff"
    type_: str = "#4ec9b0"
    punctuation: str = "#d4d4d4"
    
    # Markdown specific
    heading: str = "#569cd6"
    heading_marker: str = "#569cd6"
    bold: str = "#ffffff"
    italic: str = "#d4d4d4"
    link: str = "#ce9178"
    image: str = "#dcdcaa"
    code: str = "#ce9178"
    code_block: str = "#1e1e1e"
    blockquote: str = "#6a9955"
    list_marker: str = "#d4d4d4"
    hr: str = "#808080"
    
    # UI colors
    scrollbar: str = "#424242"
    scrollbar_hover: str = "#4f4f4f"
    border: str = "#3c3c3c"
    highlight: str = "#ffd700"
    error: str = "#f44747"
    warning: str = "#cca700"
    info: str = "#75beff"


@dataclass
class Theme:
    """A complete theme definition."""
    name: str
    type: ThemeType
    colors: SyntaxColors
    author: str = ""
    description: str = ""
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


class ThemeManager:
    """
    Manages editor themes.
    
    Features:
    - Built-in themes
    - Custom theme support
    - Theme import/export
    - GTK SourceView style scheme generation
    """
    
    def __init__(self, theme_dirs: List[str] = None):
        self.theme_dirs = theme_dirs or []
        self.themes: Dict[str, Theme] = {}
        
        # Add default theme directory
        default_dir = Path.home() / ".config" / "markmark" / "themes"
        if str(default_dir) not in self.theme_dirs:
            self.theme_dirs.append(str(default_dir))
        
        # Initialize built-in themes
        self._init_builtin_themes()
        
        # Load custom themes
        self._load_themes()
    
    def _init_builtin_themes(self) -> None:
        """Initialize built-in themes."""
        
        # VS Code Dark+ (default)
        self.add_theme(Theme(
            name="Dark+",
            type=ThemeType.DARK,
            author="MarkMark",
            description="VS Code inspired dark theme",
            colors=SyntaxColors(
                foreground="#d4d4d4",
                background="#1e1e1e",
                cursor="#ffffff",
                selection="#264f78",
                line_number="#858585",
                line_number_active="#c6c6c6",
                comment="#6a9955",
                keyword="#569cd6",
                string="#ce9178",
                number="#b5cea8",
                operator="#d4d4d4",
                function="#dcdcaa",
                variable="#9cdcfe",
                constant="#4fc1ff",
                type_="#4ec9b0",
                heading="#569cd6",
                heading_marker="#569cd6",
                bold="#ffffff",
                link="#ce9178",
                code="#ce9178",
                code_block="#1e1e1e",
                blockquote="#6a9955",
            )
        ))
        
        # Monokai
        self.add_theme(Theme(
            name="Monokai",
            type=ThemeType.DARK,
            author="MarkMark",
            description="Classic Monokai theme",
            colors=SyntaxColors(
                foreground="#f8f8f2",
                background="#272822",
                cursor="#f8f8f0",
                selection="#49483e",
                line_number="#75715e",
                line_number_active="#f8f8f2",
                comment="#75715e",
                keyword="#f92672",
                string="#e6db74",
                number="#ae81ff",
                operator="#f8f8f2",
                function="#a6e22e",
                variable="#f8f8f2",
                constant="#ae81ff",
                type_="#66d9ef",
                heading="#f92672",
                heading_marker="#f92672",
                bold="#f8f8f2",
                link="#e6db74",
                code="#e6db74",
                code_block="#272822",
                blockquote="#75715e",
            )
        ))
        
        # Solarized Dark
        self.add_theme(Theme(
            name="Solarized Dark",
            type=ThemeType.DARK,
            author="MarkMark",
            description="Solarized dark theme",
            colors=SyntaxColors(
                foreground="#839496",
                background="#002b36",
                cursor="#839496",
                selection="#073642",
                line_number="#586e75",
                line_number_active="#839496",
                comment="#586e75",
                keyword="#859900",
                string="#2aa198",
                number="#d33682",
                operator="#839496",
                function="#268bd2",
                variable="#839496",
                constant="#d33682",
                type_="#b58900",
                heading="#859900",
                heading_marker="#859900",
                bold="#839496",
                link="#2aa198",
                code="#2aa198",
                code_block="#002b36",
                blockquote="#586e75",
            )
        ))
        
        # Solarized Light
        self.add_theme(Theme(
            name="Solarized Light",
            type=ThemeType.LIGHT,
            author="MarkMark",
            description="Solarized light theme",
            colors=SyntaxColors(
                foreground="#657b83",
                background="#fdf6e3",
                cursor="#657b83",
                selection="#eee8d5",
                line_number="#93a1a1",
                line_number_active="#657b83",
                comment="#93a1a1",
                keyword="#859900",
                string="#2aa198",
                number="#d33682",
                operator="#657b83",
                function="#268bd2",
                variable="#657b83",
                constant="#d33682",
                type_="#b58900",
                heading="#859900",
                heading_marker="#859900",
                bold="#657b83",
                link="#2aa198",
                code="#2aa198",
                code_block="#fdf6e3",
                blockquote="#93a1a1",
            )
        ))
        
        # GitHub Dark
        self.add_theme(Theme(
            name="GitHub Dark",
            type=ThemeType.DARK,
            author="MarkMark",
            description="GitHub dark theme",
            colors=SyntaxColors(
                foreground="#c9d1d9",
                background="#0d1117",
                cursor="#c9d1d9",
                selection="#264f78",
                line_number="#6e7681",
                line_number_active="#c9d1d9",
                comment="#8b949e",
                keyword="#ff7b72",
                string="#a5d6ff",
                number="#79c0ff",
                operator="#c9d1d9",
                function="#d2a8ff",
                variable="#ffa657",
                constant="#79c0ff",
                type_="#7ee787",
                heading="#ff7b72",
                heading_marker="#ff7b72",
                bold="#c9d1d9",
                link="#a5d6ff",
                code="#a5d6ff",
                code_block="#0d1117",
                blockquote="#8b949e",
            )
        ))
        
        # GitHub Light
        self.add_theme(Theme(
            name="GitHub Light",
            type=ThemeType.LIGHT,
            author="MarkMark",
            description="GitHub light theme",
            colors=SyntaxColors(
                foreground="#24292f",
                background="#ffffff",
                cursor="#24292f",
                selection="#ddf4ff",
                line_number="#8c959f",
                line_number_active="#24292f",
                comment="#6e7781",
                keyword="#cf222e",
                string="#0a3069",
                number="#0550ae",
                operator="#24292f",
                function="#8250df",
                variable="#953800",
                constant="#0550ae",
                type_="#116329",
                heading="#cf222e",
                heading_marker="#cf222e",
                bold="#24292f",
                link="#0969da",
                code="#0a3069",
                code_block="#ffffff",
                blockquote="#6e7781",
            )
        ))
        
        # Dracula
        self.add_theme(Theme(
            name="Dracula",
            type=ThemeType.DARK,
            author="MarkMark",
            description="Dracula theme",
            colors=SyntaxColors(
                foreground="#f8f8f2",
                background="#282a36",
                cursor="#f8f8f0",
                selection="#44475a",
                line_number="#6272a4",
                line_number_active="#f8f8f2",
                comment="#6272a4",
                keyword="#ff79c6",
                string="#f1fa8c",
                number="#bd93f9",
                operator="#f8f8f2",
                function="#50fa7b",
                variable="#f8f8f2",
                constant="#bd93f9",
                type_="#8be9fd",
                heading="#ff79c6",
                heading_marker="#ff79c6",
                bold="#f8f8f2",
                link="#f1fa8c",
                code="#f1fa8c",
                code_block="#282a36",
                blockquote="#6272a4",
            )
        ))
        
        # Nord
        self.add_theme(Theme(
            name="Nord",
            type=ThemeType.DARK,
            author="MarkMark",
            description="Nord theme",
            colors=SyntaxColors(
                foreground="#d8dee9",
                background="#2e3440",
                cursor="#d8dee9",
                selection="#434c5e",
                line_number="#4c566a",
                line_number_active="#d8dee9",
                comment="#616e88",
                keyword="#81a1c1",
                string="#a3be8c",
                number="#b48ead",
                operator="#81a1c1",
                function="#88c0d0",
                variable="#d8dee9",
                constant="#b48ead",
                type_="#8fbcbb",
                heading="#81a1c1",
                heading_marker="#81a1c1",
                bold="#d8dee9",
                link="#a3be8c",
                code="#a3be8c",
                code_block="#2e3440",
                blockquote="#616e88",
            )
        ))
        
        # Gruvbox Dark
        self.add_theme(Theme(
            name="Gruvbox Dark",
            type=ThemeType.DARK,
            author="MarkMark",
            description="Gruvbox dark theme",
            colors=SyntaxColors(
                foreground="#ebdbb2",
                background="#282828",
                cursor="#ebdbb2",
                selection="#504945",
                line_number="#928374",
                line_number_active="#ebdbb2",
                comment="#928374",
                keyword="#fb4934",
                string="#b8bb26",
                number="#d3869b",
                operator="#ebdbb2",
                function="#fabd2f",
                variable="#ebdbb2",
                constant="#d3869b",
                type_="#8ec07c",
                heading="#fb4934",
                heading_marker="#fb4934",
                bold="#ebdbb2",
                link="#b8bb26",
                code="#b8bb26",
                code_block="#282828",
                blockquote="#928374",
            )
        ))
        
        # One Dark
        self.add_theme(Theme(
            name="One Dark",
            type=ThemeType.DARK,
            author="MarkMark",
            description="One Dark theme",
            colors=SyntaxColors(
                foreground="#abb2bf",
                background="#282c34",
                cursor="#528bff",
                selection="#3e4451",
                line_number="#5c6370",
                line_number_active="#abb2bf",
                comment="#5c6370",
                keyword="#c678dd",
                string="#98c379",
                number="#d19a66",
                operator="#56b6c2",
                function="#61afef",
                variable="#e06c75",
                constant="#d19a66",
                type_="#e5c07b",
                heading="#c678dd",
                heading_marker="#c678dd",
                bold="#abb2bf",
                link="#98c379",
                code="#98c379",
                code_block="#282c34",
                blockquote="#5c6370",
            )
        ))
    
    def _load_themes(self) -> None:
        """Load custom themes from theme directories."""
        for theme_dir in self.theme_dirs:
            theme_path = Path(theme_dir)
            if not theme_path.exists():
                continue
            
            for file in theme_path.rglob("*.json"):
                try:
                    with open(file) as f:
                        data = json.load(f)
                    self._load_theme_dict(data)
                except Exception as e:
                    print(f"Error loading theme from {file}: {e}")
    
    def _load_theme_dict(self, data: dict) -> None:
        """Load a theme from dictionary."""
        colors_data = data.get("colors", {})
        colors = SyntaxColors(
            foreground=colors_data.get("foreground", "#d4d4d4"),
            background=colors_data.get("background", "#1e1e1e"),
            cursor=colors_data.get("cursor", "#ffffff"),
            selection=colors_data.get("selection", "#264f78"),
            line_number=colors_data.get("line_number", "#858585"),
            line_number_active=colors_data.get("line_number_active", "#c6c6c6"),
            comment=colors_data.get("comment", "#6a9955"),
            keyword=colors_data.get("keyword", "#569cd6"),
            string=colors_data.get("string", "#ce9178"),
            number=colors_data.get("number", "#b5cea8"),
            operator=colors_data.get("operator", "#d4d4d4"),
            function=colors_data.get("function", "#dcdcaa"),
            variable=colors_data.get("variable", "#9cdcfe"),
            constant=colors_data.get("constant", "#4fc1ff"),
            type_=colors_data.get("type", "#4ec9b0"),
            heading=colors_data.get("heading", "#569cd6"),
            heading_marker=colors_data.get("heading_marker", "#569cd6"),
            bold=colors_data.get("bold", "#ffffff"),
            link=colors_data.get("link", "#ce9178"),
            code=colors_data.get("code", "#ce9178"),
            code_block=colors_data.get("code_block", "#1e1e1e"),
            blockquote=colors_data.get("blockquote", "#6a9955"),
        )
        
        theme = Theme(
            name=data.get("name", "Unnamed"),
            type=ThemeType(data.get("type", "dark")),
            colors=colors,
            author=data.get("author", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            metadata=data.get("metadata", {}),
        )
        self.add_theme(theme)
    
    def add_theme(self, theme: Theme) -> None:
        """Add a theme."""
        self.themes[theme.name] = theme
    
    def remove_theme(self, name: str) -> bool:
        """Remove a theme by name."""
        if name in self.themes:
            del self.themes[name]
            return True
        return False
    
    def get_theme(self, name: str) -> Optional[Theme]:
        """Get a theme by name."""
        return self.themes.get(name)
    
    def get_themes_by_type(self, theme_type: ThemeType) -> List[Theme]:
        """Get all themes of a specific type."""
        return [t for t in self.themes.values() if t.type == theme_type]
    
    def get_all_themes(self) -> List[Theme]:
        """Get all themes."""
        return list(self.themes.values())
    
    def get_theme_names(self) -> List[str]:
        """Get all theme names."""
        return list(self.themes.keys())
    
    def to_css(self, theme: Theme) -> str:
        """Convert theme to CSS."""
        c = theme.colors
        return f'''
/* Theme: {theme.name} */
.editor {{
    color: {c.foreground};
    background-color: {c.background};
    caret-color: {c.cursor};
}}

.editor:selected {{
    background-color: {c.selection};
}}

.line-numbers {{
    color: {c.line_number};
    background-color: {c.background};
}}

.line-numbers .active {{
    color: {c.line_number_active};
}}

/* Syntax highlighting */
.comment {{ color: {c.comment}; }}
.keyword {{ color: {c.keyword}; }}
.string {{ color: {c.string}; }}
.number {{ color: {c.number}; }}
.operator {{ color: {c.operator}; }}
.function {{ color: {c.function}; }}
.variable {{ color: {c.variable}; }}
.constant {{ color: {c.constant}; }}
.type {{ color: {c.type_}; }}

/* Markdown specific */
.heading {{ color: {c.heading}; font-weight: bold; }}
.heading-marker {{ color: {c.heading_marker}; }}
.bold {{ font-weight: bold; }}
.italic {{ font-style: italic; }}
.link {{ color: {c.link}; text-decoration: underline; }}
.image {{ color: {c.image}; }}
.code {{ color: {c.code}; background-color: {c.code_block}; padding: 0.2em 0.4em; border-radius: 3px; }}
.code-block {{ color: {c.code}; background-color: {c.code_block}; padding: 1em; }}
.blockquote {{ color: {c.blockquote}; border-left: 4px solid {c.blockquote}; padding-left: 1em; }}
.list-marker {{ color: {c.list_marker}; }}
.hr {{ color: {c.hr}; }}
'''
    
    def to_gtksource_style(self, theme: Theme) -> str:
        """Convert theme to GtkSourceView style scheme XML."""
        c = theme.colors
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<style-scheme id="{theme.name.lower().replace(" ", "-")}" name="{theme.name}" version="1.0">
    <author>{theme.author}</author>
    <description>{theme.description}</description>
    
    <color name="foreground" value="{c.foreground}"/>
    <color name="background" value="{c.background}"/>
    <color name="cursor" value="{c.cursor}"/>
    <color name="selection" value="{c.selection}"/>
    <color name="line_number" value="{c.line_number}"/>
    <color name="line_number_active" value="{c.line_number_active}"/>
    <color name="comment" value="{c.comment}"/>
    <color name="keyword" value="{c.keyword}"/>
    <color name="string" value="{c.string}"/>
    <color name="number" value="{c.number}"/>
    <color name="function" value="{c.function}"/>
    <color name="variable" value="{c.variable}"/>
    <color name="constant" value="{c.constant}"/>
    <color name="type" value="{c.type_}"/>
    <color name="heading" value="{c.heading}"/>
    <color name="link" value="{c.link}"/>
    <color name="code" value="{c.code}"/>
    <color name="blockquote" value="{c.blockquote}"/>
    
    <style name="text" foreground="foreground" background="background"/>
    <style name="cursor" foreground="cursor"/>
    <style name="selection" background="selection"/>
    <style name="current-line" background="selection"/>
    <style name="line-numbers" foreground="line_number" background="background"/>
    <style name="draw-spaces" foreground="line_number"/>
    
    <!-- Syntax -->
    <style name="def:comment" foreground="comment"/>
    <style name="def:keyword" foreground="keyword"/>
    <style name="def:string" foreground="string"/>
    <style name="def:number" foreground="number"/>
    <style name="def:function" foreground="function"/>
    <style name="def:variable" foreground="variable"/>
    <style name="def:constant" foreground="constant"/>
    <style name="def:type" foreground="type"/>
    <style name="def:operator" foreground="foreground"/>
    <style name="def:punctuation" foreground="foreground"/>
    
    <!-- Markdown -->
    <style name="markdown:header" foreground="heading" bold="true"/>
    <style name="markdown:header-marker" foreground="heading"/>
    <style name="markdown:emphasis" italic="true"/>
    <style name="markdown:strong-emphasis" bold="true"/>
    <style name="markdown:link" foreground="link" underline="single"/>
    <style name="markdown:image" foreground="link"/>
    <style name="markdown:code" foreground="code"/>
    <style name="markdown:code-block" foreground="code"/>
    <style name="markdown:blockquote" foreground="blockquote"/>
    <style name="markdown:list-marker" foreground="foreground"/>
    <style name="markdown:horizontal-rule" foreground="foreground"/>
</style-scheme>
'''
    
    def save_theme(self, theme: Theme, filepath: str = None) -> bool:
        """Save a theme to file."""
        filepath = filepath or str(
            Path(self.theme_dirs[0]) / f"{theme.name}.json"
        )
        
        try:
            data = {
                "name": theme.name,
                "type": theme.type.value,
                "author": theme.author,
                "description": theme.description,
                "version": theme.version,
                "colors": {
                    "foreground": theme.colors.foreground,
                    "background": theme.colors.background,
                    "cursor": theme.colors.cursor,
                    "selection": theme.colors.selection,
                    "line_number": theme.colors.line_number,
                    "line_number_active": theme.colors.line_number_active,
                    "comment": theme.colors.comment,
                    "keyword": theme.colors.keyword,
                    "string": theme.colors.string,
                    "number": theme.colors.number,
                    "operator": theme.colors.operator,
                    "function": theme.colors.function,
                    "variable": theme.colors.variable,
                    "constant": theme.colors.constant,
                    "type": theme.colors.type_,
                    "heading": theme.colors.heading,
                    "heading_marker": theme.colors.heading_marker,
                    "bold": theme.colors.bold,
                    "link": theme.colors.link,
                    "code": theme.colors.code,
                    "code_block": theme.colors.code_block,
                    "blockquote": theme.colors.blockquote,
                },
                "metadata": theme.metadata,
            }
            
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving theme: {e}")
            return False


__all__ = ['Theme', 'ThemeType', 'SyntaxColors', 'ThemeManager']
