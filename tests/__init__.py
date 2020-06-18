"""
Modules defining package tests.
"""

# Python2 compatibility
from __future__ import print_function, division, absolute_import
import sys
if sys.version_info < (3,):
    range = xrange
    
__version__   = "0.1"
__author__    = "Jayce Dowell"

from . import test_pims
from . import test_scripts

