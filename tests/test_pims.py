# -*- coding: utf-8 -*-

"""Unit test for lsl_toolkit.PasiImage module"""

import os
import numpy
import tempfile
import unittest

from lsl_toolkits import PasiImage as PasiImage


__revision__ = "$ Revision: 2 $"
__version__  = "0.1"
__author__    = "Jayce Dowell"


pimsFile = os.path.join(os.path.dirname(__file__), 'data', 'test.pims')


class pims_tests(unittest.TestCase):
    """A unittest.TestCase collection of unit tests for the lsl_toolkits.PasiImage
    module."""
    
    testPath = None

    def setUp(self):
        """Turn off all numpy warnings and create the temporary file directory."""

        numpy.seterr(all='ignore')
        self.testPath = tempfile.mkdtemp(prefix='test-pims-', suffix='.tmp')
        
    def test_pims_read(self):
        """Test reading in an image from a PasiImage file."""

        db = PasiImage.PasiImageDB(pimsFile, 'r')
        
        # Read in the first image with the correct number of elements
        hdr, data, spec = db.readImage()
        ## Image
        self.assertEqual(data.shape[0], len(db.header.stokesParams.split(',')))
        self.assertEqual(data.shape[1], db.header.xSize)
        self.assertEqual(data.shape[2], db.header.ySize)
        ## Spectra
        self.assertEqual(spec.shape[0], db.header.nSpecChans)
        
        db.close()
        
    def test_pims_loop(self):
        """Test reading in a collection of images in a loop."""
        
        db = PasiImage.PasiImageDB(pimsFile, 'r')
        
        # Go
        for i,(hdr,data,spec) in enumerate(db):
            i
            
        db.close()
        
    def test_pims_write(self):
        """Test saving data to the PasiImageDB format."""
        
        # Setup the file names
        testFile = os.path.join(self.testPath, 'test.pims')
        
        db = PasiImage.PasiImageDB(pimsFile, 'r')
        nf = PasiImage.PasiImageDB(testFile, 'w', corrVersion=db.header.corrVersion, 
                                            imagerVersion=db.header.imagerVersion, 
                                            station=db.header.station)
                                            
        # Fill it
        for rec in db:
            nf.addImage(*rec)
            
        # Done
        db.close()
        nf.close()
        
        # Re-open
        db0 = PasiImage.PasiImageDB(pimsFile, 'r')
        db1 = PasiImage.PasiImageDB(testFile, 'r')
        
        # Validate
        ## File header
        for attr in ('corrVersion', 'imagerVersion', 'station', 'stokesParams', 'xSize', 'ySize', 'nSpecChans', 'flags'):
            self.assertEqual(getattr(db0.header, attr, None), getattr(db1.header, attr, None))
        for attr in ('xPixelSize', 'yPixelSize', 'startTime', 'stopTime'):
            self.assertAlmostEqual(getattr(db0.header, attr, None), getattr(db1.header, attr, None), 6)
        ## First image
        ### Image header
        hdr0, img0, spec0 = db0.readImage()
        hdr1, img1, spec1 = db1.readImage()
        for attr in ('visFileName', 'stokesParams'):
            self.assertEqual(getattr(hdr0, attr, None), getattr(hdr1, attr, None))
        for attr in ('startTime', 'centroidTime', 'intLen', 'lst', 'freq', 'bandwidth', 'gain', 'fill', 'zenithRA', 'zenithDec', 'xPixelSize', 'yPixelSize'):
            self.assertAlmostEqual(getattr(hdr0, attr, None), getattr(hdr1, attr, None), 6)
        ### Image
        for i in xrange(img0.shape[0]):
            for j in xrange(img0.shape[1]):
                for k in xrange(img0.shape[2]):
                    self.assertAlmostEqual(img0[i,j,k], img1[i,j,k], 6)
        ### Spectra
        for i in xrange(spec0.shape[0]):
            self.assertAlmostEqual(spec0[i], spec1[i], 6)
            
        db0.close()
        db1.close()
        
    def tearDown(self):
        """Remove the test path directory and its contents"""
        
        tempFiles = os.listdir(self.testPath)
        for tempFile in tempFiles:
            os.unlink(os.path.join(self.testPath, tempFile))
        os.rmdir(self.testPath)
        self.testPath = None


class pims_test_suite(unittest.TestSuite):
    """A unittest.TestSuite class which contains all of the lsl_toolkits.PasiImage units 
    tests."""
    
    def __init__(self):
        unittest.TestSuite.__init__(self)
        
        loader = unittest.TestLoader()
        self.addTests(loader.loadTestsFromTestCase(pims_tests)) 


if __name__ == '__main__':
    unittest.main()
