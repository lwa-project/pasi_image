#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import numpy
import getopt
import pyfits
from datetime import datetime, timedelta

from lsl.common.mcs import mjdmpm2datetime

from lsl_toolkits.PasiImage import PasiImageDB


def usage(exitCode=None):
    print """pims2fits.py - Convert the images contained in one or more .pims
files into FITS images.

Usage:  pims2fits.py [OPTIONS] file [file [...]]

Options:
-h, --help              Display this help information
-f, --force             Force overwriting of FITS files
-v, --verbose           Be verbose during the conversion
"""
    
    if exitCode is not None:
        sys.exit(exitCode)
    else:
        return True


def parseOptions(args):
    # Build up the configuration
    config = {}
    config['force'] = False
    config['verbose'] = False
    config['args'] = []
    
    # Read in and process the command line flags
    try:
        opts, args = getopt.getopt(args, "hfv", ["help", "force", "verbose"])
    except getopt.GetoptError, err:
        # Print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage(exitCode=2)
        
    # Work through opts
    for opt, value in opts:
        if opt in ('-h', '--help'):
            usage(exitCode=0)
        elif opt in ('-f', '--force'):
            config['force'] = True
        elif opt in ('-v', '--verbose'):
            config['verbose'] = True
        else:
            assert False
            
    # Add in arguments
    config['args'] = args
    
    # Return configuration
    return config


def main(args):
    # Parse the command line
    config = parseOptions(args)
    filenames = config['args']
    
    # Loop over input .pims files
    for filename in filenames:
        print "Working on '%s'..." % os.path.basename(filename)
        
        ## Open the image database
        try:
            db = PasiImageDB(filename, mode='r')
        except Exception as e:
            print "ERROR: %s" % str(e)
            continue
            
        ##  Loop over the images contained in it
        fitsCounter = 0
        for i,(header,data,spec) in enumerate(db):
            if config['verbose']:
                print "  working on integration #%i" % (i+1)
                
            ## Reverse the axis order so we can get it right in the FITS file
            data = numpy.transpose(data, [0,2,1])
            
            ## Save the image size for later
            imSize = data.shape[-1]
            
            ## Zero outside of the horizon so avoid problems
            pScale = header['xPixelSize']
            sRad   = 360.0/pScale/numpy.pi / 2
            x = numpy.arange(data.shape[-2]) - 0.5
            y = numpy.arange(data.shape[-1]) - 0.5
            x,y = numpy.meshgrid(x,y)
            invalid = numpy.where( ((x-imSize/2.0)**2 + (y-imSize/2.0)**2) > (sRad**2) )
            data[:, invalid[0], invalid[1]] = 0.0
            ext = imSize/(2*sRad)
            
            ## Convert the start MJD into a datetime instance and then use 
            ## that to come up with a stop time
            mjd = int(header['startTime'])
            mpm = int((header['startTime'] - mjd)*86400.0*1000.0)
            tInt = header['intLen']*86400.0
            dateObs = mjdmpm2datetime(mjd, mpm)
            dateEnd = dateObs + timedelta(seconds=int(tInt), microseconds=int((tInt-int(tInt))*1000000))
            if config['verbose']:
                print "    start time: %s" % dateObs
                print "    end time: %s" % dateEnd
                print "    integration time: %.3f s" % tInt
                print "    frequency: %.3f MHz" % header['freq']
                
            ## Create the FITS HDU and fill in the header information
            hdu = pyfits.PrimaryHDU(data=data)
            hdu.header['TELESCOP'] = 'LWA1'
            ### Date and time
            hdu.header['DATE-OBS'] = dateObs.strftime("%Y-%m-%dT%H:%M:%S")
            hdu.header['END_UTC'] = dateEnd.strftime("%Y-%m-%dT%H:%M:%S")
            hdu.header['EXPTIME'] = tInt
            ### Coordinates - sky
            hdu.header['CTYPE1'] = 'RA---SIN'
            hdu.header['CRPIX1'] = imSize/2 + 1 + 0.5 * ((imSize+1)%2)
            hdu.header['CDELT1'] = -360.0/(2*sRad)/numpy.pi
            hdu.header['CRVAL1'] = header['zenithRA']
            hdu.header['CUNIT1'] = 'deg'
            hdu.header['CTYPE2'] = 'DEC--SIN'
            hdu.header['CRPIX2'] = imSize/2 + 1 + 0.5 * ((imSize+1)%2)
            hdu.header['CDELT2'] = 360.0/(2*sRad)/numpy.pi
            hdu.header['CRVAL2'] = header['zenithDec']
            hdu.header['CUNIT2'] = 'deg'
            ### Coordinates - Stokes parameters
            hdu.header['CTYPE3'] = 'STOKES'
            hdu.header['CRPIX3'] = 1
            hdu.header['CDELT3'] = 1
            hdu.header['CRVAL3'] = 1
            hdu.header['LONPOLE'] = 180.0
            hdu.header['LATPOLE'] = 90.0
            ### LWA1 approximate beam size
            beamSize = 2.2*74e6/header['freq']
            hdu.header['BMAJ'] = beamSize/header['xPixelSize']
            hdu.header['BMIN'] = beamSize/header['xPixelSize']
            hdu.header['BPA'] = 0.0
            ### Frequency
            hdu.header['RESTFREQ'] = header['freq']
            
            ## Write it to disk
            outName = "pasi_%.3fMHz_%s.fits" % (header['freq']/1e6, dateObs.strftime("%Y-%m-%dT%H-%M-%S"))
            hdulist = pyfits.HDUList([hdu,])
            hdulist.writeto(outName, clobber=config['force'])
            
            ## Update the counter
            fitsCounter += 1
            
        ## Done with this collection
        db.close()
        
        ## Report
        print "-> wrote %i FITS files" % fitsCounter


if __name__ == "__main__":
    main(sys.argv[1:])
    
