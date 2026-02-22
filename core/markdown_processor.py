"""
Markdown processing and rendering for MarkMark.
Provides syntax highlighting, live preview, and export capabilities.
"""

import re
import html
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    """Types of markdown tokens."""
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    CODE_BLOCK = "code_block"
    CODE_INLINE = "code_inline"
    BOLD = "bold"
    ITALIC = "italic"
    STRIKETHROUGH = "strikethrough"
    LINK = "link"
    IMAGE = "image"
    LIST_ORDERED = "list_ordered"
    LIST_UNORDERED = "list_unordered"
    BLOCKQUOTE = "blockquote"
    HORIZONTAL_RULE = "horizontal_rule"
    TABLE = "table"
    MATH_BLOCK = "math_block"
    MATH_INLINE = "math_inline"
    FOOTNOTE = "footnote"
    DEFINITION_LIST = "definition_list"
    TASK_LIST = "task_list"
    HTML = "html"
    FRONTMATTER = "frontmatter"
    TEXT = "text"
    NEWLINE = "newline"
    ESCAPE = "escape"


@dataclass
class Token:
    """A markdown token."""
    type: TokenType
    content: str
    start: int
    end: int
    level: int = 0
    meta: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.meta is None:
            self.meta = {}


class MarkdownLexer:
    """Tokenizes markdown content."""
    
    def __init__(self):
        self.pos = 0
        self.tokens: List[Token] = []
        self.content = ""
    
    def tokenize(self, content: str) -> List[Token]:
        """Tokenize markdown content."""
        self.content = content
        self.pos = 0
        self.tokens = []
        
        while self.pos < len(content):
            # Check for frontmatter (YAML)
            if self.pos == 0 and content.startswith('---\n'):
                self._parse_frontmatter()
            # Check for code blocks first
            elif content[self.pos:].startswith('```'):
                self._parse_code_block()
            # Check for math blocks
            elif content[self.pos:].startswith('$$'):
                self._parse_math_block()
            # Check for headings
            elif content[self.pos] == '#' and (self.pos == 0 or content[self.pos-1] == '\n'):
                self._parse_heading()
            # Check for horizontal rule
            elif self._is_horizontal_rule():
                self._parse_horizontal_rule()
            # Check for blockquote
            elif content[self.pos] == '>' and (self.pos == 0 or content[self.pos-1] == '\n'):
                self._parse_blockquote()
            # Check for list items
            elif self._is_list_start():
                self._parse_list()
            # Check for table
            elif self._is_table_start():
                self._parse_table()
            # Check for HTML
            elif content[self.pos] == '<':
                self._parse_html()
            # Otherwise, parse inline content
            else:
                self._parse_paragraph()
        
        return self.tokens
    
    def _parse_frontmatter(self) -> None:
        """Parse YAML frontmatter."""
        start = self.pos
        self.pos += 4  # Skip ---
        
        end = self.content.find('\n---\n', self.pos)
        if end == -1:
            end = len(self.content)
        else:
            end += 5
        
        self.tokens.append(Token(
            TokenType.FRONTMATTER,
            self.content[start:end],
            start,
            end
        ))
        self.pos = end
    
    def _parse_code_block(self) -> None:
        """Parse a code block."""
        start = self.pos
        self.pos += 3  # Skip ```
        
        # Get language
        lang_end = self.content.find('\n', self.pos)
        language = ""
        if lang_end != -1:
            language = self.content[self.pos:lang_end].strip()
            self.pos = lang_end + 1
        
        # Find end
        end_marker = self.content.find('\n```', self.pos)
        if end_marker == -1:
            end_marker = len(self.content)
        else:
            end_marker += 4
        
        self.tokens.append(Token(
            TokenType.CODE_BLOCK,
            self.content[start:end_marker],
            start,
            end_marker,
            meta={"language": language}
        ))
        self.pos = end_marker
    
    def _parse_math_block(self) -> None:
        """Parse a math block."""
        start = self.pos
        self.pos += 2  # Skip $$
        
        end_marker = self.content.find('$$', self.pos)
        if end_marker == -1:
            end_marker = len(self.content)
        else:
            end_marker += 2
        
        self.tokens.append(Token(
            TokenType.MATH_BLOCK,
            self.content[start:end_marker],
            start,
            end_marker
        ))
        self.pos = end_marker
    
    def _parse_heading(self) -> None:
        """Parse a heading."""
        start = self.pos
        level = 0
        
        while self.pos < len(self.content) and self.content[self.pos] == '#':
            level += 1
            self.pos += 1
        
        # Skip space
        if self.pos < len(self.content) and self.content[self.pos] == ' ':
            self.pos += 1
        
        # Get content until newline
        end = self.content.find('\n', self.pos)
        if end == -1:
            end = len(self.content)
        
        content = self.content[start:end]
        self.tokens.append(Token(
            TokenType.HEADING,
            content,
            start,
            end,
            level=level
        ))
        self.pos = end
    
    def _is_horizontal_rule(self) -> bool:
        """Check if current position starts a horizontal rule."""
        if self.pos > 0 and self.content[self.pos-1] != '\n':
            return False
        
        line_end = self.content.find('\n', self.pos)
        if line_end == -1:
            line_end = len(self.content)
        
        line = self.content[self.pos:line_end].strip()
        
        # Check for ---, ***, ___
        if len(line) >= 3:
            if all(c == '-' for c in line) or \
               all(c == '*' for c in line) or \
               all(c == '_' for c in line):
                return True
        
        return False
    
    def _parse_horizontal_rule(self) -> None:
        """Parse a horizontal rule."""
        start = self.pos
        end = self.content.find('\n', self.pos)
        if end == -1:
            end = len(self.content)
        else:
            end += 1
        
        self.tokens.append(Token(
            TokenType.HORIZONTAL_RULE,
            self.content[start:end],
            start,
            end
        ))
        self.pos = end
    
    def _parse_blockquote(self) -> None:
        """Parse a blockquote."""
        start = self.pos
        lines = []
        
        while self.pos < len(self.content):
            if self.content[self.pos] == '>':
                line_end = self.content.find('\n', self.pos)
                if line_end == -1:
                    line_end = len(self.content)
                
                line = self.content[self.pos:line_end]
                # Remove > prefix
                line = line[1:].lstrip()
                lines.append(line)
                self.pos = line_end + 1
            else:
                break
        
        self.tokens.append(Token(
            TokenType.BLOCKQUOTE,
            '\n'.join(lines),
            start,
            self.pos
        ))
    
    def _is_list_start(self) -> bool:
        """Check if current position starts a list."""
        if self.pos > 0 and self.content[self.pos-1] != '\n':
            return False
        
        # Check for ordered list: 1. or 1)
        ordered_match = re.match(r'\d+[.)]\s', self.content[self.pos:])
        if ordered_match:
            return True
        
        # Check for unordered list: -, *, +
        if self.pos < len(self.content):
            char = self.content[self.pos]
            if char in '-*+':
                if self.pos + 1 < len(self.content) and self.content[self.pos+1] == ' ':
                    # Make sure it's not a horizontal rule
                    line_end = self.content.find('\n', self.pos)
                    line = self.content[self.pos:line_end].strip() if line_end != -1 else self.content[self.pos:].strip()
                    if not all(c == line[0] for c in line):
                        return True
        
        # Check for task list
        if re.match(r'-\s+\[[x\s]\]', self.content[self.pos:]):
            return True
        
        return False
    
    def _parse_list(self) -> None:
        """Parse a list."""
        start = self.pos
        items = []
        is_ordered = False
        is_task = False
        
        while self.pos < len(self.content):
            if self.pos > 0 and self.content[self.pos-1] != '\n' and self.pos != start:
                break
            
            line_end = self.content.find('\n', self.pos)
            if line_end == -1:
                line_end = len(self.content)
            
            line = self.content[self.pos:line_end]
            
            # Check for ordered list item
            ordered_match = re.match(r'(\d+[.)])\s+(.*)', line)
            if ordered_match:
                is_ordered = True
                items.append(ordered_match.group(2))
                self.pos = line_end + 1
                continue
            
            # Check for task list item
            task_match = re.match(r'(-)\s+\[([x\s])\]\s+(.*)', line)
            if task_match:
                is_task = True
                items.append({
                    'checked': task_match.group(2) == 'x',
                    'text': task_match.group(3)
                })
                self.pos = line_end + 1
                continue
            
            # Check for unordered list item
            unordered_match = re.match(r'([-*+])\s+(.*)', line)
            if unordered_match:
                items.append(unordered_match.group(2))
                self.pos = line_end + 1
                continue
            
            # Check for continuation line (indented)
            if line.startswith('  ') or line.startswith('\t'):
                if items:
                    if isinstance(items[-1], dict):
                        items[-1]['text'] += '\n' + line.strip()
                    else:
                        items[-1] += '\n' + line.strip()
                    self.pos = line_end + 1
                    continue
            
            break
        
        token_type = TokenType.TASK_LIST if is_task else \
                    (TokenType.LIST_ORDERED if is_ordered else TokenType.LIST_UNORDERED)
        
        self.tokens.append(Token(
            token_type,
            items,
            start,
            self.pos,
            meta={"is_task": is_task, "is_ordered": is_ordered}
        ))
    
    def _is_table_start(self) -> bool:
        """Check if current position starts a table."""
        if self.pos > 0 and self.content[self.pos-1] != '\n':
            return False
        
        # Look for | in first line and |-| in second
        line1_end = self.content.find('\n', self.pos)
        if line1_end == -1:
            return False
        
        line1 = self.content[self.pos:line1_end]
        if '|' not in line1:
            return False
        
        line2_end = self.content.find('\n', line1_end + 1)
        if line2_end == -1:
            return False
        
        line2 = self.content[line1_end+1:line2_end]
        return bool(re.match(r'^[\s|:-]+$', line2))
    
    def _parse_table(self) -> None:
        """Parse a table."""
        start = self.pos
        rows = []
        
        while self.pos < len(self.content):
            if self.pos > 0 and self.content[self.pos-1] != '\n' and self.pos != start:
                break
            
            line_end = self.content.find('\n', self.pos)
            if line_end == -1:
                line_end = len(self.content)
            
            line = self.content[self.pos:line_end]
            
            # Check if it's a table row
            if '|' in line or line.strip().startswith('|'):
                cells = [c.strip() for c in line.strip('|').split('|')]
                
                # Skip separator row
                if not all(re.match(r'^[-:]+$', c) for c in cells):
                    rows.append(cells)
                self.pos = line_end + 1
            else:
                break
        
        self.tokens.append(Token(
            TokenType.TABLE,
            rows,
            start,
            self.pos
        ))
    
    def _parse_html(self) -> None:
        """Parse HTML content."""
        start = self.pos
        
        # Check for HTML block
        html_end = re.search(r'</\w+>\s*\n', self.content[self.pos:])
        if html_end:
            end = self.pos + html_end.end()
        else:
            # Just a single tag
            tag_end = self.content.find('>', self.pos)
            if tag_end == -1:
                tag_end = len(self.content)
            end = tag_end + 1
        
        self.tokens.append(Token(
            TokenType.HTML,
            self.content[start:end],
            start,
            end
        ))
        self.pos = end
    
    def _parse_paragraph(self) -> None:
        """Parse a paragraph or inline content."""
        start = self.pos
        
        # Collect until blank line or block element
        while self.pos < len(self.content):
            # Check for end of paragraph
            if self.content[self.pos:].startswith('\n\n'):
                break
            if self.content[self.pos:].startswith('```'):
                break
            if self.content[self.pos:].startswith('$$'):
                break
            if self.content[self.pos] == '#' and (self.pos == 0 or self.content[self.pos-1] == '\n'):
                break
            if self._is_horizontal_rule():
                break
            
            self.pos += 1
        
        content = self.content[start:self.pos].strip()
        if content:
            self.tokens.append(Token(
                TokenType.PARAGRAPH,
                content,
                start,
                self.pos
            ))
        
        # Skip trailing whitespace
        while self.pos < len(self.content) and self.content[self.pos] in ' \t':
            self.pos += 1
        if self.pos < len(self.content) and self.content[self.pos] == '\n':
            self.pos += 1


class MarkdownParser:
    """Parses markdown tokens into an AST-like structure."""
    
    def __init__(self):
        self.lexer = MarkdownLexer()
    
    def parse(self, content: str) -> List[Token]:
        """Parse markdown content into tokens."""
        tokens = self.lexer.tokenize(content)
        return self._process_inline(tokens)
    
    def _process_inline(self, tokens: List[Token]) -> List[Token]:
        """Process inline formatting within block tokens."""
        result = []
        
        for token in tokens:
            if token.type in (TokenType.PARAGRAPH, TokenType.HEADING):
                # Parse inline elements
                inline_tokens = self._parse_inline(token.content, token.start)
                if inline_tokens:
                    token.meta['inline'] = inline_tokens
            result.append(token)
        
        return result
    
    def _parse_inline(self, content: str, offset: int) -> List[Token]:
        """Parse inline markdown elements."""
        tokens = []
        i = 0
        
        while i < len(content):
            # Escape
            if content[i] == '\\' and i + 1 < len(content):
                tokens.append(Token(
                    TokenType.ESCAPE,
                    content[i+1],
                    offset + i,
                    offset + i + 2
                ))
                i += 2
                continue
            
            # Code inline
            if content[i] == '`':
                end = content.find('`', i + 1)
                if end != -1:
                    tokens.append(Token(
                        TokenType.CODE_INLINE,
                        content[i+1:end],
                        offset + i,
                        offset + end + 1
                    ))
                    i = end + 1
                    continue
            
            # Bold/Italic
            if content[i] in '*_':
                # Check for bold
                if i + 1 < len(content) and content[i+1] == content[i]:
                    end = content.find(content[i]*2, i + 2)
                    if end != -1:
                        tokens.append(Token(
                            TokenType.BOLD,
                            content[i+2:end],
                            offset + i,
                            offset + end + 2
                        ))
                        i = end + 2
                        continue
                # Check for italic
                else:
                    end = content.find(content[i], i + 1)
                    if end != -1 and content[end-1] != content[i]:
                        tokens.append(Token(
                            TokenType.ITALIC,
                            content[i+1:end],
                            offset + i,
                            offset + end + 1
                        ))
                        i = end + 1
                        continue
            
            # Strikethrough
            if content[i:i+2] == '~~':
                end = content.find('~~', i + 2)
                if end != -1:
                    tokens.append(Token(
                        TokenType.STRIKETHROUGH,
                        content[i+2:end],
                        offset + i,
                        offset + end + 2
                    ))
                    i = end + 2
                    continue
            
            # Math inline
            if content[i] == '$' and (i == 0 or content[i-1] != '$'):
                end = content.find('$', i + 1)
                if end != -1:
                    tokens.append(Token(
                        TokenType.MATH_INLINE,
                        content[i+1:end],
                        offset + i,
                        offset + end + 1
                    ))
                    i = end + 1
                    continue
            
            # Link
            if content[i] == '[':
                link_match = re.match(r'\[([^\]]+)\]\(([^)]+)\)', content[i:])
                if link_match:
                    tokens.append(Token(
                        TokenType.LINK,
                        link_match.group(1),
                        offset + i,
                        offset + i + len(link_match.group(0)),
                        meta={'url': link_match.group(2)}
                    ))
                    i += len(link_match.group(0))
                    continue
            
            # Image
            if content[i:i+2] == '![':
                img_match = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', content[i:])
                if img_match:
                    tokens.append(Token(
                        TokenType.IMAGE,
                        img_match.group(1),
                        offset + i,
                        offset + i + len(img_match.group(0)),
                        meta={'url': img_match.group(2)}
                    ))
                    i += len(img_match.group(0))
                    continue
            
            # Footnote reference
            if content[i] == '[' and content[i+1:i+2] == '^':
                fn_match = re.match(r'\[\^([^\]]+)\]', content[i:])
                if fn_match:
                    tokens.append(Token(
                        TokenType.FOOTNOTE,
                        fn_match.group(1),
                        offset + i,
                        offset + i + len(fn_match.group(0))
                    ))
                    i += len(fn_match.group(0))
                    continue
            
            i += 1
        
        return tokens


class MarkdownRenderer:
    """Renders markdown tokens to HTML."""
    
    def __init__(self):
        self.parser = MarkdownParser()
    
    def render(self, content: str) -> str:
        """Render markdown content to HTML."""
        tokens = self.parser.parse(content)
        html_parts = []
        
        for token in tokens:
            html_parts.append(self._render_token(token))
        
        return '\n'.join(html_parts)
    
    def _render_token(self, token: Token) -> str:
        """Render a single token to HTML."""
        if token.type == TokenType.HEADING:
            return f'<h{token.level}>{self._render_inline(token)}</h{token.level}>'
        
        elif token.type == TokenType.PARAGRAPH:
            return f'<p>{self._render_inline(token)}</p>'
        
        elif token.type == TokenType.CODE_BLOCK:
            lang = token.meta.get('language', '')
            code = html.escape(token.content.split('\n', 1)[-1].rstrip('`').strip())
            if lang:
                return f'<pre><code class="language-{lang}">{code}</code></pre>'
            return f'<pre><code>{code}</code></pre>'
        
        elif token.type == TokenType.MATH_BLOCK:
            math = html.escape(token.content.strip('$'))
            return f'<div class="math-display">$${math}$$</div>'
        
        elif token.type == TokenType.BLOCKQUOTE:
            return f'<blockquote>{self._render_inline_content(token.content)}</blockquote>'
        
        elif token.type == TokenType.HORIZONTAL_RULE:
            return '<hr>'
        
        elif token.type == TokenType.LIST_ORDERED:
            items = '\n'.join(f'<li>{self._render_inline_content(item)}</li>' for item in token.content)
            return f'<ol>\n{items}\n</ol>'
        
        elif token.type == TokenType.LIST_UNORDERED:
            items = '\n'.join(f'<li>{self._render_inline_content(item)}</li>' for item in token.content)
            return f'<ul>\n{items}\n</ul>'
        
        elif token.type == TokenType.TASK_LIST:
            items = []
            for item in token.content:
                checked = 'checked' if item.get('checked') else ''
                items.append(f'<li><input type="checkbox" {checked} disabled>{self._render_inline_content(item["text"])}</li>')
            return f'<ul class="task-list">\n{"".join(items)}\n</ul>'
        
        elif token.type == TokenType.TABLE:
            if token.content:
                header = '<tr>' + ''.join(f'<th>{self._render_inline_content(cell)}</th>' for cell in token.content[0]) + '</tr>'
                body = []
                for row in token.content[1:]:
                    body.append('<tr>' + ''.join(f'<td>{self._render_inline_content(cell)}</td>' for cell in row) + '</tr>')
                return f'<table>\n<thead>\n{header}\n</thead>\n<tbody>\n{"".join(body)}\n</tbody>\n</table>'
            return '<table></table>'
        
        elif token.type == TokenType.FRONTMATTER:
            return f'<div class="frontmatter"><pre>{html.escape(token.content)}</pre></div>'
        
        elif token.type == TokenType.HTML:
            return token.content
        
        return ''
    
    def _render_inline(self, token: Token) -> str:
        """Render inline content within a block token."""
        inline_tokens = token.meta.get('inline', [])
        if not inline_tokens:
            return self._render_inline_content(token.content)
        
        # Build HTML with inline formatting
        result = token.content
        offset = token.start
        
        # Process inline tokens in reverse to maintain positions
        for inline in reversed(inline_tokens):
            start = inline.start - offset
            end = inline.end - offset
            
            if inline.type == TokenType.BOLD:
                result = result[:start] + f'<strong>{inline.content}</strong>' + result[end:]
            elif inline.type == TokenType.ITALIC:
                result = result[:start] + f'<em>{inline.content}</em>' + result[end:]
            elif inline.type == TokenType.STRIKETHROUGH:
                result = result[:start] + f'<del>{inline.content}</del>' + result[end:]
            elif inline.type == TokenType.CODE_INLINE:
                result = result[:start] + f'<code>{html.escape(inline.content)}</code>' + result[end:]
            elif inline.type == TokenType.LINK:
                result = result[:start] + f'<a href="{inline.meta["url"]}">{inline.content}</a>' + result[end:]
            elif inline.type == TokenType.IMAGE:
                result = result[:start] + f'<img src="{inline.meta["url"]}" alt="{inline.content}">' + result[end:]
            elif inline.type == TokenType.MATH_INLINE:
                result = result[:start] + f'<span class="math-inline">${inline.content}$</span>' + result[end:]
            elif inline.type == TokenType.FOOTNOTE:
                result = result[:start] + f'<sup><a href="#fn-{inline.content}">{inline.content}</a></sup>' + result[end:]
        
        return result
    
    def _render_inline_content(self, content: str) -> str:
        """Render inline content directly."""
        # Simple inline rendering for complex content
        # Bold
        content = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', content)
        
        # Italic
        content = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', content)
        content = re.sub(r'_([^_]+)_', r'<em>\1</em>', content)
        
        # Strikethrough
        content = re.sub(r'~~([^~]+)~~', r'<del>\1</del>', content)
        
        # Code
        content = re.sub(r'`([^`]+)`', r'<code>\1</code>', content)
        
        # Links
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', content)
        
        # Images
        content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', content)
        
        return content


class MarkdownHighlighter:
    """Provides syntax highlighting information for the editor."""
    
    def __init__(self):
        self.parser = MarkdownParser()
    
    def get_highlights(self, content: str) -> List[Tuple[int, int, str]]:
        """
        Get highlighting information for content.
        Returns list of (start, end, style_name) tuples.
        """
        tokens = self.parser.parse(content)
        highlights = []
        
        for token in tokens:
            if token.type == TokenType.HEADING:
                # Highlight the # characters
                hash_count = token.level
                highlights.append((token.start, token.start + hash_count, 'markdown_heading_marker'))
                highlights.append((token.start + hash_count, token.end, f'markdown_heading_{token.level}'))
            
            elif token.type == TokenType.CODE_BLOCK:
                highlights.append((token.start, token.end, 'markdown_code_block'))
            
            elif token.type == TokenType.MATH_BLOCK:
                highlights.append((token.start, token.end, 'markdown_math'))
            
            elif token.type == TokenType.HORIZONTAL_RULE:
                highlights.append((token.start, token.end, 'markdown_hr'))
            
            elif token.type == TokenType.BLOCKQUOTE:
                highlights.append((token.start, token.end, 'markdown_blockquote'))
            
            elif token.type == TokenType.LINK:
                highlights.append((token.start, token.end, 'markdown_link'))
            
            elif token.type == TokenType.IMAGE:
                highlights.append((token.start, token.end, 'markdown_image'))
            
            # Process inline tokens
            inline_tokens = token.meta.get('inline', [])
            for inline in inline_tokens:
                style = f'markdown_{inline.type.value}'
                highlights.append((inline.start, inline.end, style))
        
        return highlights


class MarkdownExporter:
    """Export markdown to various formats."""
    
    def __init__(self):
        self.renderer = MarkdownRenderer()
    
    def to_html(self, content: str, include_css: bool = True) -> str:
        """Export to HTML."""
        body = self.renderer.render(content)
        
        if include_css:
            css = self._get_default_css()
            return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{css}
</style>
</head>
<body>
{body}
</body>
</html>'''
        
        return body
    
    def to_pdf(self, content: str, output_path: str) -> bool:
        """Export to PDF (requires wkhtmltopdf or similar)."""
        # This would require external tool integration
        # For now, return False to indicate not implemented
        return False
    
    def to_docx(self, content: str, output_path: str) -> bool:
        """Export to DOCX (requires python-docx)."""
        # This would require python-docx library
        return False
    
    def _get_default_css(self) -> str:
        """Get default CSS for HTML export."""
        return '''
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    line-height: 1.6;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    color: #333;
}

h1, h2, h3, h4, h5, h6 {
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    line-height: 1.3;
}

h1 { font-size: 2em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
h2 { font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
h3 { font-size: 1.25em; }
h4 { font-size: 1em; }

code {
    background: #f4f4f4;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: 'Consolas', 'Monaco', monospace;
}

pre {
    background: #f8f8f8;
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 1em;
    overflow-x: auto;
}

pre code {
    background: none;
    padding: 0;
}

blockquote {
    border-left: 4px solid #ddd;
    padding-left: 1em;
    margin-left: 0;
    color: #666;
}

table {
    border-collapse: collapse;
    width: 100%;
}

th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}

th {
    background: #f4f4f4;
}

img {
    max-width: 100%;
}

hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 2em 0;
}

.task-list {
    list-style: none;
    padding-left: 0;
}

.task-list input {
    margin-right: 0.5em;
}
'''


# Export classes
__all__ = [
    'TokenType',
    'Token',
    'MarkdownLexer',
    'MarkdownParser',
    'MarkdownRenderer',
    'MarkdownHighlighter',
    'MarkdownExporter',
]
