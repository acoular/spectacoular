"""Sphinx configuration for the SpectAcoular documentation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path('../..').resolve()))

from spectacoular.version import __version__ as version

from acoular_sphinx import (
    COMMON_EXTENSIONS,
    build_github_context,
    build_html_context,
    configure_package_theme_options,
    resolve_docs_build_config,
)

project = 'SpectAcoular'
author = 'Acoular Development Team'
globals()['copyright'] = f'2015-%Y, {author}'
today_fmt = '%B %d, %Y'
docs_build = resolve_docs_build_config(
    default_version_match='dev' if 'dev' in version else version,
)

extensions = [
    *COMMON_EXTENSIONS,
    'bokeh.sphinxext.bokeh_plot',
    'sphinx.ext.doctest',
    'sphinx.ext.githubpages',
    'sphinx_design',
    'sphinx_copybutton',
    'sphinx_gallery.gen_gallery',
    'numpydoc',
]

templates_path = ['_templates']

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']
html_context = {
    **build_html_context(),
    **build_github_context(
        github_user='acoular',
        github_repo='spectacoular',
        github_version='master',
        doc_path='docs',
    ),
}
html_theme_options = configure_package_theme_options(
    package_name='SpectAcoular',
    github_url='https://github.com/acoular/spectacoular',
    pypi_project='spectacoular',
    use_edit_page_button=True,
    switcher_json_url='https://acoular.org/spectacoular/_static/switcher.json',
    version_match=docs_build['version_match'],
)
html_sidebars = {
    '**': ['sidebar-nav-bs.html'],
}
html_favicon = '_static/acoular_logo.ico'
html_last_updated_fmt = '%b %d, %Y'
html_baseurl = docs_build['html_baseurl']
html_copy_source = False

# sphinx_copybutton config
# ------------------------
copybutton_prompt_text = r'>>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: '  # strips prompts
copybutton_prompt_is_regexp = True

autosummary_generate = True
autosummary_generate_overwrite = True

# %%
# sphinx.ext.autodoc extension settings
# -------------------------------------

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'exclude-members': 'trait_added,trait_modified',
    'inherited-members': 'ABCHasStrictTraits,HasStrictTraits,HasTraits,CHasTraits',
    'show-inheritance': True,  # False does not work, need to delete this line to deactivate!
}

numpydoc_show_class_members = False
numpydoc_show_inherited_class_members = False
numpydoc_class_members_toctree = False

html_css_files = ['css/sphinx_gallery.css', 'css/custom_pydata_sphinx_theme.css']

sphinx_gallery_conf = {
    'gallery_dirs': 'auto_examples',
    'example_extensions': {'.py'},
    'download_all_examples': False,
    'examples_dirs': ['../examples'],
}

intersphinx_mapping = {
    'acoular': ('https://acoular.org', None),
    'h5py': ('https://docs.h5py.org/en/stable/', None),
    'matplotlib': ('https://matplotlib.org/stable', None),
    'numpy': ('https://numpy.org/doc/stable', None),
    'python': (f'https://docs.python.org/{sys.version_info.major}', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
    'traits': ('https://docs.enthought.com/traits', None),
}
