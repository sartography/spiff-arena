# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# note that backend had autoapi hooked up at one point to generate python API docs.
# if we want that again some day, here were the docs in that sub-folder docs dir:
#   https://github.com/sartography/spiff-arena/blob/d9b303db782b1004a818c426283e9cfbc5ed0ec7/spiffworkflow-backend/docs/conf.py

project = "SpiffWorkflow"
copyright = "2023, Sartography"
author = "Sartography"  # Very ok to add your name here.
release = "0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["myst_parser", "sphinxcontrib.mermaid"]
myst_fence_as_directive = ["mermaid"]
myst_heading_anchors = 2

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", ".venv"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
html_theme = "sphinx_rtd_theme"
html_static_path = ["static"]
html_logo = "spiffworkflow_logo.png"

html_theme_options = {
    "logo_only": True,
    "display_version": False,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "vcs_pageview_mode": "",
    # Toc options
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}


html_css_files = ["custom.css"]
