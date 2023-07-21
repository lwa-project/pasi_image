#!/usr/bin/env python

# Python2 compatibility
from __future__ import print_function, division, absolute_import

import os
import sys
import numpy
from astropy.io import fits as astrofits
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.wcs import WCS
from astropy.time import Time
import argparse
from datetime import datetime, timedelta, timezone

from lsl.common.mcs import mjdmpm_to_datetime

from lsl_toolkits.PasiImage import PasiImageDB

from scipy.interpolate import interp1d
from lsl.common.paths import DATA as dataPath
from lsl.misc import parser as aph
import matplotlib.pyplot as plt


def calcbeamprops(az,alt,header):
    
    # az and alt need to be the same shape as the image we will correct

    freq = header['freq']
    i = 0
    beamDict = numpy.load(os.path.join(dataPath, 'lwa1-dipole-emp.npz'))
    polarpatterns = []
    for beamCoeff in (beamDict['fitX'], beamDict['fitY']):
        alphaE = numpy.polyval(beamCoeff[0,0,:],freq )
        betaE =  numpy.polyval(beamCoeff[0,1,:],freq )
        gammaE = numpy.polyval(beamCoeff[0,2,:],freq )
        deltaE = numpy.polyval(beamCoeff[0,3,:],freq )
        alphaH = numpy.polyval(beamCoeff[1,0,:],freq )
        betaH =  numpy.polyval(beamCoeff[1,1,:],freq )
        gammaH = numpy.polyval(beamCoeff[1,2,:],freq )
        deltaH = numpy.polyval(beamCoeff[1,3,:],freq )
        corrFnc = None

        def compute_beam_pattern(az, alt, corr=corrFnc):
            zaR = numpy.pi/2 - alt*numpy.pi / 180.0 
            azR = az*numpy.pi / 180.0
            
            c = 1.0
            if corrFnc is not None:
                c = corrFnc(alt*numpy.pi / 180.0)
                c = numpy.where(numpy.isfinite(c), c, 1.0)
                
            pE = (1-(2*zaR/numpy.pi)**alphaE)*numpy.cos(zaR)**betaE + gammaE*(2*zaR/numpy.pi)*numpy.cos(zaR)**deltaE
            pH = (1-(2*zaR/numpy.pi)**alphaH)*numpy.cos(zaR)**betaH + gammaH*(2*zaR/numpy.pi)*numpy.cos(zaR)**deltaH

            return c*numpy.sqrt((pE*numpy.cos(azR))**2 + (pH*numpy.sin(azR))**2)
        
        # Calculate the beam
        pattern = compute_beam_pattern(az, alt)
        polarpatterns.append(pattern)

            
        i += 1
    beamDict.close()
    return polarpatterns[0], polarpatterns[1]
    
    

        

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
            dateObs = mjdmpm_to_datetime(mjd, mpm)
            dateEnd = dateObs + timedelta(seconds=int(tInt), microseconds=int((tInt-int(tInt))*1000000))
            if args.verbose:
                print("    start time: %s" % dateObs)
                print("    end time: %s" % dateEnd)
                print("    integration time: %.3f s" % tInt)
                print("    frequency: %.3f MHz" % header['freq'])

            
            if args.pbcorr:
                crval1 = header['zenithRA']*numpy.pi/180
                crpix1 = imSize/2 + 1 + 0.5 * ((imSize+1)%2) 
                cdelt1 = numpy.pi*(-360.0/(2*sRad)/numpy.pi)/180
                crval2 = header['zenithDec']*numpy.pi/180
                crpix2 = imSize/2 + 1 + 0.5 * ((imSize+1)%2) 
                cdelt2 = numpy.pi*(360.0/(2*sRad)/numpy.pi)/180
                ra = ((crval1 + (x - crpix1)*cdelt1/(numpy.cos(crval2)))*180/numpy.pi) 
                dec = (crval2 + cdelt2*(y-crpix2))*180/numpy.pi
                # Make dec go between -90 and 90
                # Adjust RA accordingly
                decover = dec>90
                decdiff = dec[decover] - 90
                dec[decover] = dec[decover] - decdiff
                ra[decover] +=180
                decoverneg = dec<-90
                decdiffneg = dec[decoverneg] + 90
                dec[decoverneg] = dec[decoverneg] + decdiffneg
                ra[decoverneg] +=180
                ra = ra % 360
                
                sc = SkyCoord(ra,dec,unit='deg')
                lwa1 = EarthLocation.of_site('lwa1')  
                time = Time(dateObs.strftime("%Y-%m-%dT%H:%M:%S"),format="isot")
                aa = AltAz(location=lwa1, obstime=time)
                myaltaz = sc.transform_to(aa)
                alt = myaltaz.alt.deg
                az = myaltaz.az.deg
                # Keep alt between 0 and 90, adjust az accordingly
                negalt = alt < 0
                alt[negalt] += 90
                az[negalt] + 180

                XX,YY = calcbeamprops(az,alt,header)
                # Correct stokes I only, need XY and YX for U and V, could do Q here
                data[0]/=((XX+YY)/2)
            
                
            ## Create the FITS HDU and fill in the header information
            hdu = astrofits.PrimaryHDU(data=data)
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
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='be verbose during the conversion')
    parser.add_argument('-p', '--pbcorr', action='store_true',
                        help='perform primary beam correction on stokes I only')
    args = parser.parse_args()
    main(args)
    
