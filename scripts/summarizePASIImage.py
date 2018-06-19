#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import getopt

from lsl.common.mcs import mjdmpm2datetime

from lsl_toolkits.PasiImage import PasiImageDB


def usage(exitCode=None):
    print """summarizePASIImage.py - Print metadata about a PASI .pims file

Usage:  summarizePASIImage.py [OPTIONS] file [file [...]]

Options:
-h, --help              Display this help information
"""
    
    if exitCode is not None:
        sys.exit(exitCode)
    else:
        return True


def parseOptions(args):
    # Build up the configuration
    config = {}
    
    # Read in and process the command line flags
    try:
        opts, args = getopt.getopt(args, "h", ["help",])
    except getopt.GetoptError, err:
        # Print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage(exitCode=2)
        
    # Work through opts
    for opt, value in opts:
        if opt in ('-h', '--help'):
            usage(exitCode=0)
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
            
        ## Report - overall
        print "Filename: %s" % os.path.basename(filename)
        print "  Correlator: %s" % db.header.corrVersion
        print "  Imager: %s" % db.header.imagerVersion
        print "  Station: %s" % db.header.station
        print "  Stokes Parameters: %s" % db.header.stokesParams
        print "  Image Size: %i by %i with %.3f deg/px" % (db.header.xSize, db.header.ySize, db.header.xPixelSize)
        print "  Number of Integrations: %i" % db.nIntegrations
        
        ## Report - first image
        db.seek(0)
        hdr, data, spc = db.readImage()
        mjd = int(hdr.startTime)
        mpm = int((hdr.startTime - mjd)*86400*1000.0)
        tStart = mjdmpm2datetime(mjd, mpm)
        print "    First Image:"
        print "      Start Time: %s" % tStart.strftime("%Y/%m/%d %H:%M:%S.%f")
        print "      Integration Time: %.3f s" % (hdr.intLen*86400.0,)
        print "      Tuning: %.3f MHz" % (hdr.freq/1e6,)
        print "      Bandwidth: %.3f kHz" % (hdr.bandwidth/1e3,)
        
        ## Report - last image
        db.seek(db.nIntegrations-1)
        hdr, data, spc = db.readImage()
        mjd = int(hdr.startTime)
        mpm = int((hdr.startTime - mjd)*86400*1000.0)
        tStart = mjdmpm2datetime(mjd, mpm)
        print "    Last Image:"
        print "      Start Time: %s" % tStart.strftime("%Y/%m/%d %H:%M:%S.%f")
        print "      Integration Time: %.3f s" % (hdr.intLen*86400.0,)
        print "      Tuning: %.3f MHz" % (hdr.freq/1e6,)
        print "      Bandwidth: %.3f kHz" % (hdr.bandwidth/1e3,)
        
        ## Done
        print " "
        db.close()


if __name__ == "__main__":
    main(sys.argv[1:])
    
    
