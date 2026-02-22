"""
Zen mode implementation for MarkMark.
Provides a distraction-free writing environment.
"""

from typing import Optional, Callable, List
from dataclasses import dataclass
from enum import Enum


class ZenFeature(Enum):
    """Features that can be toggled in Zen mode."""
    MENU_BAR = "menu_bar"
    STATUS_BAR = "status_bar"
    SIDEBAR = "sidebar"
    LINE_NUMBERS = "line_numbers"
    MINIMAP = "minimap"
    SCROLLBAR = "scrollbar"
    TOOLBAR = "toolbar"
    RULER = "ruler"
    INDENT_GUIDES = "indent_guides"


@dataclass
class TypographySettings:
    """Typography settings for Zen mode."""
    font_family: str = "Georgia"
    font_size: int = 18
    line_height: float = 1.8
    paragraph_spacing: float = 1.5
    letter_spacing: float = 0.0
    max_width: int = 720
    text_align: str = "left"  # left, justify, center


@dataclass
class AmbientSettings:
    """Ambient environment settings."""
    background_color: str = "#1a1a2e"
    text_color: str = "#e0e0e0"
    secondary_color: str = "#888888"
    opacity: float = 1.0
    blur_radius: int = 0
    ambient_sound: str = ""  # Path to ambient sound file
    ambient_volume: float = 0.3


class ZenMode:
    """
    Zen mode for distraction-free writing.
    
    Features:
    - Minimalist interface hiding all UI chrome
    - Centered text with configurable max width
    - Focus on current paragraph/line
    - Ambient typography
    - Soft color themes
    - Typewriter scrolling
    - Optional ambient sounds
    """
    
    def __init__(self, config=None):
        self.config = config
        
        # State
        self.active: bool = False
        self.pre_zen_state: dict = {}
        
        # Settings
        self.typography = TypographySettings()
        self.ambient = AmbientSettings()
        
        # Features to hide in Zen mode
        self.hidden_features: List[ZenFeature] = [
            ZenFeature.MENU_BAR,
            ZenFeature.STATUS_BAR,
            ZenFeature.SIDEBAR,
            ZenFeature.MINIMAP,
            ZenFeature.SCROLLBAR,
            ZenFeature.TOOLBAR,
            ZenFeature.INDENT_GUIDES,
        ]
        
        # Focus settings
        self.focus_current_paragraph: bool = True
        self.focus_current_sentence: bool = False
        self.focus_opacity: float = 0.3  # Opacity for non-focused content
        
        # Typewriter mode
        self.typewriter_mode: bool = True
        self.typewriter_position: float = 0.35  # Cursor position (0-1)
        
        # Callbacks
        self.on_toggle: Optional[Callable[[bool], None]] = None
        self.on_settings_change: Optional[Callable[[], None]] = None
        
        # Sound playback
        self._sound_playing: bool = False
        self._sound_loop: bool = True
    
    def activate(self) -> None:
        """Activate Zen mode."""
        if self.active:
            return
        
        # Save current state
        self._save_state()
        
        # Activate
        self.active = True
        
        # Start ambient sound if configured
        if self.ambient.ambient_sound:
            self._start_ambient_sound()
        
        if self.on_toggle:
            self.on_toggle(True)
    
    def deactivate(self) -> None:
        """Deactivate Zen mode."""
        if not self.active:
            return
        
        # Stop ambient sound
        self._stop_ambient_sound()
        
        # Restore previous state
        self._restore_state()
        
        # Deactivate
        self.active = False
        
        if self.on_toggle:
            self.on_toggle(False)
    
    def toggle(self) -> bool:
        """Toggle Zen mode. Returns new state."""
        if self.active:
            self.deactivate()
        else:
            self.activate()
        return self.active
    
    def _save_state(self) -> None:
        """Save current UI state before entering Zen mode."""
        self.pre_zen_state = {
            'hidden_features': self.hidden_features.copy(),
            'typography': TypographySettings(
                font_family=self.typography.font_family,
                font_size=self.typography.font_size,
                line_height=self.typography.line_height,
                paragraph_spacing=self.typography.paragraph_spacing,
                letter_spacing=self.typography.letter_spacing,
                max_width=self.typography.max_width,
                text_align=self.typography.text_align,
            ),
            'focus_current_paragraph': self.focus_current_paragraph,
            'typewriter_mode': self.typewriter_mode,
        }
    
    def _restore_state(self) -> None:
        """Restore previous UI state when exiting Zen mode."""
        # The actual restoration should be done by the editor
        # This just clears the saved state
        self.pre_zen_state.clear()
    
    def is_feature_hidden(self, feature: ZenFeature) -> bool:
        """Check if a feature should be hidden."""
        return self.active and feature in self.hidden_features
    
    def hide_feature(self, feature: ZenFeature) -> None:
        """Add a feature to the hidden list."""
        if feature not in self.hidden_features:
            self.hidden_features.append(feature)
            if self.active and self.on_settings_change:
                self.on_settings_change()
    
    def show_feature(self, feature: ZenFeature) -> None:
        """Remove a feature from the hidden list."""
        if feature in self.hidden_features:
            self.hidden_features.remove(feature)
            if self.active and self.on_settings_change:
                self.on_settings_change()
    
    def toggle_feature(self, feature: ZenFeature) -> bool:
        """Toggle a feature's visibility. Returns new hidden state."""
        if feature in self.hidden_features:
            self.show_feature(feature)
            return False
        else:
            self.hide_feature(feature)
            return True
    
    # Typography settings
    def set_font_family(self, family: str) -> None:
        """Set the font family."""
        self.typography.font_family = family
        if self.active and self.on_settings_change:
            self.on_settings_change()
    
    def set_font_size(self, size: int) -> None:
        """Set the font size."""
        self.typography.font_size = max(8, min(72, size))
        if self.active and self.on_settings_change:
            self.on_settings_change()
    
    def set_line_height(self, height: float) -> None:
        """Set the line height."""
        self.typography.line_height = max(1.0, min(3.0, height))
        if self.active and self.on_settings_change:
            self.on_settings_change()
    
    def set_max_width(self, width: int) -> None:
        """Set the maximum text width."""
        self.typography.max_width = max(400, min(1200, width))
        if self.active and self.on_settings_change:
            self.on_settings_change()
    
    def set_text_align(self, align: str) -> None:
        """Set text alignment."""
        if align in ('left', 'justify', 'center'):
            self.typography.text_align = align
            if self.active and self.on_settings_change:
                self.on_settings_change()
    
    # Ambient settings
    def set_background_color(self, color: str) -> None:
        """Set background color."""
        self.ambient.background_color = color
        if self.active and self.on_settings_change:
            self.on_settings_change()
    
    def set_text_color(self, color: str) -> None:
        """Set text color."""
        self.ambient.text_color = color
        if self.active and self.on_settings_change:
            self.on_settings_change()
    
    def set_opacity(self, opacity: float) -> None:
        """Set background opacity."""
        self.ambient.opacity = max(0.5, min(1.0, opacity))
        if self.active and self.on_settings_change:
            self.on_settings_change()
    
    def set_ambient_sound(self, path: str) -> None:
        """Set ambient sound file."""
        self.ambient.ambient_sound = path
        if self.active:
            self._stop_ambient_sound()
            self._start_ambient_sound()
    
    def _start_ambient_sound(self) -> None:
        """Start playing ambient sound."""
        # Implementation would use a sound library
        self._sound_playing = True
    
    def _stop_ambient_sound(self) -> None:
        """Stop playing ambient sound."""
        # Implementation would use a sound library
        self._sound_playing = False
    
    def toggle_ambient_sound(self) -> bool:
        """Toggle ambient sound. Returns new playing state."""
        if self._sound_playing:
            self._stop_ambient_sound()
        else:
            self._start_ambient_sound()
        return self._sound_playing
    
    # Focus settings
    def set_focus_paragraph(self, enabled: bool) -> None:
        """Enable/disable paragraph focus."""
        self.focus_current_paragraph = enabled
        if self.active and self.on_settings_change:
            self.on_settings_change()
    
    def set_focus_sentence(self, enabled: bool) -> None:
        """Enable/disable sentence focus."""
        self.focus_current_sentence = enabled
        if self.active and self.on_settings_change:
            self.on_settings_change()
    
    def set_focus_opacity(self, opacity: float) -> None:
        """Set opacity for non-focused content."""
        self.focus_opacity = max(0.1, min(1.0, opacity))
        if self.active and self.on_settings_change:
            self.on_settings_change()
    
    # Typewriter mode
    def set_typewriter_mode(self, enabled: bool) -> None:
        """Enable/disable typewriter scrolling."""
        self.typewriter_mode = enabled
        if self.active and self.on_settings_change:
            self.on_settings_change()
    
    def set_typewriter_position(self, position: float) -> None:
        """Set cursor position on screen (0=top, 1=bottom)."""
        self.typewriter_position = max(0.1, min(0.9, position))
        if self.active and self.on_settings_change:
            self.on_settings_change()
    
    # Presets
    def apply_preset(self, preset_name: str) -> None:
        """Apply a Zen mode preset."""
        presets = {
            'minimal': {
                'hidden_features': [
                    ZenFeature.MENU_BAR, ZenFeature.STATUS_BAR,
                    ZenFeature.SIDEBAR, ZenFeature.MINIMAP,
                    ZenFeature.SCROLLBAR, ZenFeature.LINE_NUMBERS
                ],
                'typography': TypographySettings(
                    font_family="Georgia", font_size=18,
                    line_height=1.8, max_width=720
                ),
                'focus_current_paragraph': True,
                'typewriter_mode': True,
            },
            'dark_room': {
                'hidden_features': [
                    ZenFeature.MENU_BAR, ZenFeature.STATUS_BAR,
                    ZenFeature.SIDEBAR, ZenFeature.MINIMAP,
                    ZenFeature.SCROLLBAR, ZenFeature.LINE_NUMBERS,
                    ZenFeature.RULER, ZenFeature.INDENT_GUIDES
                ],
                'typography': TypographySettings(
                    font_family="Courier New", font_size=16,
                    line_height=2.0, max_width=600
                ),
                'ambient': AmbientSettings(
                    background_color="#000000",
                    text_color="#00ff00",
                    opacity=1.0
                ),
                'focus_current_paragraph': False,
                'typewriter_mode': True,
            },
            'typewriter': {
                'hidden_features': [
                    ZenFeature.MENU_BAR, ZenFeature.STATUS_BAR,
                    ZenFeature.SIDEBAR, ZenFeature.MINIMAP,
                    ZenFeature.LINE_NUMBERS
                ],
                'typography': TypographySettings(
                    font_family="American Typewriter", font_size=16,
                    line_height=1.6, max_width=680
                ),
                'focus_current_paragraph': False,
                'typewriter_mode': True,
                'typewriter_position': 0.4,
            },
            'readable': {
                'hidden_features': [
                    ZenFeature.MENU_BAR, ZenFeature.STATUS_BAR,
                    ZenFeature.SIDEBAR, ZenFeature.MINIMAP
                ],
                'typography': TypographySettings(
                    font_family="Merriweather", font_size=16,
                    line_height=1.8, max_width=680,
                    text_align="justify"
                ),
                'focus_current_paragraph': False,
                'typewriter_mode': False,
            },
            'code': {
                'hidden_features': [
                    ZenFeature.MENU_BAR, ZenFeature.STATUS_BAR,
                    ZenFeature.SIDEBAR, ZenFeature.MINIMAP
                ],
                'typography': TypographySettings(
                    font_family="JetBrains Mono", font_size=14,
                    line_height=1.5, max_width=900
                ),
                'focus_current_paragraph': False,
                'typewriter_mode': False,
            },
        }
        
        preset = presets.get(preset_name)
        if preset:
            if 'hidden_features' in preset:
                self.hidden_features = preset['hidden_features'].copy()
            if 'typography' in preset:
                self.typography = preset['typography']
            if 'ambient' in preset:
                self.ambient = preset['ambient']
            if 'focus_current_paragraph' in preset:
                self.focus_current_paragraph = preset['focus_current_paragraph']
            if 'typewriter_mode' in preset:
                self.typewriter_mode = preset['typewriter_mode']
            if 'typewriter_position' in preset:
                self.typewriter_position = preset['typewriter_position']
            
            if self.active and self.on_settings_change:
                self.on_settings_change()
    
    def get_css(self) -> str:
        """Generate CSS for Zen mode styling."""
        return f'''
.zen-mode {{
    background-color: {self.ambient.background_color};
    color: {self.ambient.text_color};
    opacity: {self.ambient.opacity};
}}

.zen-mode .editor {{
    font-family: '{self.typography.font_family}', serif;
    font-size: {self.typography.font_size}px;
    line-height: {self.typography.line_height};
    letter-spacing: {self.typography.letter_spacing}em;
    max-width: {self.typography.max_width}px;
    text-align: {self.typography.text_align};
    margin: 0 auto;
    padding: 40px 20px;
}}

.zen-mode .paragraph {{
    margin-bottom: {self.typography.paragraph_spacing}em;
}}

.zen-mode .dimmed {{
    opacity: {self.focus_opacity};
    transition: opacity 0.3s ease;
}}

.zen-mode .current-paragraph {{
    opacity: 1.0;
}}
'''
    
    def get_status_text(self) -> str:
        """Get status text for Zen mode."""
        return f"ZEN MODE | {self.typography.font_family} {self.typography.font_size}px | {self.typography.max_width}px"


class FocusTracker:
    """Tracks focus for paragraph/sentence highlighting."""
    
    def __init__(self):
        self.current_paragraph_start: int = 0
        self.current_paragraph_end: int = 0
        self.current_sentence_start: int = 0
        self.current_sentence_end: int = 0
    
    def update(self, content: str, cursor_pos: int) -> None:
        """Update focus based on cursor position."""
        # Find paragraph boundaries
        self.current_paragraph_start = content.rfind('\n\n', 0, cursor_pos)
        if self.current_paragraph_start == -1:
            self.current_paragraph_start = 0
        else:
            self.current_paragraph_start += 2
        
        self.current_paragraph_end = content.find('\n\n', cursor_pos)
        if self.current_paragraph_end == -1:
            self.current_paragraph_end = len(content)
        
        # Find sentence boundaries
        self._find_sentence(content, cursor_pos)
    
    def _find_sentence(self, content: str, cursor_pos: int) -> None:
        """Find the current sentence boundaries."""
        import re
        
        # Find all sentence boundaries
        pattern = r'[.!?]+\s+'
        matches = list(re.finditer(pattern, content))
        
        self.current_sentence_start = 0
        self.current_sentence_end = len(content)
        
        for i, match in enumerate(matches):
            if match.end() > cursor_pos:
                self.current_sentence_end = match.end()
                if i > 0:
                    self.current_sentence_start = matches[i-1].end()
                break
            elif i == len(matches) - 1:
                self.current_sentence_start = match.end()
    
    def is_in_focus(self, pos: int, paragraph_focus: bool, sentence_focus: bool) -> bool:
        """Check if a position is in the focused region."""
        if paragraph_focus:
            return self.current_paragraph_start <= pos <= self.current_paragraph_end
        if sentence_focus:
            return self.current_sentence_start <= pos <= self.current_sentence_end
        return True


__all__ = ['ZenMode', 'ZenFeature', 'TypographySettings', 'AmbientSettings', 'FocusTracker']
