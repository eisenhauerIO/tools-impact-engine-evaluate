"""Sphinx configuration for impact-engine-evaluate."""

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

project = "Impact Engine Evaluate"
copyright = "2024, Impact Engine Team"
author = "Impact Engine Team"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"

napoleon_numpy_docstring = True
