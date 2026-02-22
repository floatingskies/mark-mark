"""
Plugin system for MarkMark.
Provides extensibility through plugins with hooks, commands, and UI extensions.
"""

import os
import json
import importlib.util
from pathlib import Path
from typing import Optional, List, Dict, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


class HookType(Enum):
    """Types of hooks available for plugins."""
    # Editor events
    BEFORE_SAVE = "before_save"
    AFTER_SAVE = "after_save"
    BEFORE_OPEN = "before_open"
    AFTER_OPEN = "after_open"
    BEFORE_CLOSE = "before_close"
    AFTER_CLOSE = "after_close"
    
    # Text events
    BEFORE_INSERT = "before_insert"
    AFTER_INSERT = "after_insert"
    BEFORE_DELETE = "before_delete"
    AFTER_DELETE = "after_delete"
    TEXT_CHANGED = "text_changed"
    
    # Cursor events
    CURSOR_MOVED = "cursor_moved"
    SELECTION_CHANGED = "selection_changed"
    
    # Mode events
    MODE_CHANGED = "mode_changed"
    ZEN_MODE_TOGGLED = "zen_mode_toggled"
    
    # File events
    FILE_CREATED = "file_created"
    FILE_DELETED = "file_deleted"
    FILE_RENAMED = "file_renamed"
    
    # UI events
    MENU_POPULATED = "menu_populated"
    TOOLBAR_POPULATED = "toolbar_populated"
    STATUS_BAR_UPDATE = "status_bar_update"
    
    # Command events
    BEFORE_COMMAND = "before_command"
    AFTER_COMMAND = "after_command"
    
    # Plugin events
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    name: str
    version: str
    description: str
    author: str = ""
    homepage: str = ""
    license: str = "MIT"
    min_app_version: str = "1.0.0"
    dependencies: List[str] = field(default_factory=list)
    enabled: bool = True


class PluginInterface(ABC):
    """Interface that all plugins must implement."""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass
    
    @abstractmethod
    def activate(self, app: Any) -> None:
        """Called when plugin is activated."""
        pass
    
    @abstractmethod
    def deactivate(self, app: Any) -> None:
        """Called when plugin is deactivated."""
        pass


class Hook:
    """A hook that plugins can register callbacks to."""
    
    def __init__(self, hook_type: HookType):
        self.hook_type = hook_type
        self.callbacks: List[Callable] = []
        self.priorities: Dict[Callable, int] = {}
    
    def register(self, callback: Callable, priority: int = 0) -> None:
        """Register a callback with this hook."""
        self.callbacks.append(callback)
        self.priorities[callback] = priority
        self.callbacks.sort(key=lambda c: self.priorities[c], reverse=True)
    
    def unregister(self, callback: Callable) -> None:
        """Unregister a callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            del self.priorities[callback]
    
    def call(self, *args, **kwargs) -> Any:
        """Call all registered callbacks."""
        result = None
        for callback in self.callbacks:
            try:
                result = callback(*args, **kwargs)
                if result is not None and self.hook_type in (
                    HookType.BEFORE_SAVE, HookType.BEFORE_OPEN,
                    HookType.BEFORE_CLOSE, HookType.BEFORE_INSERT,
                    HookType.BEFORE_DELETE, HookType.BEFORE_COMMAND
                ):
                    # Allow callbacks to modify/stop the action
                    if result is False:
                        return False
            except Exception as e:
                print(f"Hook callback error: {e}")
        return result


class PluginCommand:
    """A command provided by a plugin."""
    
    def __init__(self, name: str, handler: Callable, description: str = "",
                 shortcut: str = "", category: str = "plugin"):
        self.name = name
        self.handler = handler
        self.description = description
        self.shortcut = shortcut
        self.category = category


class PluginManager:
    """
    Manages plugin loading, lifecycle, and hook registration.
    
    Features:
    - Dynamic plugin loading from directories
    - Hook system for event-based extensibility
    - Command registration
    - Dependency management
    - Plugin configuration
    """
    
    def __init__(self, plugin_dirs: List[str] = None, config=None):
        self.config = config
        self.plugin_dirs = plugin_dirs or []
        self.plugins: Dict[str, PluginInterface] = {}
        self.hooks: Dict[HookType, Hook] = {}
        self.commands: Dict[str, PluginCommand] = {}
        self.configs: Dict[str, dict] = {}
        
        # Initialize hooks
        for hook_type in HookType:
            self.hooks[hook_type] = Hook(hook_type)
        
        # Add default plugin directory
        default_dir = Path.home() / ".config" / "markmark" / "plugins"
        if str(default_dir) not in self.plugin_dirs:
            self.plugin_dirs.append(str(default_dir))
        
        # Ensure plugin directories exist
        for plugin_dir in self.plugin_dirs:
            Path(plugin_dir).mkdir(parents=True, exist_ok=True)
    
    def discover_plugins(self) -> List[PluginMetadata]:
        """Discover available plugins in plugin directories."""
        discovered = []
        
        for plugin_dir in self.plugin_dirs:
            plugin_path = Path(plugin_dir)
            if not plugin_path.exists():
                continue
            
            for item in plugin_path.iterdir():
                if item.is_dir():
                    # Check for plugin.json or plugin.py
                    plugin_json = item / "plugin.json"
                    plugin_py = item / "plugin.py"
                    
                    if plugin_json.exists():
                        try:
                            with open(plugin_json) as f:
                                data = json.load(f)
                            metadata = PluginMetadata(
                                name=data.get("name", item.name),
                                version=data.get("version", "0.0.0"),
                                description=data.get("description", ""),
                                author=data.get("author", ""),
                                homepage=data.get("homepage", ""),
                                license=data.get("license", "MIT"),
                                min_app_version=data.get("min_app_version", "1.0.0"),
                                dependencies=data.get("dependencies", []),
                                enabled=data.get("enabled", True),
                            )
                            discovered.append(metadata)
                        except Exception as e:
                            print(f"Error loading plugin metadata from {plugin_json}: {e}")
                    
                    elif plugin_py.exists():
                        # Single-file plugin
                        discovered.append(PluginMetadata(
                            name=item.name,
                            version="0.0.0",
                            description="",
                        ))
        
        return discovered
    
    def load_plugin(self, plugin_name: str, plugin_dir: str = None) -> bool:
        """Load a plugin by name."""
        if plugin_name in self.plugins:
            return True
        
        # Find plugin directory
        plugin_path = None
        if plugin_dir:
            plugin_path = Path(plugin_dir) / plugin_name
        else:
            for pd in self.plugin_dirs:
                potential = Path(pd) / plugin_name
                if potential.exists():
                    plugin_path = potential
                    break
        
        if not plugin_path or not plugin_path.exists():
            print(f"Plugin not found: {plugin_name}")
            return False
        
        try:
            # Load plugin module
            plugin_py = plugin_path / "plugin.py"
            if plugin_py.exists():
                spec = importlib.util.spec_from_file_location(
                    f"markmark_plugin_{plugin_name}",
                    plugin_py
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find plugin class
                plugin_class = None
                for name in dir(module):
                    obj = getattr(module, name)
                    if isinstance(obj, type) and issubclass(obj, PluginInterface) and obj is not PluginInterface:
                        plugin_class = obj
                        break
                
                if plugin_class:
                    plugin = plugin_class()
                    self.plugins[plugin_name] = plugin
                    
                    # Load plugin config
                    config_file = plugin_path / "config.json"
                    if config_file.exists():
                        with open(config_file) as f:
                            self.configs[plugin_name] = json.load(f)
                    
                    return True
            
        except Exception as e:
            print(f"Error loading plugin {plugin_name}: {e}")
            import traceback
            traceback.print_exc()
        
        return False
    
    def activate_plugin(self, plugin_name: str, app: Any) -> bool:
        """Activate a loaded plugin."""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return False
        
        try:
            plugin.activate(app)
            self.call_hook(HookType.PLUGIN_LOADED, plugin_name=plugin_name)
            return True
        except Exception as e:
            print(f"Error activating plugin {plugin_name}: {e}")
            return False
    
    def deactivate_plugin(self, plugin_name: str, app: Any) -> bool:
        """Deactivate a plugin."""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return False
        
        try:
            plugin.deactivate(app)
            self.call_hook(HookType.PLUGIN_UNLOADED, plugin_name=plugin_name)
            return True
        except Exception as e:
            print(f"Error deactivating plugin {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str, app: Any = None) -> bool:
        """Unload a plugin completely."""
        if plugin_name in self.plugins:
            if app:
                self.deactivate_plugin(plugin_name, app)
            del self.plugins[plugin_name]
        
        # Remove plugin commands
        self.commands = {
            k: v for k, v in self.commands.items()
            if not k.startswith(f"{plugin_name}.")
        }
        
        # Remove plugin config
        if plugin_name in self.configs:
            del self.configs[plugin_name]
        
        return True
    
    # Hook system
    def register_hook(self, hook_type: HookType, callback: Callable, priority: int = 0) -> None:
        """Register a callback for a hook."""
        self.hooks[hook_type].register(callback, priority)
    
    def unregister_hook(self, hook_type: HookType, callback: Callable) -> None:
        """Unregister a callback from a hook."""
        self.hooks[hook_type].unregister(callback)
    
    def call_hook(self, hook_type: HookType, *args, **kwargs) -> Any:
        """Call all callbacks registered for a hook."""
        return self.hooks[hook_type].call(*args, **kwargs)
    
    # Command system
    def register_command(self, command: PluginCommand) -> None:
        """Register a plugin command."""
        self.commands[command.name] = command
    
    def unregister_command(self, command_name: str) -> None:
        """Unregister a plugin command."""
        if command_name in self.commands:
            del self.commands[command_name]
    
    def execute_command(self, command_name: str, *args, **kwargs) -> Any:
        """Execute a registered command."""
        command = self.commands.get(command_name)
        if command:
            return command.handler(*args, **kwargs)
        return None
    
    def get_commands(self, category: str = None) -> List[PluginCommand]:
        """Get all registered commands, optionally filtered by category."""
        commands = list(self.commands.values())
        if category:
            commands = [c for c in commands if c.category == category]
        return commands
    
    # Plugin configuration
    def get_plugin_config(self, plugin_name: str) -> dict:
        """Get configuration for a plugin."""
        return self.configs.get(plugin_name, {})
    
    def set_plugin_config(self, plugin_name: str, config: dict) -> None:
        """Set configuration for a plugin."""
        self.configs[plugin_name] = config


# Built-in plugins

class SpellCheckPlugin(PluginInterface):
    """Built-in spell check plugin."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="spell_check",
            version="1.0.0",
            description="Real-time spell checking",
            author="MarkMark Team",
        )
    
    def activate(self, app: Any) -> None:
        # Register spell check hooks
        app.plugin_manager.register_hook(
            HookType.TEXT_CHANGED,
            self._check_spelling
        )
    
    def deactivate(self, app: Any) -> None:
        app.plugin_manager.unregister_hook(
            HookType.TEXT_CHANGED,
            self._check_spelling
        )
    
    def _check_spelling(self, text: str, **kwargs) -> None:
        # Placeholder for spell check logic
        pass


class AutoSavePlugin(PluginInterface):
    """Built-in auto-save plugin."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="auto_save",
            version="1.0.0",
            description="Automatic file saving",
            author="MarkMark Team",
        )
    
    def activate(self, app: Any) -> None:
        self.app = app
        # Register for text changes
        app.plugin_manager.register_hook(
            HookType.TEXT_CHANGED,
            self._schedule_save
        )
    
    def deactivate(self, app: Any) -> None:
        app.plugin_manager.unregister_hook(
            HookType.TEXT_CHANGED,
            self._schedule_save
        )
    
    def _schedule_save(self, **kwargs) -> None:
        # Schedule auto-save
        pass


class MarkdownLinterPlugin(PluginInterface):
    """Built-in markdown linting plugin."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="markdown_linter",
            version="1.0.0",
            description="Markdown linting and validation",
            author="MarkMark Team",
        )
    
    def activate(self, app: Any) -> None:
        app.plugin_manager.register_hook(
            HookType.AFTER_OPEN,
            self._lint_document
        )
        app.plugin_manager.register_hook(
            HookType.TEXT_CHANGED,
            self._lint_document
        )
    
    def deactivate(self, app: Any) -> None:
        app.plugin_manager.unregister_hook(
            HookType.AFTER_OPEN,
            self._lint_document
        )
        app.plugin_manager.unregister_hook(
            HookType.TEXT_CHANGED,
            self._lint_document
        )
    
    def _lint_document(self, content: str = "", **kwargs) -> List[dict]:
        """Lint markdown document and return issues."""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Check line length
            if len(line) > 120:
                issues.append({
                    "line": i + 1,
                    "message": "Line too long",
                    "severity": "warning"
                })
            
            # Check for trailing whitespace
            if line.rstrip() != line:
                issues.append({
                    "line": i + 1,
                    "message": "Trailing whitespace",
                    "severity": "info"
                })
            
            # Check heading style
            if line.startswith('#'):
                if not re.match(r'^#{1,6}\s', line):
                    issues.append({
                        "line": i + 1,
                        "message": "Heading requires space after #",
                        "severity": "warning"
                    })
        
        return issues


class WordCountPlugin(PluginInterface):
    """Built-in word count plugin."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="word_count",
            version="1.0.0",
            description="Real-time word, character, and line counting",
            author="MarkMark Team",
        )
    
    def activate(self, app: Any) -> None:
        self.app = app
        app.plugin_manager.register_hook(
            HookType.TEXT_CHANGED,
            self._update_counts
        )
        app.plugin_manager.register_hook(
            HookType.SELECTION_CHANGED,
            self._update_selection_counts
        )
    
    def deactivate(self, app: Any) -> None:
        app.plugin_manager.unregister_hook(
            HookType.TEXT_CHANGED,
            self._update_counts
        )
        app.plugin_manager.unregister_hook(
            HookType.SELECTION_CHANGED,
            self._update_selection_counts
        )
    
    def _update_counts(self, content: str = "", **kwargs) -> dict:
        """Update word count statistics."""
        words = len(content.split())
        chars = len(content)
        chars_no_space = len(content.replace(' ', '').replace('\n', '').replace('\t', ''))
        lines = len(content.split('\n'))
        
        return {
            "words": words,
            "characters": chars,
            "characters_no_spaces": chars_no_space,
            "lines": lines,
        }
    
    def _update_selection_counts(self, selection: str = "", **kwargs) -> dict:
        """Update selection word count."""
        if not selection:
            return {}
        
        return {
            "selected_words": len(selection.split()),
            "selected_characters": len(selection),
        }


# Export classes
__all__ = [
    'HookType',
    'PluginMetadata',
    'PluginInterface',
    'Hook',
    'PluginCommand',
    'PluginManager',
    'SpellCheckPlugin',
    'AutoSavePlugin',
    'MarkdownLinterPlugin',
    'WordCountPlugin',
]
