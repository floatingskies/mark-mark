# MarkMark - Advanced Markdown Multitool

A comprehensive GTK4-based markdown editor with Vim-mode, Zen-mode, CLI mode,
Helix/Neovim inspired features, and extensible framework support.

**More complete than KDE's Kate for writing and note-taking.**

## Features

### Core Editor
- Full-featured markdown editor with live preview
- Syntax highlighting for markdown and code blocks
- Multi-tab/multi-buffer support
- Split view (horizontal/vertical)
- Minimap navigation
- Line numbers with relative mode support

### Vim Mode
Complete Vim emulation including:
- **Modes**: Normal, Insert, Visual, Visual Line, Visual Block, Command, Replace
- **Motions**: h, j, k, l, w, W, b, B, e, E, 0, ^, $, gg, G, {, }, %
- **Operators**: d, c, y, p, >, <, =, g~, gu, gU, gq
- **Text Objects**: iw, iW, i", i', i(, i[, i{, i<, it, ip, is, and their "a" variants
- **Registers**: Named (a-z), numbered (0-9), unnamed (")
- **Marks**: a-z (local), A-Z (global), special marks
- **Macros**: Record and play with q and @
- **Search**: /, ?, n, N, *, # with highlighting
- **Ex Commands**: :w, :q, :e, :s, :g, :v, :%s, and many more

### Helix/Neovim Inspired Features
- **Multi-cursor editing**: Add cursors above/below, split selections
- **Selection-first editing model**: Select then operate
- **Object selection**: Select inside/around quotes, brackets, tags
- **Surround operations**: Add, change, delete surrounding characters
- **Multiple selections**: Split by regex, by line
- **Smart text objects**: Extended markdown-aware objects

### Zen Mode
Distraction-free writing environment:
- Hide all UI chrome (menu, status bar, sidebar)
- Centered text with configurable max width
- Focus on current paragraph/sentence
- Typewriter scrolling (cursor stays centered)
- Ambient typography settings
- Multiple presets (minimal, dark room, typewriter, readable)
- Optional ambient sounds

### CLI Mode
Powerful command-line interface:
- Interactive REPL mode
- Batch command execution
- Pipe support for processing
- All editing operations from command line
- Quick file processing and conversion

### Note-Taking System
Comprehensive note management:
- Wiki-style linking between notes ([[note-name]])
- Tag-based organization (#tag)
- Full-text search
- Categories and folders
- Daily notes
- Templates for notes
- Import/export support

### Framework Features
- **Plugin System**: Hooks, commands, UI extensions
- **Snippets**: Text expansion with variables
- **Templates**: Document templates with fill-in fields
- **Themes**: 10+ built-in themes, custom theme support
- **Keybindings**: Fully customizable
- **Configuration**: JSON-based, live reload

### Export Options
- HTML with styling
- PDF (via WeasyPrint)
- DOCX (via python-docx)
- Plain text

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/markmark/markmark.git
cd markmark

# Install dependencies
# On Debian/Ubuntu:
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-gtksource-5 gir1.2-adw-1

# On Fedora:
sudo dnf install python3-gobject gtk4 gtksourceview5-devel libadwaita-devel

# On Arch Linux:
sudo pacman -S python-gobject gtk4 gtksourceview5 libadwaita

# Install MarkMark
pip install -e .
```

### Requirements

- Python 3.9+
- GTK 4.0
- GtkSourceView 5
- libadwaita (optional, for modern UI)
- PyGObject

## Usage

### GUI Mode

```bash
# Open GUI with no file
markmark

# Open a specific file
markmark document.md

# Open in Zen mode
markmark --zen document.md
```

### CLI Mode

```bash
# Interactive CLI mode
markmark -c

# Open file in CLI
markmark -c document.md

# Execute commands
markmark -e "open doc.md; print 1 20; save"

# Process from pipe
cat document.md | markmark -p

# Export to HTML
markmark -f html document.md -o output.html
```

### CLI Commands

```
File Commands:
  open <file>      Open a file for editing
  new [name]       Create a new file
  save [file]      Save current file
  close [force]    Close current file

Editor Commands:
  insert <line> <text>    Insert text at line
  append <text>           Append text to end
  delete <start> [end]    Delete lines
  replace /old/new/       Replace text (regex)
  move <start> <end> <dest>    Move lines
  copy <start> <end> <dest>    Copy lines

Buffer Commands:
  print [start] [end]     Print buffer contents
  head [n]                Print first n lines
  tail [n]                Print last n lines
  lines                   Count lines/words/chars

Search Commands:
  search <pattern>        Search for pattern
  match <text>            Find matching lines

Format Commands:
  format                  Format markdown
  toc                     Generate table of contents
  wrap <width>            Wrap text to width

Export Commands:
  export <format> [file]  Export to format
  preview                 Preview as HTML

System Commands:
  shell <cmd>             Execute shell command
  cd <path>               Change directory
  pwd                     Print working directory
  ls [path]               List files

Other:
  help [command]          Show help
  version                 Show version
  quit                    Exit CLI
```

## Vim Mode Reference

### Mode Switching

| Key | Action |
|-----|--------|
| `i` | Enter insert mode |
| `a` | Insert after cursor |
| `I` | Insert at line start |
| `A` | Insert at line end |
| `o` | Insert line below |
| `O` | Insert line above |
| `v` | Visual mode |
| `V` | Visual line mode |
| `Ctrl+v` | Visual block mode |
| `:` | Command mode |
| `R` | Replace mode |
| `Esc` | Return to normal mode |

### Motions

| Key | Action |
|-----|--------|
| `h` `j` `k` `l` | Move left/down/up/right |
| `w` `W` | Word/WORD forward |
| `b` `B` | Word/WORD backward |
| `e` `E` | End of word/WORD |
| `0` | Line start |
| `^` | First non-whitespace |
| `$` | Line end |
| `gg` | File start |
| `G` | File end |
| `{` `}` | Paragraph prev/next |
| `%` | Match bracket |
| `Ctrl+u/d` | Half page up/down |
| `Ctrl+b/f` | Page up/down |

### Operators

| Key | Action |
|-----|--------|
| `d` | Delete |
| `c` | Change |
| `y` | Yank |
| `p` `P` | Paste after/before |
| `x` `X` | Delete char/before |
| `r` | Replace char |
| `>` `<` | Indent/unindent |
| `=` | Auto indent |
| `J` | Join lines |
| `g~` `gu` `gU` | Toggle/lower/upper case |

### Text Objects

| Object | Inner | Around |
|--------|-------|--------|
| Word | `iw` | `aw` |
| WORD | `iW` | `aW` |
| Sentence | `is` | `as` |
| Paragraph | `ip` | `ap` |
| Quotes | `i"` `i'` | `a"` `a'` |
| Brackets | `i(` `i[` `i{` | `a(` `a[` `a{` |
| Tag | `it` | `at` |

### Ex Commands

| Command | Action |
|---------|--------|
| `:w` | Write file |
| `:q` | Quit |
| `:wq` | Write and quit |
| `:e <file>` | Edit file |
| `:bn` `:bp` | Buffer next/prev |
| `:s/old/new/` | Substitute |
| `:%s/old/new/g` | Global substitute |
| `:g/pattern/cmd` | Global command |
| `:set option` | Set option |
| `:help` | Show help |

## Helix-Style Features

### Multi-Cursor

| Key | Action |
|-----|--------|
| `C-n` | Add cursor below |
| `C-o` | Add cursor above |
| `S` | Split selection |
| `;` | Collapse selections |
| `Alt+;` | Flip selections |
| `%` | Select all |

### Object Selection

| Key | Action |
|-----|--------|
| `mi"` | Select inside quotes |
| `ma(` | Select around parens |
| `mI"` | Extend inside quotes |

## Configuration

Configuration is stored in `~/.config/markmark/config.json`.

### Example Configuration

```json
{
  "vim": {
    "enabled": true,
    "relative_line_numbers": true,
    "leader_key": "space"
  },
  "editor": {
    "font_family": "JetBrains Mono",
    "font_size": 12,
    "show_line_numbers": true,
    "auto_save": true
  },
  "zen": {
    "hide_menu_bar": true,
    "center_text": true,
    "max_line_width": 80
  },
  "markdown": {
    "live_preview": true,
    "render_math": true
  }
}
```

## Plugins

### Plugin Structure

```
my_plugin/
├── plugin.json    # Plugin metadata
├── plugin.py      # Plugin code
└── config.json    # Default config
```

### Plugin Example

```python
from core.plugin_system import PluginInterface, PluginMetadata, HookType

class MyPlugin(PluginInterface):
    @property
    def metadata(self):
        return PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            description="My custom plugin"
        )
    
    def activate(self, app):
        app.plugin_manager.register_hook(
            HookType.AFTER_SAVE,
            self.on_save
        )
    
    def deactivate(self, app):
        app.plugin_manager.unregister_hook(
            HookType.AFTER_SAVE,
            self.on_save
        )
    
    def on_save(self, filepath, **kwargs):
        print(f"Saved: {filepath}")
```

## Themes

Built-in themes:
- Dark+ (default)
- Monokai
- Solarized Dark/Light
- GitHub Dark/Light
- Dracula
- Nord
- Gruvbox Dark
- One Dark

Custom themes can be added to `~/.config/markmark/themes/`.

## Snippets

Built-in snippets include:
- Headings: `h1`, `h2`, `h3`
- Links: `link`, `img`
- Lists: `ul`, `ol`, `task`
- Code: `code`, `icode`
- Tables: `table`
- Formatting: `b`, `i`, `s`
- Math: `math`, `imath`
- Documents: `blog`, `readme`

Custom snippets can be added to `~/.config/markmark/snippets/`.

## Templates

Built-in templates:
- Empty Document
- Basic Markdown
- Blog Post
- README
- Technical Documentation
- Meeting Notes
- Journal Entry
- Tutorial
- Project Proposal
- Release Notes
- Book Chapter
- Letter

Custom templates can be added to `~/.config/markmark/templates/`.

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting PRs.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Inspired by:
- Vim/Neovim
- Helix
- KDE Kate
- VS Code
- Obsidian
- Typora
