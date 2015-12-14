# -*- coding: utf-8 -*-

import ez_setup
ez_setup.use_setuptools()

import glob

from setuptools import setup, Extension, Distribution, find_packages

try:
	import numpy
except ImportError:
	pass

setup(
  name                 = "PasiImage",
  version              = "0.1.0",
  description          = "Python reader for PASI Image Database files",
  url                  = "http://fornax.phys.unm.edu/lwa/trac/", 
  author               = "Jake Hartman",
  author_email         = "jdowell@unm.edu",
  license              = 'GPL',
  classifiers          = ['Development Status :: 4 - Beta',
				   'Intended Audience :: Science/Research',
				   'License :: OSI Approved :: GNU General Public License (GPL)',
				   'Topic :: Scientific/Engineering :: Astronomy'],
  packages             = find_packages(exclude="tests"), 
  namespace_packages   = ['lsl_toolkits',],
  scripts              = glob.glob('scripts/*.py'), 
  include_package_data = True,  
  zip_safe             = False,  
)