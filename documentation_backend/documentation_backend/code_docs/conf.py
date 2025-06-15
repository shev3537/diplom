# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------

project = 'code-docs'
copyright = '2025, Kirill'
author = 'Kirill'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',  # если используешь автодокументацию
]

# Модули, которые нужно мокировать (не импортировать) при сборке
autodoc_mock_imports = ["flask"]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = 'ru'  # если нужна русская локализация

master_doc = 'index'  # главный документ

# -- Options for HTML output -------------------------------------------------

html_theme = 'alabaster'
html_static_path = ['_static']
