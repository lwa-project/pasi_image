#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import numpy
import getopt

from lsl.common.mcs import mjdmpm2datetime
from lsl.common.stations import lwa1
from lsl.sim import vis as simVis
from lsl.imaging import overlay
from lsl import astro

from lsl_toolkits.PasiImage import PasiImageDB

from matplotlib import pyplot as plt
from matplotlib.ticker import NullFormatter


def usage(exitCode=None):
    print """imagePASI.py - Display images in a PASI .pims file

Usage:  imagePASI.py [OPTIONS] file [file [...]]

Options:
-h, --help              Display this help information
-s, --dataset           Data set to image (Default = All)
-n, --no-labels         Disable source and grid labels
-g, --no-grid           Disable the RA/Dec grid
"""
    
    if exitCode is not None:
        sys.exit(exitCode)
    else:
        return True


def parseOptions(args):
    # Build up the configuration
    config = {}
    config['dataset'] = 0
    config['label'] = True
    config['grid'] = True
    config['args'] = []
    
    # Read in and process the command line flags
    try:
        opts, args = getopt.getopt(args, "hs:ng", ["help", "dataset=", "no-labels", "no-grid"])
    except getopt.GetoptError, err:
        # Print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage(exitCode=2)
        
    # Work through opts
    for opt, value in opts:
        if opt in ('-h', '--help'):
            usage(exitCode=0)
        elif opt in ('-s', '--dataset'):
            config['dataset'] = int(value)
        elif opt in ('-n', '--no-labels'):
            config['label'] = False
        elif opt in ('-g', '--no-grid'):
            config['grid'] = False
        else:
            assert False
            
    # Add in arguments
    config['args'] = args
    
    # Return configuration
    return config


def main(args):
    config = parseOptions(args)
    filenames = config['args']
    
    # Loop over the input files
    for filename in filenames:
        ## Is this file valid?
        try:
            db = PasiImageDB(filename, 'r')
        except Exception as e:
            print "ERROR: %s" % str(e)
            continue
            
        ## Setup the array
        if db.header.station == 'LWA1':
            aa = simVis.buildSimArray(lwa1, lwa1.getAntennas()[0::2], numpy.array([38e6,]))
        else:
            aa = None
            
        ## Go!
        for i,(hdr,img,spec) in enumerate(db):
            if config['dataset'] != 0 and config['dataset'] != (i+1):
                continue
                
            mjd = int(hdr.startTime)
            mpm = int((hdr.startTime - mjd)*86400*1000.0)
            tStart = mjdmpm2datetime(mjd, mpm)
            if aa is not None:
                aa.set_jultime(hdr.centroidTime + astro.MJD_OFFSET)
                
            stokes = hdr.stokesParams.split(',')
            
            ### Save the image size for later
            imSize = img.shape[-1]
            
            ### Zero outside of the horizon so avoid problems
            pCntr = imSize/2 + 1 + 0.5 * ((imSize+1)%2)
            pScale = hdr['xPixelSize']
            sRad   = 360.0/pScale/numpy.pi / 2
            x = numpy.arange(1, img.shape[-2]+1, dtype=numpy.float32) - pCntr
            y = numpy.arange(1, img.shape[-1]+1, dtype=numpy.float32) - pCntr
            x /= -sRad
            y /= sRad
            x,y = numpy.meshgrid(x,y)
            invalid = numpy.where( (x**2 + y**2) > 1 )
            img[:, invalid[0], invalid[1]] = 0.0
            
            ### Try and set the image scale correctly for the display
            x2 = x - 1 / sRad
            y2 = y - 1 / sRad
            extent = (x2.max(), x2.min(), y.min(), y.max())
            
            ### Loop over Stokes parameters
            fig = plt.figure()
            for j,label in enumerate(stokes):
                ax = fig.add_subplot(2, 2, j+1)
                ax.imshow(img[j,:,:].T, origin='lower', interpolation='nearest', extent=extent)
                ax.set_title(label)
                ax.set_xlim((1,-1))
                ax.set_ylim((-1,1))
                
                ## Turn off tick marks
                ax.xaxis.set_major_formatter( NullFormatter() )
                ax.yaxis.set_major_formatter( NullFormatter() )
                
                ## Is we know where we are, overlay some stuff
                if aa is not None:
                    # Horizon
                    overlay.horizon(ax, aa)
                    # RA/Dec graticle
                    if config['grid']:
                        overlay.graticleRADec(ax, aa)
                    # Source positions
                    overlay.sources(ax, aa, simVis.srcs, label=config['label'])
                    
            fig.suptitle('%.3f MHz @ %s' % (hdr.freq/1e6, tStart.strftime("%Y/%m/%d %H:%M:%S")))
            plt.show()
            
        ## Done
        db.close()


if __name__ == "__main__":
    numpy.seterr(all='ignore')
    main(sys.argv[1:])
    
