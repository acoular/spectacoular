# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))




# -- Project information -----------------------------------------------------

project = 'SpectAcoular'
copyright = '2020, Acoular Development Team'
author = 'Acoular Development Team'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'bokeh.sphinxext.bokeh_plot',
    #'bokeh.sphinxext.bokeh_gallery',
    'sphinx_gallery.gen_gallery',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary', 
    'sphinx.ext.doctest', 
    'sphinx.ext.githubpages',
    'traits.util.trait_documenter',
    'numpydoc' #conda install -c anaconda numpydoc
]


# optional spell checking:
# conda install -c conda-forge sphinxcontrib-spelling
# conda install -c chen pyenchant
try:
    import sphinxcontrib.spelling
    extensions.append("sphinxcontrib.spelling")
except:
    pass

spelling_word_list_filename="spelling_wordlist.txt" # including words without spell check (Acoular, ...)

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# autosummary: https://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html
autosummary_generate = True
autodoc_member_order = 'bysource'
autosummary_generate_overwrite = True # alternatively generate stub files manually with sphinx-autogen *.rst
numpydoc_show_class_members = False # Whether to show all members of a class in the Methods and Attributes sections automatically.
numpydoc_show_inherited_class_members = False #Whether to show all inherited members of a class in the Methods and Attributes sections automatically.
numpydoc_class_members_toctree = False #Whether to create a Sphinx table of contents for the lists of class methods and attributes. If a table of contents is made, Sphinx expects each entry to have a separate page.

# -- Options for HTML output -------------------------------------------------

# The style sheet to use for HTML and HTML Help pages. A file of that name
# must exist either in Sphinx' static/ path, or in one of the custom paths
# given in html_static_path.
#html_style = 'default.css'
html_theme = 'haikuac'
html_theme_path = ['_themes/']

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']



#%%
# sphinx_gallery.gen_gallery extension settings
# ---------------------------------------------

# Custom CSS paths should either relative to html_static_path
# or fully qualified paths (eg. https://...)
# necessary to hide "go to the end" note etc.
html_css_files = ['sphinx_gallery.css']

# sphinx_gallery.gen_gallery extension configuration
sphinx_gallery_conf = {
    'gallery_dirs': 'auto_examples',  # path to where to save gallery generated output
    'example_extensions': {'.py'},
    'download_all_examples': False,  # whether to download all examples
    'examples_dirs': ['../examples'],   
}

#%% 
# intersphinx extension settings

intersphinx_mapping = {
    "numpy": ("https://numpy.org/doc/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    "matplotlib": ("https://matplotlib.org/stable", None),
    "bokeh": ("https://docs.bokeh.org/en/latest", None),
    "acoular": ("https://www.acoular.org/", None),
}