#!/usr/bin/env python

# Python2 compatibility
from __future__ import print_function, division, absolute_import

import os
import sys
import numpy
import argparse

from lsl.common.mcs import mjdmpm_to_datetime
from lsl.common.stations import lwa1
from lsl.sim import vis as simVis
from lsl.imaging import overlay
from lsl import astro

from lsl_toolkits.PasiImage import PasiImageDB

from matplotlib import pyplot as plt
from matplotlib.ticker import NullFormatter


def main(args):
    # Loop over the input files
    for filename in args.filename:
        ## Is this file valid?
        try:
            db = PasiImageDB(filename, 'r')
        except Exception as e:
            print("ERROR: %s" % str(e))
            continue
            
        ## Setup the array
        if db.header.station == 'LWA1':
            aa = simVis.build_sim_array(lwa1, lwa1.antennas[0::2], numpy.array([38e6,]))
        else:
            aa = None
            
        ## Go!
        for i,(hdr,img,spec) in enumerate(db):
            if args.dataset != 0 and args.dataset != (i+1):
                continue
                
            mjd = int(hdr.startTime)
            mpm = int((hdr.startTime - mjd)*86400*1000.0)
            tStart = mjdmpm_to_datetime(mjd, mpm)
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
                    if not args.no_grid:
                        overlay.graticule_radec(ax, aa)
                    # Source positions
                    overlay.sources(ax, aa, simVis.SOURCES, label=(not args.no_labels))
                    
            fig.suptitle('%.3f MHz @ %s' % (hdr.freq/1e6, tStart.strftime("%Y/%m/%d %H:%M:%S")))
            plt.show()
            
        ## Done
        db.close()


if __name__ == "__main__":
    numpy.seterr(all='ignore')
    parser = argparse.ArgumentParser(
        description='display images in a PASI .pims file',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
    parser.add_argument('filename', type=str, nargs='+',
                        help='filename to display')
    parser.add_argument('-s', '--dataset', type=int, default=0,
                        help='daata set to image (one-based; 0 = all)')
    parser.add_argument('-n', '--no-labels', action='store_true',
                        help='disable source and grid labels')
    parser.add_argument('-g', '--no-grid', action='store_true',
                        help='disable the RA/Dec grid')
    args = parser.parse_args()
    main(args)
    
