#!/usr/bin/env python3
"""
MarkMark - Advanced Markdown Multitool
Setup script for installation.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text()

setup(
    name="markmark",
    version="1.0.0",
    author="MarkMark Team",
    author_email="markmark@example.com",
    description="Advanced Markdown Multitool with Vim-mode, Zen-mode, CLI mode, and more",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/markmark/markmark",
    license="MIT",
    
    packages=find_packages(),
    include_package_data=True,
    
    python_requires=">=3.9",
    
    install_requires=[
        "PyGObject>=3.42.0",
    ],
    
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "mypy>=0.950",
            "flake8>=4.0.0",
        ],
        "export": [
            "weasyprint>=53.0",
            "python-docx>=0.8.11",
        ],
        "spell": [
            "pyenchant>=3.2.0",
        ],
    },
    
    entry_points={
        "console_scripts": [
            "markmark=main:main",
            "mm=main:main",
        ],
    },
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Text Editors",
        "Topic :: Text Processing :: Markup :: Markdown",
        "Typing :: Typed",
    ],
    
    keywords="markdown editor gtk vim zen-mode cli helix neovim",
    
    project_urls={
        "Bug Tracker": "https://github.com/markmark/markmark/issues",
        "Documentation": "https://github.com/markmark/markmark#readme",
        "Source Code": "https://github.com/markmark/markmark",
    },
)
