LSL Toolkit for Images Created by the Prototype All-Sky Imager (PASI)
=====================================================================
[![Build and Test](https://github.com/lwa-project/pasi_image/actions/workflows/main.yml/badge.svg)](https://github.com/lwa-project/pasi_image/actions/workflows/main.yml)  [![codecov](https://codecov.io/gh/lwa-project/pasi_image/branch/master/graph/badge.svg?token=3UO1IC8GVN)](https://codecov.io/gh/lwa-project/pasi_image)


### [![Paper](https://img.shields.io/badge/arXiv-1503.05150-blue.svg)](https://arxiv.org/abs/1503.05150)

DESCRIPTION
-----------
This package provides the the PasiImageDB class that is used to
read images created by the Prototype All-Sky Imager running at 
LWA1.  This reader supports all three versions of the PASI image
format found on the LWA1 data archive.

REQUIREMENTS
------------
  * python >= 2.7
  * numpy >= 1.2
  * lsl >= 1.3 (required for some of the scripts)
  * matplotlib >= 0.98.3 (required for some of the scripts)
  * astropy >= 2.0 (required for some of the scripts)

INSTALLING
----------
The PasiImage package is installed as a regular Python package using distutils.  
Unzip and untar the source distribution. Setup the python interpreter you 
wish to use for running the package applications and switch to the root of 
the source distribution tree.

Install PasiImage by running:
    
    pip install [--root=<prefix>|--user] .

If the '--root' option is not provided, then the installation tree root directory 
is the same as for the Python interpreter used to run `setup.py`.  For instance, 
if the Python interpreter is in '/usr/local/bin/python', then '<prefix>' will be 
set to '/usr/local'.  Otherwise, the explicit <prefix> value is taken from the 
command line option.  The package will install files in the following locations:
 * <prefix>/bin
 * <prefix>/lib/python2.6/site-packages
 * <prefix>/share/doc
 * <prefix>/share/install

If an alternate '<prefix>' value is provided, you should set the PATH environment 
to include directory '<prefix>/bin' and the PYTHONPATH environment to include 
directory '<prefix>/lib/python2.6/site-packages'.

If the '--user' option is provided, then then installation tree root directory will 
be in the current user's home directory.

UNIT TESTS
----------
Unit tests for the package may be found in the 'PasiImage/tests' sub-directory in 
the package source distribution tree.  To run the complete suite of package unit 
tests:

    cd tests
    python -m unittest discover

DOCUMENTATION
-------------
See the module's internal documentation.

RELEASE NOTES
-------------
See the CHANGELOG for a detailed list of changes and notes.
