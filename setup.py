# coding=UTF-8
#------------------------------------------------------------------------------
# Copyright (c) 2020-2021, Acoular Development Team.
#------------------------------------------------------------------------------
from setuptools import setup
from os.path import join, abspath, dirname
import os


bf_version = "22.08"
bf_author = "Acoular Development Team"

# Get the long description from the relevant file
here = abspath(dirname(__file__))
with open(join(here, 'README.rst')) as f:
    long_description = f.read()


install_requires = list([
      'acoular>=21.05',
      'setuptools',	
      'bokeh >=1.3.0',

	])

#if "CONDA_PREFIX" not in os.environ:
#    install_requires.append('PyQt5>=5.6;python_version>="3.4"')

setup_requires = list([
      'acoular>=20.02',
      'setuptools',	
      'bokeh >=1.3.0',
	])

#if "CONDA_PREFIX" not in os.environ:
#    setup_requires.append('python-qt5;python_version<="2.7"')
#    setup_requires.append('PyQt5>=5.6;python_version>="3.4"')

    
setup(name="spectacoular", 
      version=bf_version, 
      description="Library for SpectAcoular interactive applications with Acoular",
      long_description=long_description,
      license="BSD",
      author=bf_author,
      author_email="info@acoular.org",
      url="https://acoular.github.io/spectacoular/",
      classifiers=[
      'Development Status :: 5 - Production/Stable',
      'Intended Audience :: Education',
      'Intended Audience :: Science/Research',
      'Topic :: Scientific/Engineering :: Physics',
      'License :: OSI Approved :: BSD License',
      'Programming Language :: Python :: 3.7',
      'Programming Language :: Python :: 3.8',
      'Programming Language :: Python :: 3.9',      
      'Programming Language :: Python :: 3.10',      
      ],
      keywords='acoustic beamforming microphone array GUI',
      packages = ['spectacoular'],

      install_requires = install_requires,

      setup_requires = setup_requires,
      
      #scripts=[join('examples','acoular_demo.py')],
      include_package_data = True,
      #package_data={'acoular': ['xml/*.xml'],
	  #	    'acoular': ['tests/*.*']},
      #to solve numba compiler 
      zip_safe=False
)

