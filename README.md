LSL Toolkit for Images Created by the Prototype All-Sky Imager (PASI)
=====================================================================
[![Build and Test](https://github.com/lwa-project/pasi_image/actions/workflows/main.yml/badge.svg)](https://github.com/lwa-project/pasi_image/actions/workflows/main.yml)  [![codecov](https://codecov.io/gh/lwa-project/pasi_image/branch/master/graph/badge.svg?token=3UO1IC8GVN)](https://codecov.io/gh/lwa-project/pasi_image)


### [![Paper](https://img.shields.io/badge/arXiv-1503.05150-blue.svg)](https://arxiv.org/abs/1503.05150)

**Note:** PASI stopped producing data on 2025 March 1 (MJD 60735).  This
package is now in maintenance mode for archival access to existing data.

DESCRIPTION
-----------
This package provides the PasiImageDB class that is used to read images
created by the Prototype All-Sky Imager that was running at LWA1.  This
reader supports all three versions of the PASI image format found on the
LWA1 data archive.

REQUIREMENTS
------------
  * python >= 3.6
  * numpy >= 1.2
  * lsl >= 2.0 (required for some of the scripts)
  * matplotlib >= 0.98.3 (required for some of the scripts)
  * astropy >= 2.0 (required for some of the scripts)

INSTALLING
----------
Install PasiImage by running:

    pip install [--user] .

UNIT TESTS
----------
To run the complete suite of package unit tests:

    python -m pytest tests/

DOCUMENTATION
-------------
See the module's internal documentation.

RELEASE NOTES
-------------
See the CHANGELOG for a detailed list of changes and notes.
