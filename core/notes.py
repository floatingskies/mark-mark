"""
Note-taking system for MarkMark.
Provides organization, tagging, linking, and search for notes.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


class NoteCategory(Enum):
    """Note categories."""
    GENERAL = "general"
    WORK = "work"
    PERSONAL = "personal"
    IDEAS = "ideas"
    RESEARCH = "research"
    JOURNAL = "journal"
    PROJECT = "project"
    MEETING = "meeting"
    REFERENCE = "reference"
    ARCHIVE = "archive"


@dataclass
class NoteMetadata:
    """Metadata for a note."""
    title: str
    created: str
    modified: str
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    pinned: bool = False
    favorite: bool = False
    archived: bool = False
    template: str = ""
    uuid: str = ""
    
    def __post_init__(self):
        if not self.uuid:
            self.uuid = self._generate_uuid()
    
    @staticmethod
    def _generate_uuid() -> str:
        """Generate a unique ID."""
        import time
        return hashlib.md5(f"{time.time()}{os.urandom(8)}".encode()).hexdigest()[:12]


@dataclass
class Note:
    """A note with content and metadata."""
    metadata: NoteMetadata
    content: str
    path: str = ""
    
    @property
    def title(self) -> str:
        return self.metadata.title
    
    @property
    def tags(self) -> List[str]:
        return self.metadata.tags
    
    @property
    def category(self) -> str:
        return self.metadata.category
    
    @property
    def created(self) -> datetime:
        return datetime.fromisoformat(self.metadata.created)
    
    @property
    def modified(self) -> datetime:
        return datetime.fromisoformat(self.metadata.modified)


@dataclass
class NoteLink:
    """A link between notes."""
    source_uuid: str
    target_uuid: str
    link_type: str = "reference"  # reference, parent, child, related
    created: str = ""
    
    def __post_init__(self):
        if not self.created:
            self.created = datetime.now().isoformat()


class NoteIndex:
    """Index for fast note searching."""
    
    def __init__(self):
        self.title_index: Dict[str, Set[str]] = {}  # title words -> note uuids
        self.tag_index: Dict[str, Set[str]] = {}    # tag -> note uuids
        self.content_index: Dict[str, Set[str]] = {}  # content words -> note uuids
        self.category_index: Dict[str, Set[str]] = {}  # category -> note uuids
        self.date_index: Dict[str, Set[str]] = {}   # date string -> note uuids
    
    def add_note(self, note: Note) -> None:
        """Add a note to the index."""
        uuid = note.metadata.uuid
        
        # Index title words
        title_words = self._tokenize(note.title)
        for word in title_words:
            if word not in self.title_index:
                self.title_index[word] = set()
            self.title_index[word].add(uuid)
        
        # Index tags
        for tag in note.tags:
            tag_lower = tag.lower()
            if tag_lower not in self.tag_index:
                self.tag_index[tag_lower] = set()
            self.tag_index[tag_lower].add(uuid)
        
        # Index content words
        content_words = self._tokenize(note.content)
        for word in content_words:
            if word not in self.content_index:
                self.content_index[word] = set()
            self.content_index[word].add(uuid)
        
        # Index category
        cat = note.category.lower()
        if cat not in self.category_index:
            self.category_index[cat] = set()
        self.category_index[cat].add(uuid)
        
        # Index date
        date_str = note.metadata.created[:10]  # YYYY-MM-DD
        if date_str not in self.date_index:
            self.date_index[date_str] = set()
        self.date_index[date_str].add(uuid)
    
    def remove_note(self, note: Note) -> None:
        """Remove a note from the index."""
        uuid = note.metadata.uuid
        
        # Remove from all indexes
        for index in [self.title_index, self.tag_index, self.content_index, 
                      self.category_index, self.date_index]:
            for word, uuids in list(index.items()):
                uuids.discard(uuid)
                if not uuids:
                    del index[word]
    
    def search(self, query: str, search_type: str = "all") -> Set[str]:
        """Search for notes matching query."""
        results: Optional[Set[str]] = None
        words = self._tokenize(query)
        
        for word in words:
            word_results: Set[str] = set()
            
            if search_type in ("all", "title"):
                word_results.update(self.title_index.get(word, set()))
            
            if search_type in ("all", "content"):
                word_results.update(self.content_index.get(word, set()))
            
            if search_type in ("all", "tag"):
                word_results.update(self.tag_index.get(word, set()))
            
            if results is None:
                results = word_results
            else:
                results &= word_results  # AND search
        
        return results or set()
    
    def search_by_tag(self, tag: str) -> Set[str]:
        """Search notes by tag."""
        return self.tag_index.get(tag.lower(), set())
    
    def search_by_category(self, category: str) -> Set[str]:
        """Search notes by category."""
        return self.category_index.get(category.lower(), set())
    
    def search_by_date(self, date_str: str) -> Set[str]:
        """Search notes by date."""
        return self.date_index.get(date_str, set())
    
    def get_all_tags(self) -> List[str]:
        """Get all tags used."""
        return sorted(self.tag_index.keys())
    
    def get_tag_counts(self) -> Dict[str, int]:
        """Get tag usage counts."""
        return {tag: len(uuids) for tag, uuids in self.tag_index.items()}
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for indexing."""
        # Remove markdown formatting
        text = re.sub(r'[#*_`\[\]()]', ' ', text)
        # Split on non-alphanumeric
        words = re.findall(r'\b\w{2,}\b', text.lower())
        return words


class NoteManager:
    """
    Manages the note-taking system.
    
    Features:
    - Note organization by category and tags
    - Wiki-style linking between notes
    - Full-text search
    - Templates
    - Automatic organization
    - Import/export
    """
    
    def __init__(self, notes_dir: str = None, config=None):
        self.config = config
        self.notes_dir = Path(notes_dir) if notes_dir else Path.home() / ".config" / "markmark" / "notes"
        self.notes: Dict[str, Note] = {}
        self.links: List[NoteLink] = []
        self.index = NoteIndex()
        self.templates: Dict[str, str] = {}
        
        # Ensure directory exists
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        for category in NoteCategory:
            (self.notes_dir / category.value).mkdir(exist_ok=True)
        
        # Initialize default templates
        self._init_templates()
        
        # Load existing notes
        self._load_notes()
    
    def _init_templates(self) -> None:
        """Initialize default note templates."""
        self.templates = {
            "default": "# {title}\n\n",
            "meeting": "# {title}\n\n**Date:** {date}\n**Attendees:** \n\n## Agenda\n\n- \n\n## Notes\n\n\n## Action Items\n\n- [ ] \n",
            "journal": "# {date}\n\n## Morning\n\n\n## Afternoon\n\n\n## Evening\n\n\n## Reflections\n\n",
            "project": "# {title}\n\n## Overview\n\n\n## Goals\n\n- \n\n## Tasks\n\n- [ ] \n\n## Notes\n\n",
            "research": "# {title}\n\n## Research Question\n\n\n## Sources\n\n- \n\n## Notes\n\n\n## Conclusions\n\n",
            "idea": "# {title}\n\n## The Idea\n\n\n## Why It Matters\n\n\n## Next Steps\n\n",
        }
    
    def _load_notes(self) -> None:
        """Load all notes from the notes directory."""
        for md_file in self.notes_dir.rglob("*.md"):
            try:
                note = self._load_note(md_file)
                if note:
                    self.notes[note.metadata.uuid] = note
                    self.index.add_note(note)
            except Exception as e:
                print(f"Warning: Could not load note {md_file}: {e}")
    
    def _load_note(self, filepath: Path) -> Optional[Note]:
        """Load a single note from file."""
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Parse frontmatter
        metadata, body = self._parse_frontmatter(content)
        
        if not metadata:
            # Create metadata from file
            stat = filepath.stat()
            metadata = NoteMetadata(
                title=filepath.stem,
                created=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            )
        
        return Note(
            metadata=metadata,
            content=body,
            path=str(filepath),
        )
    
    def _parse_frontmatter(self, content: str) -> Tuple[Optional[NoteMetadata], str]:
        """Parse YAML frontmatter from note content."""
        if not content.startswith('---\n'):
            return None, content
        
        end = content.find('\n---\n', 4)
        if end == -1:
            return None, content
        
        frontmatter = content[4:end]
        body = content[end + 5:]
        
        # Simple YAML parsing
        metadata_dict = {}
        for line in frontmatter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Parse lists
                if value.startswith('[') and value.endswith(']'):
                    value = [v.strip() for v in value[1:-1].split(',') if v.strip()]
                # Parse booleans
                elif value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                
                metadata_dict[key] = value
        
        metadata = NoteMetadata(
            title=metadata_dict.get('title', 'Untitled'),
            created=metadata_dict.get('created', datetime.now().isoformat()),
            modified=metadata_dict.get('modified', datetime.now().isoformat()),
            category=metadata_dict.get('category', 'general'),
            tags=metadata_dict.get('tags', []),
            pinned=metadata_dict.get('pinned', False),
            favorite=metadata_dict.get('favorite', False),
            archived=metadata_dict.get('archived', False),
            uuid=metadata_dict.get('uuid', ''),
        )
        
        return metadata, body
    
    def create_note(self, title: str, category: str = "general", 
                   tags: List[str] = None, template: str = None) -> Note:
        """Create a new note."""
        now = datetime.now().isoformat()
        
        metadata = NoteMetadata(
            title=title,
            created=now,
            modified=now,
            category=category,
            tags=tags or [],
            template=template or "default",
        )
        
        # Get template content
        template_content = self.templates.get(template or "default", "# {title}\n\n")
        content = template_content.format(
            title=title,
            date=now[:10],
            time=now[11:19],
        )
        
        # Determine file path
        category_dir = self.notes_dir / category
        filename = self._slugify(title) + ".md"
        filepath = category_dir / filename
        
        # Handle duplicate filenames
        counter = 1
        while filepath.exists():
            filepath = category_dir / f"{self._slugify(title)}-{counter}.md"
            counter += 1
        
        note = Note(
            metadata=metadata,
            content=content,
            path=str(filepath),
        )
        
        # Save and index
        self.save_note(note)
        self.notes[metadata.uuid] = note
        self.index.add_note(note)
        
        return note
    
    def save_note(self, note: Note) -> None:
        """Save a note to disk."""
        note.metadata.modified = datetime.now().isoformat()
        
        # Format content with frontmatter
        content = self._format_with_frontmatter(note)
        
        # Ensure directory exists
        Path(note.path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(note.path, 'w') as f:
            f.write(content)
    
    def _format_with_frontmatter(self, note: Note) -> str:
        """Format note content with YAML frontmatter."""
        frontmatter = f"""---
title: {note.metadata.title}
created: {note.metadata.created}
modified: {note.metadata.modified}
category: {note.metadata.category}
tags: {json.dumps(note.metadata.tags)}
pinned: {str(note.metadata.pinned).lower()}
favorite: {str(note.metadata.favorite).lower()}
archived: {str(note.metadata.archived).lower()}
uuid: {note.metadata.uuid}
---

"""
        return frontmatter + note.content
    
    def delete_note(self, note: Note) -> None:
        """Delete a note."""
        # Remove from index
        self.index.remove_note(note)
        
        # Remove from memory
        if note.metadata.uuid in self.notes:
            del self.notes[note.metadata.uuid]
        
        # Remove file
        if note.path and os.path.exists(note.path):
            os.remove(note.path)
        
        # Remove links involving this note
        self.links = [
            link for link in self.links
            if link.source_uuid != note.metadata.uuid
            and link.target_uuid != note.metadata.uuid
        ]
    
    def get_note(self, uuid: str) -> Optional[Note]:
        """Get a note by UUID."""
        return self.notes.get(uuid)
    
    def get_note_by_title(self, title: str) -> Optional[Note]:
        """Get a note by title."""
        for note in self.notes.values():
            if note.title.lower() == title.lower():
                return note
        return None
    
    def search(self, query: str, search_type: str = "all") -> List[Note]:
        """Search for notes."""
        uuids = self.index.search(query, search_type)
        return [self.notes[uuid] for uuid in uuids if uuid in self.notes]
    
    def get_by_tag(self, tag: str) -> List[Note]:
        """Get notes by tag."""
        uuids = self.index.search_by_tag(tag)
        return [self.notes[uuid] for uuid in uuids if uuid in self.notes]
    
    def get_by_category(self, category: str) -> List[Note]:
        """Get notes by category."""
        uuids = self.index.search_by_category(category)
        return [self.notes[uuid] for uuid in uuids if uuid in self.notes]
    
    def get_all_tags(self) -> List[Tuple[str, int]]:
        """Get all tags with counts."""
        counts = self.index.get_tag_counts()
        return sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    
    def get_recent(self, limit: int = 10) -> List[Note]:
        """Get recently modified notes."""
        sorted_notes = sorted(
            self.notes.values(),
            key=lambda n: n.metadata.modified,
            reverse=True
        )
        return sorted_notes[:limit]
    
    def get_pinned(self) -> List[Note]:
        """Get pinned notes."""
        return [n for n in self.notes.values() if n.metadata.pinned]
    
    def get_favorites(self) -> List[Note]:
        """Get favorite notes."""
        return [n for n in self.notes.values() if n.metadata.favorite]
    
    # Wiki-style linking
    def extract_links(self, note: Note) -> List[str]:
        """Extract wiki-style links from note content."""
        # Match [[link]] or [[link|text]]
        pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
        return re.findall(pattern, note.content)
    
    def create_link(self, source: Note, target: Note, link_type: str = "reference") -> NoteLink:
        """Create a link between notes."""
        link = NoteLink(
            source_uuid=source.metadata.uuid,
            target_uuid=target.metadata.uuid,
            link_type=link_type,
        )
        self.links.append(link)
        return link
    
    def get_linked_notes(self, note: Note) -> List[Note]:
        """Get all notes linked to/from a note."""
        uuid = note.metadata.uuid
        linked_uuids = set()
        
        for link in self.links:
            if link.source_uuid == uuid:
                linked_uuids.add(link.target_uuid)
            if link.target_uuid == uuid:
                linked_uuids.add(link.source_uuid)
        
        return [self.notes[u] for u in linked_uuids if u in self.notes]
    
    def get_backlinks(self, note: Note) -> List[Note]:
        """Get notes that link to this note."""
        uuid = note.metadata.uuid
        backlink_uuids = set()
        
        for link in self.links:
            if link.target_uuid == uuid:
                backlink_uuids.add(link.source_uuid)
        
        return [self.notes[u] for u in backlink_uuids if u in self.notes]
    
    def resolve_link(self, link_text: str) -> Optional[Note]:
        """Resolve a wiki link to a note."""
        # Try exact title match first
        note = self.get_note_by_title(link_text)
        if note:
            return note
        
        # Try partial match
        for n in self.notes.values():
            if link_text.lower() in n.title.lower():
                return n
        
        return None
    
    # Daily notes
    def get_or_create_daily_note(self, date: datetime = None) -> Note:
        """Get or create today's daily note."""
        date = date or datetime.now()
        date_str = date.strftime("%Y-%m-%d")
        title = f"Daily Note - {date_str}"
        
        # Check if exists
        for note in self.notes.values():
            if note.title == title:
                return note
        
        # Create new daily note
        return self.create_note(
            title=title,
            category="journal",
            template="journal",
        )
    
    # Templates
    def add_template(self, name: str, content: str) -> None:
        """Add a custom template."""
        self.templates[name] = content
    
    def get_template(self, name: str) -> Optional[str]:
        """Get a template by name."""
        return self.templates.get(name)
    
    def list_templates(self) -> List[str]:
        """List available templates."""
        return list(self.templates.keys())
    
    # Import/Export
    def export_note(self, note: Note, format: str = "md") -> str:
        """Export a note to a specific format."""
        if format == "md":
            return self._format_with_frontmatter(note)
        elif format == "html":
            from .markdown_processor import MarkdownRenderer
            renderer = MarkdownRenderer()
            return renderer.render(note.content)
        elif format == "json":
            return json.dumps({
                "metadata": asdict(note.metadata),
                "content": note.content,
            }, indent=2)
        return note.content
    
    def import_note(self, content: str, format: str = "md") -> Note:
        """Import a note from a specific format."""
        if format == "md":
            metadata, body = self._parse_frontmatter(content)
            if not metadata:
                metadata = NoteMetadata(
                    title="Imported Note",
                    created=datetime.now().isoformat(),
                    modified=datetime.now().isoformat(),
                )
            return self.create_note(
                title=metadata.title,
                category=metadata.category,
                tags=metadata.tags,
            )
        elif format == "json":
            data = json.loads(content)
            return self.create_note(
                title=data["metadata"]["title"],
                category=data["metadata"].get("category", "general"),
                tags=data["metadata"].get("tags", []),
            )
        
        return self.create_note(title="Imported Note")
    
    # Utility
    def _slugify(self, text: str) -> str:
        """Convert text to a URL-safe slug."""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        return text.strip('-')


__all__ = [
    'NoteCategory',
    'NoteMetadata',
    'Note',
    'NoteLink',
    'NoteIndex',
    'NoteManager',
]
