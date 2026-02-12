
import glob

from setuptools import setup, find_namespace_packages

try:
    import numpy
except ImportError:
    pass

setup(
    name                 = "lsl-toolkits-pasiimage",
    version              = "0.4.0",
    description          = "LSL Toolkit for PASI Image Database Files", 
    long_description     = "LWA Software Library reader for PASI Image Database files",
    url                  = "https://fornax.phys.unm.edu/lwa/trac/", 
    author               = "Jake Hartman",
    author_email         = "jdowell@unm.edu",
    license              = 'GPL',
    classifiers          = ['Development Status :: 5 - Production/Stable',
                            'Intended Audience :: Developers',
                            'Intended Audience :: Science/Research',
                            'License :: OSI Approved :: GNU General Public License (GPL)',
                            'Topic :: Scientific/Engineering :: Astronomy',
                            'Programming Language :: Python :: 2',
                            'Programming Language :: Python :: 2.6',
                            'Programming Language :: Python :: 2.7',
                            'Operating System :: MacOS :: MacOS X',
                            'Operating System :: POSIX :: Linux'],
    packages             = find_namespace_packages(where='src/',
                                                   include=['lsl_toolkits.PasiImage']),
    package_dir          = {'': 'src'},
    scripts              = glob.glob('scripts/*.py'), 
    python_requires      = '>=3.6', 
    install_requires     = ['numpy', 'lsl'],
    include_package_data = True,  
    zip_safe             = False,  
    test_suite           = "tests"
)
