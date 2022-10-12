"""Sphinx configuration."""
from datetime import datetime


project = "Spiffworkflow Backend"
author = "Sartography"
copyright = f"{datetime.now().year}, {author}"
extensions = [
    "sphinx.ext.napoleon",
    "autoapi.extension",
    "sphinx_click",
]

# https://github.com/readthedocs/sphinx-autoapi
autoapi_type = "python"
autoapi_dirs = ["../src"]
html_theme = "furo"
