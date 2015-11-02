#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Simple tool to convert a single Time Zone boundaries defined in multipolygon tz_world shapefile
(see http://efele.net/maps/tz/world/) to a kml file; mainly for display and verification purposes.
"""
import argparse
import os
import sys

import shapefile

__author__ = 'Andrey Maslyuk'
__license__ = 'MIT'
__version__ = '1.0.0'


def shapefile_tz_to_kml(dbfilebase, tzname, kmlfile, verbose):
    if verbose:
        print('Opening tz_world...')
    db = shapefile.Reader(dbfilebase)

    if verbose:
        print('Searching tz_world...')

    shapes = []
    for idx in range(db.numRecords):
        tzname = db.record(idx)[0]
        if tzname == tzname:
            sh = db.shape(idx)
            if 5 == sh.shapeType:
                shapes.append(sh)
            else:
                if verbose:
                    print('Unknown shape type ' + str(sh.shapeType) + ' at ' + str(idx))

    if 0 == len(shapes):
        print('Time Zone not found: ' + tzname)
        return 2

    if verbose:
        print('Found regions: ' + str(len(shapes)))

    with open(kmlfile, 'w') as kmlfile:
        kmlfile.write('<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Placemark>')

        kmlfile.write('<name>' + tzname + '</name>')
        kmlfile.write('<description>Time zone borders for ' + tzname + ' as retrieved from tz_world</description>')

        for sh in shapes:
            pos = len(sh.points) - 1
            for lim in reversed(sh.parts):
                kmlfile.write('<Polygon><extrude>1</extrude><altitudeMode>relativeToGround</altitudeMode>')
                kmlfile.write('<outerBoundaryIs><LinearRing><coordinates>')
                for p in range(pos, lim, -1):
                    lon = sh.points[p][0]
                    lat = sh.points[p][1]
                    kmlfile.write(str(lon) + ',' + str(lat) + ',0 ')
                kmlfile.write('</coordinates></LinearRing></outerBoundaryIs></Polygon>')
                pos = lim - 1

        kmlfile.write('</Placemark></kml>')

    if verbose:
        print('Done')
    return 0


def main():
    # arguments definition
    argparser = argparse.ArgumentParser(description='Converts a named Time Zone from tz_world multipolygon shapefile ' +
                                                    '(see http://efele.net/maps/tz/world/) to KML format.')
    argparser.add_argument('tz', metavar='name',
                           help='Time Zone to convert (e.g. America/New_York)')
    argparser.add_argument('-db', metavar='directory',
                           help='tz_world database directory, defaults to "tz_world"',
                           default='tz_world')
    argparser.add_argument('-out', metavar='kml_file',
                           help='output kml file path/name; defaults to Time Zone name-derived in current directory',
                           default='auto')
    argparser.add_argument('-v', action='store_true',
                           help='verbose output')
    args = argparser.parse_args()

    # arguments checks
    if not os.path.isdir(args.db):
        print('The tz_world database directory does not exist: ' + args.db)
        sys.exit(1)
    dbfile = os.path.join(args.db, 'tz_world_mp')
    dbfiletest = dbfile + '.shp'
    if not os.path.isfile(dbfiletest):
        print('The tz_world database does not exist: ' + dbfiletest)
        sys.exit(1)

    if args.out == 'auto':
        outfile = args.tz.replace('/', '_') + '.kml'
    else:
        outfile = args.out

    # processing
    try:
        ret = shapefile_tz_to_kml(dbfile, args.tz, outfile, args.v)
        if ret != 0:
            sys.exit(ret)
    except:
        print('Unexpected error: ', sys.exc_info()[0])


if __name__ == '__main__':
    main()
