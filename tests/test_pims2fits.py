"""
Unit test for pims2fits.py script.
"""

import os
import sys
import glob
import numpy as np
import shutil
import tempfile
import unittest
import subprocess

from lsl_toolkits.PasiImage import PasiImageDB
from astropy.io import fits

currentDir = os.path.abspath(os.getcwd())
if os.path.exists(os.path.join(currentDir, 'tests', 'test_pims2fits.py')):
    MODULE_BUILD = currentDir
else:
    MODULE_BUILD = None
    
run_scripts_tests = False
if MODULE_BUILD is not None:
    run_scripts_tests = True

__version__  = "0.1"
__author__    = "Jayce Dowell"


pimsFile = os.path.join(os.path.dirname(__file__), 'data', 'test.pims')



@unittest.skipUnless(run_scripts_tests, "cannot determine correct script path to use")
class pims2fits_tests(unittest.TestCase):
    """A unittest.TestCase collection of unit tests for the pims2fits.py
    script."""
    
    testPath = None

    def setUp(self):
        """Turn off all numpy warnings and create the temporary file directory."""

        np.seterr(all='ignore')
        self.testPath = tempfile.mkdtemp(prefix='test-pims2fits-', suffix='.tmp')
        
    def tearDown(self):
        try:
            shutil.rmtree(self.testPath)
        except OSError:
            pass
            
    def run_pims2fits(self, *args, print_on_failure=True):
        """
        Run pims2fits.py with the specified arguements and return the subprocess
        status code.
        """
        
        status = 1
        with open(os.path.join(self.testPath, 'pims2fits.log'), 'w') as logfile:
            try:
                cmd = [sys.executable, os.path.join(MODULE_BUILD, 'scripts/pims2fits.py')]
                cmd.extend(args)
                
                status = subprocess.check_call(cmd, stdout=logfile, cwd=self.testPath)
                
            except subprocess.CalledProcessError:
                pass
                
        if status == 1:
            with open(os.path.join(self.testPath, 'pims2fits.log'), 'r') as logfile:
                print(logfile.read())
                
        return status
        
    def test_pims2fitsdef_oims_run(self):
        """Create fits from oims with default settings"""

        status = self.run_pims2fits(pimsFile)
        self.assertEqual(status, 0)

        db = PasiImageDB(pimsFile, 'r')
        nStokes = len(db.header.stokesParams.split(','))
        xSize = db.header.xSize
        ySize = db.header.ySize

        fitsFiles = sorted(glob.glob(os.path.join(self.testPath, '*.fits')))
        self.assertEqual(len(fitsFiles), db.nIntegrations)

        for i,f in enumerate(fitsFiles):
            db.seek(i)
            hdr, data, spec = db.readImage()

            with fits.open(f) as hdul:
                hdu = hdul[0]

                # Shape: transposed from (nStokes, xSize, ySize)
                #        to (nStokes, ySize, xSize) by pims2fits
                self.assertEqual(hdu.data.shape, (nStokes, ySize, xSize))

                # Key FITS headers
                self.assertIn('DATE-OBS', hdu.header)
                self.assertEqual(hdu.header['CTYPE1'], 'RA---SIN')
                self.assertEqual(hdu.header['CTYPE2'], 'DEC--SIN')
                self.assertIn('RESTFREQ', hdu.header)
                self.assertIn('EXPTIME', hdu.header)

                # Frequency matches the pims integration header
                self.assertAlmostEqual(hdu.header['RESTFREQ'], hdr['freq'], 1)

        db.close()


class pims2fits_test_suite(unittest.TestSuite):
    """A unittest.TestSuite class which contains all of the pims2fits.py
    unit tests."""
    
    def __init__(self):
        unittest.TestSuite.__init__(self)
        
        loader = unittest.TestLoader()
        self.addTests(loader.loadTestsFromTestCase(pims2fits_tests)) 


if __name__ == '__main__':
    unittest.main()
