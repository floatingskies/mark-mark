#!/bin/bash
# MarkMark Installation Script
# Run this to set up MarkMark on your system

set -e

echo "========================================="
echo "  MarkMark - Advanced Markdown Editor"
echo "========================================="
echo ""

# Detect OS
if [ -f /etc/debian_version ]; then
    OS="debian"
    echo "Detected: Debian/Ubuntu"
elif [ -f /etc/fedora-release ]; then
    OS="fedora"
    echo "Detected: Fedora"
elif [ -f /etc/arch-release ]; then
    OS="arch"
    echo "Detected: Arch Linux"
else
    OS="unknown"
    echo "Warning: Unknown OS. You may need to install dependencies manually."
fi

# Install system dependencies
echo ""
echo "Installing system dependencies..."
echo ""

case $OS in
    debian)
        sudo apt update
        sudo apt install -y \
            python3-gi \
            python3-gi-cairo \
            gir1.2-gtk-4.0 \
            gir1.2-gtksource-5 \
            gir1.2-adw-1
        ;;
    fedora)
        sudo dnf install -y \
            python3-gobject \
            gtk4 \
            gtksourceview5-devel \
            libadwaita-devel
        ;;
    arch)
        sudo pacman -S --needed \
            python-gobject \
            gtk4 \
            gtksourceview5 \
            libadwaita
        ;;
    *)
        echo "Please install the following packages manually:"
        echo "  - PyGObject (python3-gi)"
        echo "  - GTK 4"
        echo "  - GtkSourceView 5"
        echo "  - libadwaita (optional)"
        ;;
esac

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "Testing installation..."
echo ""

# Test Python imports
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')

# Test GTK
print('Testing GTK...')
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
print('  ✓ GTK 4.0')

# Test GtkSourceView
try:
    gi.require_version('GtkSource', '5')
    from gi.repository import GtkSource
    print('  ✓ GtkSourceView 5')
except:
    print('  ⚠ GtkSourceView 5 not available (optional)')

# Test core modules
print('Testing core modules...')
from core.config import ConfigManager
print('  ✓ config')
from core.vim_mode import VimMode
print('  ✓ vim_mode')
from core.helix_mode import HelixFeatures
print('  ✓ helix_mode')
from core.zen_mode import ZenMode
print('  ✓ zen_mode')
from core.markdown_processor import MarkdownRenderer
print('  ✓ markdown_processor')
from core.notes import NoteManager
print('  ✓ notes')
from core.cli_mode import CLIMode
print('  ✓ cli_mode')
from core.plugin_system import PluginManager
print('  ✓ plugin_system')

print()
print('All imports successful!')
"

echo ""
echo "========================================="
echo "  Installation Complete!"
echo "========================================="
echo ""
echo "To run MarkMark:"
echo "  cd '$SCRIPT_DIR'"
echo "  python3 run.py [file.md]"
echo ""
echo "For CLI mode:"
echo "  python3 run.py -c [file.md]"
echo ""
echo "For help:"
echo "  python3 run.py --help"
echo ""
