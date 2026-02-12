#!/usr/bin/env python3

import os
import sys
import numpy as np
from astropy.io import fits as astrofits
import argparse
from datetime import datetime, timedelta

from lsl.common.mcs import mjdmpm_to_datetime
from lsl.common.paths import DATA as dataPath
from lsl.common.stations import lwa1, lwasv, lwana
from lsl.sim.beam import beam_response

from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.wcs import WCS as AstroWCS
from astropy.wcs.utils import pixel_to_skycoord
from astropy.time import Time
from astropy.io import fits as astrofits

from lsl_toolkits.PasiImage import PasiImageDB

def pbcorr(header,imSize,pScale,station):
    sRad   = 360.0/pScale/np.pi / 2
    w = AstroWCS(naxis=2)
    w.wcs.crpix = [(imSize + 1)/2.0,
                   (imSize + 1)/2.0]
    # 130 degrees is what is visible to the dipoles
    w.wcs.cdelt = np.array([-130/imSize,
                             130/imSize]) 
    w.wcs.crval = [header['zenithRA'],
                   header['zenithDec']]
    w.wcs.ctype = ["RA---SIN",
                   "DEC--SIN"]
    x = np.arange(imSize) - 0.5
    y = np.arange(imSize) - 0.5
    x,y = np.meshgrid(x,y)
    maskpix  = ((x-imSize/2.0)**2 + (y-imSize/2.0)**2) > ((0.95*sRad)**2)
    x[maskpix] = imSize/2
    y[maskpix] = imSize/2
    sc = pixel_to_skycoord(x,y,wcs=w,mode='wcs')
    # Need date and location for converting to altaz
    mjd = int(header['startTime'])
    mpm = int((header['startTime'] - mjd)*86400.0*1000.0)
    tInt = header['intLen']*86400.0
    dateObs = mjdmpm_to_datetime(mjd, mpm)
    time = Time(dateObs.strftime("%Y-%m-%dT%H:%M:%S"),format="isot")
    if station == 'LWASV':
        aa = AltAz(location=lwasv.earth_location, obstime=time)
    elif station == 'LWA1':
        aa = AltAz(location=lwa1.earth_location, obstime=time)
    elif station == 'LWANA':
        aa = AltAz(location=lwana.earth_location, obstime=time)
    else:
        print(station,"unrecognized")
    myaltaz = sc.transform_to(aa)
    alt = myaltaz.alt.deg
    az = myaltaz.az.deg
    # Keep alt between 0 and 90, adjust az accordingly
    negalt = alt < 0
    alt[negalt] += 90
    az[negalt] + 180
    freq = header['freq']
    XX = beam_response('empirical', 'XX', az, alt, frequency=freq)
    YY = beam_response('empirical', 'YY', az, alt, frequency=freq)
    return XX,YY

def main(args):
    # Loop over input .pims files
    for filename in args.filename:
        print("Working on '%s'..." % os.path.basename(filename))
        
        ## Open the image database
        try:
            db = PasiImageDB(filename, mode='r')
        except Exception as e:
            print("ERROR: %s" % str(e))
            continue
            
        ##  Loop over the images contained in it
        fitsCounter = 0
        for i,(header,data,spec) in enumerate(db):
            if args.verbose:
                print("  working on integration #%i" % (i+1))
                
            ## Reverse the axis order so we can get it right in the FITS file
            data = np.transpose(data, [0,2,1])*1.0
            
            ## Save the image size for later
            imSize = data.shape[-1]
            
            ## Zero outside of the horizon so avoid problems
            pScale = header['xPixelSize']
            sRad   = 360.0/pScale/np.pi / 2
            x = np.arange(data.shape[-2]) - 0.5
            y = np.arange(data.shape[-1]) - 0.5
            x,y = np.meshgrid(x,y)
            invalid = np.where( ((x-imSize/2.0)**2 + (y-imSize/2.0)**2) > (sRad**2) )
            data[:, invalid[0], invalid[1]] = 0.0
            ext = imSize/(2*sRad)
            if args.pbcorr:
                XX,YY = pbcorr(header, imSize, db.header['xPixelSize'],db.header['station'])
                data[0,:,:]/=((XX+YY)/2)
             
            
            ## Convert the start MJD into a datetime instance and then use 
            ## that to come up with a stop time
            mjd = int(header['startTime'])
            mpm = int((header['startTime'] - mjd)*86400.0*1000.0)
            tInt = header['intLen']*86400.0
            dateObs = mjdmpm_to_datetime(mjd, mpm)
            dateEnd = dateObs + timedelta(seconds=int(tInt), microseconds=int((tInt-int(tInt))*1000000))
            if args.verbose:
                print("    start time: %s" % dateObs)
                print("    end time: %s" % dateEnd)
                print("    integration time: %.3f s" % tInt)
                print("    frequency: %.3f MHz" % header['freq'])
                
            ## Create the FITS HDU and fill in the header information
            hdu = astrofits.PrimaryHDU(data=data)
            hdu.header['TELESCOP'] = 'LWA1'
            ### Date and time
            hdu.header['DATE-OBS'] = dateObs.strftime("%Y-%m-%dT%H:%M:%S")
            hdu.header['END_UTC'] = dateEnd.strftime("%Y-%m-%dT%H:%M:%S")
            hdu.header['EXPTIME'] = tInt
            ### Coordinates - sky
            hdu.header['CTYPE1'] = 'RA---SIN'
            hdu.header['CRPIX1'] = imSize/2 + 0.5 * ((imSize+1)%2)
            hdu.header['CDELT1'] = -360.0/(2*sRad)/np.pi
            hdu.header['CRVAL1'] = header['zenithRA']
            hdu.header['CUNIT1'] = 'deg'
            hdu.header['CTYPE2'] = 'DEC--SIN'
            hdu.header['CRPIX2'] = imSize/2 + 0.5 * ((imSize+1)%2)
            hdu.header['CDELT2'] = 360.0/(2*sRad)/np.pi
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
            hdulist = astrofits.HDUList([hdu,])
            hdulist.writeto(outName, overwrite=args.force)
            
            ## Update the counter
            fitsCounter += 1
            
        ## Done with this collection
        db.close()
        
        ## Report
        print("-> wrote %i FITS files" % fitsCounter)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='convert the images contained in one or more .pims files into FITS images',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
    parser.add_argument('filename', type=str, nargs='+',
                        help='filename to convert')
    parser.add_argument('-f', '--force', action='store_true',
                        help='force overwriting of FITS files')
    parser.add_argument('-p', '--pbcorr', action='store_true',
                        help='PB correct stokes I')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='be verbose during the conversion')
    args = parser.parse_args()
    main(args)
