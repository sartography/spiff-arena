# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# note that backend had autoapi hooked up at one point to generate python API docs.
# if we want that again some day, here were the docs in that sub-folder docs dir:
#   https://github.com/sartography/spiff-arena/blob/d9b303db782b1004a818c426283e9cfbc5ed0ec7/spiffworkflow-backend/docs/conf.py

project = "SpiffArena"
copyright = "2026, SpiffWorks"
author = "SpiffWorks"  # Very ok to add your name here.
release = "0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["myst_parser", "sphinxcontrib.mermaid", "sphinx_tags"]
myst_fence_as_directive = ["mermaid"]
myst_heading_anchors = 2

# tags are sort of annoying and buggy, given that the individual tag show pages are broken when clicked from leaf node pages
# and they are required to be in the top-level toctree, which forces the side nav to highlight the current page twice, once
# where it belongs and once in the tags section.
# tags_create_tags = True
tags_extension = ["md"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", ".venv"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "spiffworks"
html_theme_path = ["_themes"]
html_static_path = ["static"]
html_logo = "spiffworkflow_logo.png"

html_css_files = ["custom.css"]
