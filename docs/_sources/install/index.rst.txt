Installation
============

Requirements
------------

SpectAcoular runs under 64bit Windows and Linux (it should also run under OS X, but this is untested).
In order to install SpectAcoular you need a Python 3 environment with the following Python Packages installed:

    * `Acoular <http://www.acoular.org/>`_, 
    * `Bokeh <https://docs.bokeh.org/en/latest/index.html#>`_, 

The recommended Anaconda installation below ensures that the required packages will be installed properly. 

Anaconda (Windows and Linux)
----------------------------------------------------

This option assumes that you have the `Anaconda <https://www.anaconda.com/download/>`_ Python-distribution installed on your computer. If this is not the case you may `download <https://www.anaconda.com/download/>`_ and install it (highly recommended). **You may install Anaconda alongside any other Python installation on your system**, without the need to interfere with the other Python installation.

Once Anaconda Python is properly installed and works, start a console, i.e. either "cmd" or the "Anaconda command prompt" on Windows, Terminal on Linux.
In the command line, type

.. code-block:: console

    $ conda install -c acoular spectacoular

This will install SpectAcoular in your Anaconda Python environment and make the SpectAcoular library available from Python. In addition, this will install all dependencies (those other packages mentioned above) if they are not already present on your system.
Depending on your type of Anaconda installation (single user or system-wide), you may be asked for admin privileges in order to start the installation process.


