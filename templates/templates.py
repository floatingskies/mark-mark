"""
Templates system for MarkMark.
Provides document templates for various use cases.
"""

import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TemplateVariable:
    """A variable in a template."""
    name: str
    default: str = ""
    description: str = ""
    required: bool = False
    type: str = "text"  # text, number, date, select, multiselect
    options: List[str] = field(default_factory=list)


@dataclass
class Template:
    """A document template."""
    name: str
    content: str
    description: str = ""
    category: str = "general"
    variables: List[TemplateVariable] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def render(self, values: Dict[str, str] = None) -> str:
        """Render template with variable values."""
        values = values or {}
        result = self.content
        
        # Replace variables
        for var in self.variables:
            value = values.get(var.name, var.default)
            result = result.replace(f"{{{{{var.name}}}}}", value)
        
        # Handle built-in variables
        now = datetime.now()
        builtins = {
            "YEAR": str(now.year),
            "MONTH": f"{now.month:02d}",
            "DAY": f"{now.day:02d}",
            "DATE": now.strftime("%Y-%m-%d"),
            "TIME": now.strftime("%H:%M:%S"),
            "DATETIME": now.isoformat(),
            "WEEKDAY": now.strftime("%A"),
            "MONTH_NAME": now.strftime("%B"),
        }
        
        for name, value in builtins.items():
            result = result.replace(f"{{{{{name}}}}}", value)
        
        return result


class TemplateManager:
    """
    Manages document templates.
    
    Features:
    - Built-in templates
    - Custom template support
    - Variable interpolation
    - Template categories
    - Import/Export
    """
    
    def __init__(self, template_dirs: List[str] = None):
        self.template_dirs = template_dirs or []
        self.templates: Dict[str, Template] = {}
        self.categories: Dict[str, List[str]] = {}
        
        # Add default template directory
        default_dir = Path.home() / ".config" / "markmark" / "templates"
        if str(default_dir) not in self.template_dirs:
            self.template_dirs.append(str(default_dir))
        
        # Initialize default templates
        self._init_default_templates()
        
        # Load templates from directories
        self._load_templates()
    
    def _init_default_templates(self) -> None:
        """Initialize default document templates."""
        
        # Empty document
        self.add_template(Template(
            name="Empty Document",
            content="",
            description="Blank document",
            category="basic",
        ))
        
        # Basic Markdown
        self.add_template(Template(
            name="Basic Markdown",
            content="""# {{TITLE}}

{{CONTENT}}
""",
            description="Basic markdown document",
            category="basic",
            variables=[
                TemplateVariable(name="TITLE", default="Untitled", description="Document title"),
                TemplateVariable(name="CONTENT", default="", description="Document content"),
            ]
        ))
        
        # Blog Post
        self.add_template(Template(
            name="Blog Post",
            content="""---
title: "{{TITLE}}"
author: "{{AUTHOR}}"
date: "{{DATE}}"
tags: [{{TAGS}}]
category: {{CATEGORY}}
---

# {{TITLE}}

## Introduction

{{INTRODUCTION}}

## Main Content

{{CONTENT}}

## Conclusion

{{CONCLUSION}}

---

*Published on {{DATE}} by {{AUTHOR}}*
""",
            description="Blog post with frontmatter",
            category="blog",
            variables=[
                TemplateVariable(name="TITLE", default="My Blog Post", description="Post title"),
                TemplateVariable(name="AUTHOR", default="Author Name", description="Author name"),
                TemplateVariable(name="TAGS", default="markdown, writing", description="Post tags"),
                TemplateVariable(name="CATEGORY", default="General", description="Post category"),
                TemplateVariable(name="INTRODUCTION", default="", description="Introduction paragraph"),
                TemplateVariable(name="CONTENT", default="", description="Main content"),
                TemplateVariable(name="CONCLUSION", default="", description="Conclusion paragraph"),
            ]
        ))
        
        # README
        self.add_template(Template(
            name="README",
            content="""# {{PROJECT_NAME}}

{{DESCRIPTION}}

## Features

{{FEATURES}}

## Installation

```bash
{{INSTALLATION}}
```

## Usage

```bash
{{USAGE}}
```

## Documentation

{{DOCUMENTATION}}

## Contributing

{{CONTRIBUTING}}

## License

{{LICENSE}}
""",
            description="Project README",
            category="project",
            variables=[
                TemplateVariable(name="PROJECT_NAME", default="My Project", description="Project name"),
                TemplateVariable(name="DESCRIPTION", default="A brief description", description="Project description"),
                TemplateVariable(name="FEATURES", default="- Feature 1\n- Feature 2", description="Project features"),
                TemplateVariable(name="INSTALLATION", default="pip install myproject", description="Installation command"),
                TemplateVariable(name="USAGE", default="myproject --help", description="Usage example"),
                TemplateVariable(name="DOCUMENTATION", default="See [docs](docs/) for more information.", description="Documentation link"),
                TemplateVariable(name="CONTRIBUTING", default="Contributions are welcome!", description="Contributing info"),
                TemplateVariable(name="LICENSE", default="MIT", description="License"),
            ]
        ))
        
        # Technical Documentation
        self.add_template(Template(
            name="Technical Documentation",
            content="""# {{TITLE}}

**Version:** {{VERSION}}  
**Author:** {{AUTHOR}}  
**Last Updated:** {{DATE}}

## Overview

{{OVERVIEW}}

## Architecture

{{ARCHITECTURE}}

## API Reference

{{API_REFERENCE}}

## Examples

{{EXAMPLES}}

## Troubleshooting

{{TROUBLESHOOTING}}

## Changelog

### Version {{VERSION}}
- Initial release
""",
            description="Technical documentation",
            category="documentation",
            variables=[
                TemplateVariable(name="TITLE", default="API Documentation", description="Document title"),
                TemplateVariable(name="VERSION", default="1.0.0", description="Version number"),
                TemplateVariable(name="AUTHOR", default="Author", description="Author name"),
                TemplateVariable(name="OVERVIEW", default="", description="Overview section"),
                TemplateVariable(name="ARCHITECTURE", default="", description="Architecture description"),
                TemplateVariable(name="API_REFERENCE", default="", description="API documentation"),
                TemplateVariable(name="EXAMPLES", default="", description="Code examples"),
                TemplateVariable(name="TROUBLESHOOTING", default="", description="Troubleshooting guide"),
            ]
        ))
        
        # Meeting Notes
        self.add_template(Template(
            name="Meeting Notes",
            content="""# Meeting Notes

**Date:** {{DATE}}  
**Time:** {{TIME}}  
**Location:** {{LOCATION}}

## Attendees

{{ATTENDEES}}

## Agenda

{{AGENDA}}

## Discussion

{{DISCUSSION}}

## Action Items

| Task | Owner | Due Date |
|------|-------|----------|
{{ACTION_ITEMS}}

## Next Meeting

**Date:** {{NEXT_DATE}}  
**Time:** {{NEXT_TIME}}

## Notes

{{NOTES}}
""",
            description="Meeting notes template",
            category="business",
            variables=[
                TemplateVariable(name="LOCATION", default="Conference Room", description="Meeting location"),
                TemplateVariable(name="ATTENDEES", default="- Attendee 1\n- Attendee 2", description="Attendee list"),
                TemplateVariable(name="AGENDA", default="1. Topic 1\n2. Topic 2", description="Meeting agenda"),
                TemplateVariable(name="DISCUSSION", default="", description="Discussion notes"),
                TemplateVariable(name="ACTION_ITEMS", default="| Task | Owner | Due Date |", description="Action items table"),
                TemplateVariable(name="NEXT_DATE", default="TBD", description="Next meeting date"),
                TemplateVariable(name="NEXT_TIME", default="TBD", description="Next meeting time"),
                TemplateVariable(name="NOTES", default="", description="Additional notes"),
            ]
        ))
        
        # Journal Entry
        self.add_template(Template(
            name="Journal Entry",
            content="""# {{DATE}} - {{TITLE}}

## Morning

{{MORNING}}

## Afternoon

{{AFTERNOON}}

## Evening

{{EVENING}}

## Reflections

{{REFLECTIONS}}

## Tomorrow's Goals

{{GOALS}}

---

*Gratitude: {{GRATITUDE}}*
""",
            description="Daily journal entry",
            category="journal",
            variables=[
                TemplateVariable(name="TITLE", default="Daily Reflections", description="Entry title"),
                TemplateVariable(name="MORNING", default="", description="Morning activities"),
                TemplateVariable(name="AFTERNOON", default="", description="Afternoon activities"),
                TemplateVariable(name="EVENING", default="", description="Evening activities"),
                TemplateVariable(name="REFLECTIONS", default="", description="Daily reflections"),
                TemplateVariable(name="GOALS", default="- Goal 1\n- Goal 2", description="Tomorrow's goals"),
                TemplateVariable(name="GRATITUDE", default="", description="Something to be grateful for"),
            ]
        ))
        
        # Tutorial
        self.add_template(Template(
            name="Tutorial",
            content="""# {{TITLE}}

> **Difficulty:** {{DIFFICULTY}}  
> **Time Required:** {{TIME_REQUIRED}}  
> **Prerequisites:** {{PREREQUISITES}}

## Introduction

{{INTRODUCTION}}

## Prerequisites

{{PREREQUISITES_DETAIL}}

## Step 1: {{STEP1_TITLE}}

{{STEP1_CONTENT}}

## Step 2: {{STEP2_TITLE}}

{{STEP2_CONTENT}}

## Step 3: {{STEP3_TITLE}}

{{STEP3_CONTENT}}

## Conclusion

{{CONCLUSION}}

## Next Steps

{{NEXT_STEPS}}

---

*Found an error? [Report it here]({{ISSUE_LINK}})*
""",
            description="Tutorial template",
            category="documentation",
            variables=[
                TemplateVariable(name="TITLE", default="How to...", description="Tutorial title"),
                TemplateVariable(name="DIFFICULTY", default="Beginner", description="Difficulty level"),
                TemplateVariable(name="TIME_REQUIRED", default="30 minutes", description="Time required"),
                TemplateVariable(name="PREREQUISITES", default="None", description="Prerequisites"),
                TemplateVariable(name="INTRODUCTION", default="", description="Introduction"),
                TemplateVariable(name="PREREQUISITES_DETAIL", default="", description="Prerequisites details"),
                TemplateVariable(name="STEP1_TITLE", default="Getting Started", description="Step 1 title"),
                TemplateVariable(name="STEP1_CONTENT", default="", description="Step 1 content"),
                TemplateVariable(name="STEP2_TITLE", default="Main Task", description="Step 2 title"),
                TemplateVariable(name="STEP2_CONTENT", default="", description="Step 2 content"),
                TemplateVariable(name="STEP3_TITLE", default="Finishing Up", description="Step 3 title"),
                TemplateVariable(name="STEP3_CONTENT", default="", description="Step 3 content"),
                TemplateVariable(name="CONCLUSION", default="", description="Conclusion"),
                TemplateVariable(name="NEXT_STEPS", default="", description="Next steps"),
                TemplateVariable(name="ISSUE_LINK", default="#", description="Issue link"),
            ]
        ))
        
        # Project Proposal
        self.add_template(Template(
            name="Project Proposal",
            content="""# {{PROJECT_NAME}}

## Executive Summary

{{EXECUTIVE_SUMMARY}}

## Problem Statement

{{PROBLEM_STATEMENT}}

## Proposed Solution

{{PROPOSED_SOLUTION}}

## Goals and Objectives

{{GOALS}}

## Scope

{{SCOPE}}

## Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
{{TIMELINE}}

## Budget

{{BUDGET}}

## Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
{{RISKS}}

## Success Criteria

{{SUCCESS_CRITERIA}}

## Team

{{TEAM}}

## Approval

- [ ] Approved by: ________________
- [ ] Date: ________________
""",
            description="Project proposal template",
            category="business",
            variables=[
                TemplateVariable(name="PROJECT_NAME", default="Project Name", description="Project name"),
                TemplateVariable(name="EXECUTIVE_SUMMARY", default="", description="Executive summary"),
                TemplateVariable(name="PROBLEM_STATEMENT", default="", description="Problem statement"),
                TemplateVariable(name="PROPOSED_SOLUTION", default="", description="Proposed solution"),
                TemplateVariable(name="GOALS", default="- Goal 1\n- Goal 2", description="Goals and objectives"),
                TemplateVariable(name="SCOPE", default="", description="Project scope"),
                TemplateVariable(name="TIMELINE", default="| Phase 1 | 2 weeks | Planning |", description="Timeline table"),
                TemplateVariable(name="BUDGET", default="", description="Budget information"),
                TemplateVariable(name="RISKS", default="| Risk 1 | Medium | High | Mitigation |", description="Risks table"),
                TemplateVariable(name="SUCCESS_CRITERIA", default="- Criterion 1\n- Criterion 2", description="Success criteria"),
                TemplateVariable(name="TEAM", default="", description="Team members"),
            ]
        ))
        
        # Release Notes
        self.add_template(Template(
            name="Release Notes",
            content="""# {{PROJECT_NAME}} v{{VERSION}}

**Release Date:** {{DATE}}

## Highlights

{{HIGHLIGHTS}}

## New Features

{{NEW_FEATURES}}

## Improvements

{{IMPROVEMENTS}}

## Bug Fixes

{{BUG_FIXES}}

## Breaking Changes

{{BREAKING_CHANGES}}

## Known Issues

{{KNOWN_ISSUES}}

## Upgrade Guide

{{UPGRADE_GUIDE}}

## Contributors

{{CONTRIBUTORS}}

---

[Download v{{VERSION}}]({{DOWNLOAD_LINK}})
""",
            description="Release notes template",
            category="project",
            variables=[
                TemplateVariable(name="PROJECT_NAME", default="Project", description="Project name"),
                TemplateVariable(name="VERSION", default="1.0.0", description="Version number"),
                TemplateVariable(name="HIGHLIGHTS", default="", description="Release highlights"),
                TemplateVariable(name="NEW_FEATURES", default="- Feature 1\n- Feature 2", description="New features"),
                TemplateVariable(name="IMPROVEMENTS", default="- Improvement 1", description="Improvements"),
                TemplateVariable(name="BUG_FIXES", default="- Fix 1", description="Bug fixes"),
                TemplateVariable(name="BREAKING_CHANGES", default="None", description="Breaking changes"),
                TemplateVariable(name="KNOWN_ISSUES", default="None", description="Known issues"),
                TemplateVariable(name="UPGRADE_GUIDE", default="", description="Upgrade instructions"),
                TemplateVariable(name="CONTRIBUTORS", default="", description="Contributors list"),
                TemplateVariable(name="DOWNLOAD_LINK", default="#", description="Download link"),
            ]
        ))
        
        # Book Chapter
        self.add_template(Template(
            name="Book Chapter",
            content="""# Chapter {{CHAPTER_NUMBER}}: {{CHAPTER_TITLE}}

## Introduction

{{INTRODUCTION}}

## Section 1: {{SECTION1_TITLE}}

{{SECTION1_CONTENT}}

## Section 2: {{SECTION2_TITLE}}

{{SECTION2_CONTENT}}

## Section 3: {{SECTION3_TITLE}}

{{SECTION3_CONTENT}}

## Summary

{{SUMMARY}}

## Key Takeaways

{{KEY_TAKEAWAYS}}

## Discussion Questions

{{DISCUSSION_QUESTIONS}}

---

*Chapter {{CHAPTER_NUMBER}} of {{BOOK_TITLE}}*
""",
            description="Book chapter template",
            category="writing",
            variables=[
                TemplateVariable(name="BOOK_TITLE", default="Book Title", description="Book title"),
                TemplateVariable(name="CHAPTER_NUMBER", default="1", description="Chapter number"),
                TemplateVariable(name="CHAPTER_TITLE", default="Chapter Title", description="Chapter title"),
                TemplateVariable(name="INTRODUCTION", default="", description="Chapter introduction"),
                TemplateVariable(name="SECTION1_TITLE", default="Section 1", description="Section 1 title"),
                TemplateVariable(name="SECTION1_CONTENT", default="", description="Section 1 content"),
                TemplateVariable(name="SECTION2_TITLE", default="Section 2", description="Section 2 title"),
                TemplateVariable(name="SECTION2_CONTENT", default="", description="Section 2 content"),
                TemplateVariable(name="SECTION3_TITLE", default="Section 3", description="Section 3 title"),
                TemplateVariable(name="SECTION3_CONTENT", default="", description="Section 3 content"),
                TemplateVariable(name="SUMMARY", default="", description="Chapter summary"),
                TemplateVariable(name="KEY_TAKEAWAYS", default="- Takeaway 1\n- Takeaway 2", description="Key takeaways"),
                TemplateVariable(name="DISCUSSION_QUESTIONS", default="1. Question 1\n2. Question 2", description="Discussion questions"),
            ]
        ))
        
        # Letter
        self.add_template(Template(
            name="Letter",
            content="""{{SENDER_NAME}}
{{SENDER_ADDRESS}}
{{SENDER_CITY}}, {{SENDER_STATE}} {{SENDER_ZIP}}
{{SENDER_EMAIL}}

{{DATE}}

{{RECIPIENT_NAME}}
{{RECIPIENT_ADDRESS}}
{{RECIPIENT_CITY}}, {{RECIPIENT_STATE}} {{RECIPIENT_ZIP}}

Dear {{RECIPIENT_NAME}},

{{BODY}}

Sincerely,

{{SIGNATURE}}

{{SENDER_NAME}}
""",
            description="Formal letter template",
            category="correspondence",
            variables=[
                TemplateVariable(name="SENDER_NAME", default="Your Name", description="Your name"),
                TemplateVariable(name="SENDER_ADDRESS", default="123 Your Street", description="Your address"),
                TemplateVariable(name="SENDER_CITY", default="City", description="Your city"),
                TemplateVariable(name="SENDER_STATE", default="State", description="Your state"),
                TemplateVariable(name="SENDER_ZIP", default="12345", description="Your ZIP code"),
                TemplateVariable(name="SENDER_EMAIL", default="email@example.com", description="Your email"),
                TemplateVariable(name="RECIPIENT_NAME", default="Recipient Name", description="Recipient name"),
                TemplateVariable(name="RECIPIENT_ADDRESS", default="456 Their Street", description="Recipient address"),
                TemplateVariable(name="RECIPIENT_CITY", default="City", description="Recipient city"),
                TemplateVariable(name="RECIPIENT_STATE", default="State", description="Recipient state"),
                TemplateVariable(name="RECIPIENT_ZIP", default="67890", description="Recipient ZIP code"),
                TemplateVariable(name="BODY", default="", description="Letter body"),
                TemplateVariable(name="SIGNATURE", default="", description="Signature"),
            ]
        ))
    
    def _load_templates(self) -> None:
        """Load templates from template directories."""
        for template_dir in self.template_dirs:
            template_path = Path(template_dir)
            if not template_path.exists():
                continue
            
            for file in template_path.rglob("*.json"):
                try:
                    with open(file) as f:
                        data = json.load(f)
                    self._load_template_dict(data)
                except Exception as e:
                    print(f"Error loading template from {file}: {e}")
    
    def _load_template_dict(self, data: dict) -> None:
        """Load a template from dictionary."""
        variables = [
            TemplateVariable(
                name=v.get("name", ""),
                default=v.get("default", ""),
                description=v.get("description", ""),
                required=v.get("required", False),
                type=v.get("type", "text"),
                options=v.get("options", []),
            )
            for v in data.get("variables", [])
        ]
        
        template = Template(
            name=data.get("name", "Unnamed"),
            content=data.get("content", ""),
            description=data.get("description", ""),
            category=data.get("category", "general"),
            variables=variables,
            metadata=data.get("metadata", {}),
        )
        self.add_template(template)
    
    def add_template(self, template: Template) -> None:
        """Add a template."""
        self.templates[template.name] = template
        
        if template.category not in self.categories:
            self.categories[template.category] = []
        self.categories[template.category].append(template.name)
    
    def remove_template(self, name: str) -> bool:
        """Remove a template by name."""
        if name in self.templates:
            template = self.templates[name]
            if template.category in self.categories:
                self.categories[template.category] = [
                    t for t in self.categories[template.category] if t != name
                ]
            del self.templates[name]
            return True
        return False
    
    def get_template(self, name: str) -> Optional[Template]:
        """Get a template by name."""
        return self.templates.get(name)
    
    def render_template(self, name: str, values: Dict[str, str] = None) -> Optional[str]:
        """Render a template by name."""
        template = self.get_template(name)
        if template:
            return template.render(values)
        return None
    
    def get_templates_by_category(self, category: str) -> List[Template]:
        """Get all templates in a category."""
        names = self.categories.get(category, [])
        return [self.templates[n] for n in names if n in self.templates]
    
    def get_all_categories(self) -> List[str]:
        """Get all template categories."""
        return list(self.categories.keys())
    
    def search_templates(self, query: str) -> List[Template]:
        """Search templates by name or description."""
        query_lower = query.lower()
        results = []
        
        for template in self.templates.values():
            if (query_lower in template.name.lower() or
                query_lower in template.description.lower()):
                results.append(template)
        
        return results
    
    def save_template(self, template: Template, filepath: str = None) -> bool:
        """Save a template to file."""
        filepath = filepath or str(
            Path(self.template_dirs[0]) / f"{template.name}.json"
        )
        
        try:
            data = {
                "name": template.name,
                "content": template.content,
                "description": template.description,
                "category": template.category,
                "variables": [
                    {
                        "name": v.name,
                        "default": v.default,
                        "description": v.description,
                        "required": v.required,
                        "type": v.type,
                        "options": v.options,
                    }
                    for v in template.variables
                ],
                "metadata": template.metadata,
            }
            
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving template: {e}")
            return False


__all__ = ['Template', 'TemplateVariable', 'TemplateManager']
