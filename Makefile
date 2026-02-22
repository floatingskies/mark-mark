# MarkMark Makefile

PYTHON = python3
PIP = pip3

.PHONY: all install uninstall run clean test lint format help

all: install

help:
	@echo "MarkMark - Advanced Markdown Multitool"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install      Install MarkMark and dependencies"
	@echo "  uninstall    Remove MarkMark"
	@echo "  run          Run MarkMark GUI"
	@echo "  run-cli      Run MarkMark CLI"
	@echo "  clean        Remove build artifacts"
	@echo "  test         Run tests"
	@echo "  lint         Run linters"
	@echo "  format       Format code"
	@echo "  dist         Create distribution packages"
	@echo ""

install:
	$(PIP) install -e .

install-deps-debian:
	sudo apt update
	sudo apt install -y python3-gi python3-gi-cairo \
		gir1.2-gtk-4.0 gir1.2-gtksource-5 gir1.2-adw-1 \
		libgtk-4-dev libgtksourceview-5-dev libadwaita-1-dev

install-deps-fedora:
	sudo dnf install -y python3-gobject gtk4 gtksourceview5-devel \
		libadwaita-devel

install-deps-arch:
	sudo pacman -S --needed python-gobject gtk4 gtksourceview5 libadwaita

uninstall:
	$(PIP) uninstall -y markmark

run:
	$(PYTHON) main.py

run-cli:
	$(PYTHON) main.py -c

clean:
	rm -rf build/ dist/ *.egg-info __pycache__ .pytest_cache .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

test:
	$(PYTHON) -m pytest tests/ -v --cov=.

lint:
	$(PYTHON) -m flake8 . --max-line-length=100
	$(PYTHON) -m mypy .

format:
	$(PYTHON) -m black .
	$(PYTHON) -m isort .

dist: clean
	$(PYTHON) -m build

install-desktop:
	mkdir -p ~/.local/share/applications
	mkdir -p ~/.local/share/icons/hicolor/scalable/apps
	cp markmark.desktop ~/.local/share/applications/
	cp icons/markmark.svg ~/.local/share/icons/hicolor/scalable/apps/
	update-desktop-database ~/.local/share/applications

uninstall-desktop:
	rm -f ~/.local/share/applications/markmark.desktop
	rm -f ~/.local/share/icons/hicolor/scalable/apps/markmark.svg
	update-desktop-database ~/.local/share/applications
