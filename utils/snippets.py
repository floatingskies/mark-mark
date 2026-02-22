"""
Snippets system for MarkMark.
Provides text expansion and code snippets functionality.
"""

import re
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SnippetField:
    """A field in a snippet that can be filled."""
    name: str
    default: str = ""
    description: str = ""
    choices: List[str] = field(default_factory=list)
    transform: str = ""  # Transform to apply (uppercase, lowercase, capitalize, etc.)


@dataclass
class Snippet:
    """A text snippet with variable fields."""
    name: str
    trigger: str
    content: str
    description: str = ""
    category: str = "general"
    fields: List[SnippetField] = field(default_factory=list)
    scope: str = "markdown"  # markdown, python, javascript, etc.
    
    def expand(self, variables: Dict[str, str] = None) -> str:
        """Expand snippet with variables."""
        variables = variables or {}
        
        # Built-in variables
        builtins = {
            "CURRENT_YEAR": str(datetime.now().year),
            "CURRENT_MONTH": f"{datetime.now().month:02d}",
            "CURRENT_DAY": f"{datetime.now().day:02d}",
            "CURRENT_DATE": datetime.now().strftime("%Y-%m-%d"),
            "CURRENT_TIME": datetime.now().strftime("%H:%M:%S"),
            "CURRENT_DATETIME": datetime.now().isoformat(),
            "CLIPBOARD": "",  # Would be filled from clipboard
            "FILENAME": "",   # Would be filled from current file
            "LINE_NUMBER": "",  # Would be filled from cursor position
        }
        
        all_vars = {**builtins, **variables}
        
        result = self.content
        
        # Replace ${VAR} style variables
        for var_name, var_value in all_vars.items():
            result = result.replace(f"${{{var_name}}}", var_value)
            result = result.replace(f"${var_name}", var_value)
        
        # Handle field placeholders
        # ${1:default} -> default, ${2:name} -> name
        field_pattern = r'\$(\d+)(?::([^}]+))?(?:\|([^|}]+)\|)?'
        
        def replace_field(match):
            field_num = match.group(1)
            default = match.group(2) or ""
            choices = match.group(3)
            return default
        
        result = re.sub(field_pattern, replace_field, result)
        
        return result


class SnippetManager:
    """
    Manages snippet storage, expansion, and insertion.
    
    Features:
    - Multiple snippet sources
    - Variable expansion
    - Field navigation
    - Snippet categories
    - Import/Export
    """
    
    def __init__(self, snippet_dirs: List[str] = None):
        self.snippet_dirs = snippet_dirs or []
        self.snippets: Dict[str, Snippet] = {}
        self.categories: Dict[str, List[str]] = {}
        
        # Add default snippet directory
        default_dir = Path.home() / ".config" / "markmark" / "snippets"
        if str(default_dir) not in self.snippet_dirs:
            self.snippet_dirs.append(str(default_dir))
        
        # Initialize default snippets
        self._init_default_snippets()
        
        # Load snippets from directories
        self._load_snippets()
    
    def _init_default_snippets(self) -> None:
        """Initialize default markdown snippets."""
        
        # Headings
        self.add_snippet(Snippet(
            name="Heading 1",
            trigger="h1",
            content="# ${1:Title}",
            description="Level 1 heading",
            category="markdown",
        ))
        
        self.add_snippet(Snippet(
            name="Heading 2",
            trigger="h2",
            content="## ${1:Title}",
            description="Level 2 heading",
            category="markdown",
        ))
        
        self.add_snippet(Snippet(
            name="Heading 3",
            trigger="h3",
            content="### ${1:Title}",
            description="Level 3 heading",
            category="markdown",
        ))
        
        # Links
        self.add_snippet(Snippet(
            name="Link",
            trigger="link",
            content="[${1:link text}](${2:url})",
            description="Markdown link",
            category="markdown",
        ))
        
        self.add_snippet(Snippet(
            name="Image",
            trigger="img",
            content="![${1:alt text}](${2:image url})",
            description="Markdown image",
            category="markdown",
        ))
        
        # Lists
        self.add_snippet(Snippet(
            name="Bullet List",
            trigger="ul",
            content="- ${1:item}\n- ${2:item}\n- ${3:item}",
            description="Bullet list",
            category="markdown",
        ))
        
        self.add_snippet(Snippet(
            name="Numbered List",
            trigger="ol",
            content="1. ${1:item}\n2. ${2:item}\n3. ${3:item}",
            description="Numbered list",
            category="markdown",
        ))
        
        self.add_snippet(Snippet(
            name="Task List",
            trigger="task",
            content="- [ ] ${1:task}\n- [ ] ${2:task}\n- [ ] ${3:task}",
            description="Task list",
            category="markdown",
        ))
        
        # Code
        self.add_snippet(Snippet(
            name="Code Block",
            trigger="code",
            content="```${1:language}\n${2:code}\n```",
            description="Code block",
            category="markdown",
        ))
        
        self.add_snippet(Snippet(
            name="Inline Code",
            trigger="icode",
            content="`${1:code}`",
            description="Inline code",
            category="markdown",
        ))
        
        # Tables
        self.add_snippet(Snippet(
            name="Table",
            trigger="table",
            content="| ${1:Header 1} | ${2:Header 2} | ${3:Header 3} |\n|-------------|-------------|-------------|\n| ${4:Cell 1} | ${5:Cell 2} | ${6:Cell 3} |\n| ${7:Cell 4} | ${8:Cell 5} | ${9:Cell 6} |",
            description="Markdown table",
            category="markdown",
        ))
        
        # Blockquotes
        self.add_snippet(Snippet(
            name="Blockquote",
            trigger="quote",
            content="> ${1:quote}",
            description="Blockquote",
            category="markdown",
        ))
        
        # Horizontal rule
        self.add_snippet(Snippet(
            name="Horizontal Rule",
            trigger="hr",
            content="---",
            description="Horizontal rule",
            category="markdown",
        ))
        
        # Formatting
        self.add_snippet(Snippet(
            name="Bold",
            trigger="b",
            content="**${1:bold text}**",
            description="Bold text",
            category="markdown",
        ))
        
        self.add_snippet(Snippet(
            name="Italic",
            trigger="i",
            content="*${1:italic text}*",
            description="Italic text",
            category="markdown",
        ))
        
        self.add_snippet(Snippet(
            name="Strikethrough",
            trigger="s",
            content="~~${1:strikethrough text}~~",
            description="Strikethrough text",
            category="markdown",
        ))
        
        # Footnotes
        self.add_snippet(Snippet(
            name="Footnote",
            trigger="fn",
            content="[^${1:1}]\n\n[^${1:1}]: ${2:footnote text}",
            description="Footnote",
            category="markdown",
        ))
        
        # Definition list
        self.add_snippet(Snippet(
            name="Definition",
            trigger="def",
            content="${1:term}\n: ${2:definition}",
            description="Definition list item",
            category="markdown",
        ))
        
        # Abbreviation
        self.add_snippet(Snippet(
            name="Abbreviation",
            trigger="abbr",
            content="*[${1:ABBR}]: ${2:full text}",
            description="Abbreviation definition",
            category="markdown",
        ))
        
        # Math
        self.add_snippet(Snippet(
            name="Math Block",
            trigger="math",
            content="$$\n${1:equation}\n$$",
            description="Math block",
            category="markdown",
        ))
        
        self.add_snippet(Snippet(
            name="Inline Math",
            trigger="imath",
            content="$${1:equation}$$",
            description="Inline math",
            category="markdown",
        ))
        
        # Admonitions (GitHub-flavored)
        self.add_snippet(Snippet(
            name="Note Admonition",
            trigger="note",
            content="> [!NOTE]\n> ${1:note content}",
            description="Note admonition",
            category="markdown",
        ))
        
        self.add_snippet(Snippet(
            name="Warning Admonition",
            trigger="warning",
            content="> [!WARNING]\n> ${1:warning content}",
            description="Warning admonition",
            category="markdown",
        ))
        
        # Frontmatter
        self.add_snippet(Snippet(
            name="YAML Frontmatter",
            trigger="frontmatter",
            content="---\ntitle: ${1:Title}\nauthor: ${2:Author}\ndate: ${CURRENT_DATE}\ntags: [${3:tag1, tag2}]\n---\n",
            description="YAML frontmatter",
            category="markdown",
        ))
        
        # Document templates
        self.add_snippet(Snippet(
            name="Blog Post",
            trigger="blog",
            content="""---
title: ${1:Title}
date: ${CURRENT_DATE}
author: ${2:Author}
tags: [${3:tag1, tag2}]
---

# $1

${4:Introduction}

## Overview

${5:Content}

## Conclusion

${6:Conclusion}
""",
            description="Blog post template",
            category="document",
        ))
        
        self.add_snippet(Snippet(
            name="README",
            trigger="readme",
            content="""# ${1:Project Name}

${2:Short description}

## Installation

```
${3:installation command}
```

## Usage

```
${4:usage example}
```

## Features

- ${5:Feature 1}
- ${6:Feature 2}

## License

${7:MIT}
""",
            description="README template",
            category="document",
        ))
        
        # Code snippets
        self.add_snippet(Snippet(
            name="Python Function",
            trigger="pyfunc",
            content="def ${1:function_name}(${2:args}):\n    \"\"\"${3:Docstring}\"\"\"\n    ${4:pass}",
            description="Python function",
            category="python",
            scope="python",
        ))
        
        self.add_snippet(Snippet(
            name="JavaScript Function",
            trigger="jsfunc",
            content="function ${1:functionName}(${2:args}) {\n    ${3:// body}\n}",
            description="JavaScript function",
            category="javascript",
            scope="javascript",
        ))
    
    def _load_snippets(self) -> None:
        """Load snippets from snippet directories."""
        for snippet_dir in self.snippet_dirs:
            snippet_path = Path(snippet_dir)
            if not snippet_path.exists():
                continue
            
            for file in snippet_path.rglob("*.json"):
                try:
                    with open(file) as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        for snippet_data in data:
                            self._load_snippet_dict(snippet_data)
                    else:
                        self._load_snippet_dict(data)
                        
                except Exception as e:
                    print(f"Error loading snippets from {file}: {e}")
    
    def _load_snippet_dict(self, data: dict) -> None:
        """Load a snippet from dictionary."""
        snippet = Snippet(
            name=data.get("name", "Unnamed"),
            trigger=data.get("trigger", ""),
            content=data.get("content", ""),
            description=data.get("description", ""),
            category=data.get("category", "general"),
            scope=data.get("scope", "markdown"),
        )
        self.add_snippet(snippet)
    
    def add_snippet(self, snippet: Snippet) -> None:
        """Add a snippet."""
        self.snippets[snippet.trigger] = snippet
        
        if snippet.category not in self.categories:
            self.categories[snippet.category] = []
        self.categories[snippet.category].append(snippet.trigger)
    
    def remove_snippet(self, trigger: str) -> bool:
        """Remove a snippet by trigger."""
        if trigger in self.snippets:
            snippet = self.snippets[trigger]
            if snippet.category in self.categories:
                self.categories[snippet.category] = [
                    t for t in self.categories[snippet.category] if t != trigger
                ]
            del self.snippets[trigger]
            return True
        return False
    
    def get_snippet(self, trigger: str) -> Optional[Snippet]:
        """Get a snippet by trigger."""
        return self.snippets.get(trigger)
    
    def expand_snippet(self, trigger: str, variables: Dict[str, str] = None) -> Optional[str]:
        """Expand a snippet by trigger."""
        snippet = self.get_snippet(trigger)
        if snippet:
            return snippet.expand(variables)
        return None
    
    def get_snippets_by_category(self, category: str) -> List[Snippet]:
        """Get all snippets in a category."""
        triggers = self.categories.get(category, [])
        return [self.snippets[t] for t in triggers if t in self.snippets]
    
    def get_all_triggers(self) -> List[str]:
        """Get all snippet triggers."""
        return list(self.snippets.keys())
    
    def search_snippets(self, query: str) -> List[Snippet]:
        """Search snippets by name, trigger, or description."""
        query_lower = query.lower()
        results = []
        
        for snippet in self.snippets.values():
            if (query_lower in snippet.name.lower() or
                query_lower in snippet.trigger.lower() or
                query_lower in snippet.description.lower()):
                results.append(snippet)
        
        return results
    
    def save_snippet(self, snippet: Snippet, filepath: str = None) -> bool:
        """Save a snippet to file."""
        filepath = filepath or str(
            Path(self.snippet_dirs[0]) / f"{snippet.trigger}.json"
        )
        
        try:
            data = {
                "name": snippet.name,
                "trigger": snippet.trigger,
                "content": snippet.content,
                "description": snippet.description,
                "category": snippet.category,
                "scope": snippet.scope,
            }
            
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving snippet: {e}")
            return False
    
    def export_snippets(self, filepath: str, category: str = None) -> bool:
        """Export snippets to a JSON file."""
        try:
            snippets = (
                self.get_snippets_by_category(category)
                if category else list(self.snippets.values())
            )
            
            data = [
                {
                    "name": s.name,
                    "trigger": s.trigger,
                    "content": s.content,
                    "description": s.description,
                    "category": s.category,
                    "scope": s.scope,
                }
                for s in snippets
            ]
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting snippets: {e}")
            return False
    
    def import_snippets(self, filepath: str) -> int:
        """Import snippets from a JSON file."""
        try:
            with open(filepath) as f:
                data = json.load(f)
            
            count = 0
            snippets = data if isinstance(data, list) else [data]
            
            for snippet_data in snippets:
                self._load_snippet_dict(snippet_data)
                count += 1
            
            return count
        except Exception as e:
            print(f"Error importing snippets: {e}")
            return 0


__all__ = ['Snippet', 'SnippetField', 'SnippetManager']
