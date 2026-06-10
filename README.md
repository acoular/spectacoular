[![PyPI](https://img.shields.io/pypi/pyversions/spectacoular.svg)](https://pypi.org/project/spectacoular)
[![PyPI](https://img.shields.io/pypi/v/spectacoular.svg)](https://pypi.org/project/spectacoular)
[![DOI](https://zenodo.org/badge/DOI/10.5281/5242826.svg)](https://zenodo.org/doi/10.5281/zenodo.5242826)

![Poster](https://github.com/acoular/spectacoular/blob/master/docs/_static/poster.png)

## Package Documentation

The documentation for the SpectAcoular package is available at [https://acoular.github.io/spectacoular/](https://acoular.github.io/spectacoular/).

## Quick Start

Install **SpectAcoular** with `uv`:

```console
$ uv venv
$ uv pip install spectacoular
```

To install optional dependencies needed for live-audio and measurement applications, use:

```console
$ uv pip install 'spectacoular[full]'
```

To verify your installation, start one of the included applications:

```console
$ uv run micgeom_app --show
```

A browser window or tab should open with the microphone geometry application.

For more detailed installation instructions, see the [installation guide](https://acoular.github.io/spectacoular/install/index.html).
