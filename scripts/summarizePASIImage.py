#!/usr/bin/env python

# Python2 compatibility
from __future__ import print_function, division, absolute_import

import os
import sys
import argparse

from lsl.common.mcs import mjdmpm_to_datetime

from lsl_toolkits.PasiImage import PasiImageDB


def main(args):
    # Loop over the input files
    for filename in args.filename:
        ## Is this file valid?
        try:
            db = PasiImageDB(filename, 'r')
        except Exception as e:
            print("ERROR: %s" % str(e))
            continue
            
        ## Report - overall
        print("Filename: %s" % os.path.basename(filename))
        print("  Correlator: %s" % db.header.corrVersion)
        print("  Imager: %s" % db.header.imagerVersion)
        print("  Station: %s" % db.header.station)
        print("  Stokes Parameters: %s" % db.header.stokesParams)
        print("  Image Size: %i by %i with %.3f deg/px" % (db.header.xSize, db.header.ySize, db.header.xPixelSize))
        print("  Number of Integrations: %i" % db.nIntegrations)
        
        ## Report - first image
        db.seek(0)
        hdr, data, spc = db.readImage()
        mjd = int(hdr.startTime)
        mpm = int((hdr.startTime - mjd)*86400*1000.0)
        tStart = mjdmpm_to_datetime(mjd, mpm)
        print("    First Image:")
        print("      Start Time: %s" % tStart.strftime("%Y/%m/%d %H:%M:%S.%f"))
        print("      Integration Time: %.3f s" % (hdr.intLen*86400.0,))
        print("      Tuning: %.3f MHz" % (hdr.freq/1e6,))
        print("      Bandwidth: %.3f kHz" % (hdr.bandwidth/1e3,))
        
        ## Report - last image
        db.seek(db.nIntegrations-1)
        hdr, data, spc = db.readImage()
        mjd = int(hdr.startTime)
        mpm = int((hdr.startTime - mjd)*86400*1000.0)
        tStart = mjdmpm_to_datetime(mjd, mpm)
        print("    Last Image:")
        print("      Start Time: %s" % tStart.strftime("%Y/%m/%d %H:%M:%S.%f"))
        print("      Integration Time: %.3f s" % (hdr.intLen*86400.0,))
        print("      Tuning: %.3f MHz" % (hdr.freq/1e6,))
        print("      Bandwidth: %.3f kHz" % (hdr.bandwidth/1e3,))
        
        ## Done
        print(" ")
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='print metadata about a PASI .pims file',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
    parser.add_argument('filename', type=str, nargs='+',
                        help='filename to read')
    args = parser.parse_args()
    main(args)
    
