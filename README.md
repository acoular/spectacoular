
![Poster](https://github.com/acoular/spectacoular/blob/master/docs/_static/poster.png)

## Package Documentation

The documentation for the SpectAcoular package is available at [https://acoular.github.io/spectacoular/](https://acoular.github.io/spectacoular/).

## Quick Start

To install **SpectAcoular**, one can use the Anaconda Python distribution or the Python package manager `pip`. The following instructions describe how to install SpectAcoular using the Anaconda Python distribution.
In the command line, type:

```console
$ conda install -c acoular spectacoular
```

This will install SpectAcoular in your Anaconda Python environment and make the SpectAcoular library available from Python. In addition, this will install all dependencies (those other packages mentioned above) if they are not already present on your system.

Alternatively, one can use `pip` to install SpectAcoular. In the command line, type:

```console
$ pip install spectacoular
```

Note that for some pre-built applications, additional optional packages are required:

- `python-sounddevice` (for sound output)
- `opencv` (for image display)

When using pip, one can install the optional packages by specifying the `full` option:

```console
$ pip install spectacoular[full]
```

If you use conda, optional packages are not included and need to be installed separately. To verify your installation, you can run one of the pre-built interactive applications (e.g. MicGeomExample app). To do so, type the following command in a dedicated console (e.g. shell):

```console
$ micgeom_app
```

A new window should appear in the browser running the application.

    