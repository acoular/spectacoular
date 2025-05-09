Installation
============

Requirements
------------

SpectAcoular runs under 64bit Windows and Linux (it should also run under OS X, but this is untested).
In order to install SpectAcoular you need a Python 3 environment with the following Python Packages installed:

    * `Acoular <http://www.acoular.org/>`_, 
    * `Bokeh <https://docs.bokeh.org/en/latest/index.html#>`_, 

There are also optional dependencies that are required for some of the applications:

    * `OpenCV <https://opencv.org/>`_ (only for the Measurement App),
    * `Sounddevice <https://python-sounddevice.readthedocs.io/en/0.4.1/>`_ (only for the Measurement App),

Installation with pip
---------------------

One easy way to install SpectAcoular is to use the Python package manager `pip <https://pip.pypa.io/en/stable/>`_.
In order to install SpectAcoular with pip, open a console, i.e. either "cmd" or the "Anaconda command prompt" on Windows, Terminal on Linux.

In the command line, type

.. code-block:: console

    $ pip install spectacoular

This will install SpectAcoular in your Python environment and make the SpectAcoular library available from Python. 
If you want to install the optional dependencies, you can do so by running

.. code-block:: console

    $ pip install spectacoular[full]


Installation with conda, micromamba or mamba
----------------------------------------------------

This option assumes that you have the `Anaconda <https://www.anaconda.com/download/>`_ Python-distribution (or alternatively mamba / micromamba) 
installed on your computer. **You may install Anaconda alongside any other Python installation on your system**, without the need to interfere with 
the other Python installation.

Once Anaconda Python is properly installed and works, start a console, i.e. either "cmd" or the "Anaconda command prompt" on Windows, Terminal on Linux.
In the command line, type

.. code-block:: console

    $ conda install -c acoular spectacoular


This will install SpectAcoular in your Anaconda Python environment and make the SpectAcoular library available from Python. 
In addition, this will install all dependencies (those other packages mentioned above) if they are not already present on your system.
Depending on your type of Anaconda installation (single user or system-wide), you may be asked for admin privileges in order to start the installation process.


