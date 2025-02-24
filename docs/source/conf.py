# Configuration file for the Sphinx documentation builder.
import os
import sys

# Get the absolute path to the `src` directory
sys.path.insert(0, os.path.abspath("../../src"))
# autodoc_mock_imports = ["cosmos_hurrywave",]

# -- Project information

project = 'CoSMoS'
copyright = 'Deltares'
author = 'Maarten van Ormondt'
release = '0.1'
version = '0.1.0'

# -- General configuration
extensions = [
    'autoapi.extension',
    # "sphinx-autoapi",  # Enable AutoAPI
    "sphinx_rtd_theme",  # Optional, if using ReadTheDocs theme
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    # 'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.autosectionlabel',
]

autosummary_generate = True
autosectionlabel_prefix_document = True
remove_from_toctrees = ["_generated/*"]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

# -- Options for EPUB output
epub_show_urls = 'footnote'


# -- AutoAPI Configuration ---------------------------------------------------
autoapi_type = "python"  # Set to Python
autoapi_dirs = ["../../src"]  # Adjust this to your source directory
autoapi_ignore = ["*utils*",]  # Optional: Ignore tests/setup files
autoapi_add_toctree = True  # Automatically add API docs to the ToC
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "special-members",
    "private-members",
]