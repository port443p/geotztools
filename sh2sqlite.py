#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Simple tool to convert Time Zones boundaries defined in multipolygon tz_world shapefile
(see http://efele.net/maps/tz/world/) to a SQLite database for quicker Location->Time Zone mapping.
Database contains a single table which may be merged to existing database.
"""
import argparse
import os
import sys
import sqlite3
import array

import shapefile

__author__ = 'Andrey Maslyuk'
__license__ = 'MIT'
__version__ = '1.0.0'


COORD_ENCODER = 10000000
COORD_MAX = 200 * COORD_ENCODER
COORD_MIN = -200 * COORD_ENCODER
COORD_DELIMITER = COORD_MAX


def shapefile_to_sqlite(dbfilebase, sqlfile, verbose):

    if verbose:
        print('Opening tz_world...')
    db = shapefile.Reader(dbfilebase)

    if verbose:
        print('processing...')
    conn = sqlite3.connect(sqlfile)

    conn.execute('drop index if exists tztools_tz0_bounds;')
    conn.execute('drop table if exists tztools_tz0;')
    conn.commit()

    conn.execute('create table tztools_tz0(' +
                 'minlon integer, minlat integer, maxlon integer, maxlat integer,' +
                 'name text primary key, region blob);')
    conn.commit()

    # The database is a single table with data; can be safely merged into other DBs.
    # All coordinates in DB are stored as 32-bit ints (degrees * COORD_ENCODER; gives ~1/2" precision).
    # Each row is a complete TZ having name, bounding rectangle and regions.
    # Regions blob is an array of polygons' vertices in form <Longitude, Latitude> stored sequentially;
    #   polygons are separated by a single divider value of COORD_DELIMITER (non-coordinate).

    for idx in range(db.numRecords):
        tzname = db.record(idx)[0]
        sh = db.shape(idx)
        if 5 == sh.shapeType:
            minlon = int(COORD_MAX)
            minlat = int(COORD_MAX)
            maxlon = int(COORD_MIN)
            maxlat = int(COORD_MIN)
            region = array.array('l')

            pos = len(sh.points) - 1
            for lim in reversed(sh.parts):
                for p in range(pos, lim, -1):
                    lon = int(sh.points[p][0] * COORD_ENCODER)
                    lat = int(sh.points[p][1] * COORD_ENCODER)
                    region.append(lon)
                    region.append(lat)

                    if lon < minlon:
                        minlon = lon
                    elif lon > maxlon:
                        maxlon = lon
                    if lat < minlat:
                        minlat = lat
                    elif lat > maxlat:
                        maxlat = lat

                pos = lim - 1
                region.append(int(COORD_DELIMITER))  # insert delimiter
            region.pop()  # remove last delimiter
            conn.execute('insert into tztools_tz0(minlon, minlat, maxlon, maxlat, name, region) values(?,?,?,?,?,?);',
                         [minlon, minlat, maxlon, maxlat, tzname, sqlite3.Binary(region.tobytes())])
        else:
            if verbose:
                print('Unknown shape type ' + str(sh.shapeType) + ' at ' + str(idx))
    conn.commit()

    conn.execute('create index tztools_tz0_bounds on tztools_tz0(minlon, minlat, maxlon, maxlat);')
    conn.commit()
    conn.close()

    if verbose:
        print('Done')
    return 0


def main():
    # arguments definition
    argparser = argparse.ArgumentParser(description='Converts tz_world multipolygon shapefile ' +
                                                    '(see http://efele.net/maps/tz/world/) to indexed SQLite.')
    argparser.add_argument('-db', metavar='directory',
                           help='tz_world database directory, defaults to "tz_world"',
                           default='tz_world')
    argparser.add_argument('-out', metavar='sqlite_file',
                           help='output SQLite DB file path/name; defaults to "tz_world_mp.sqlite" in current directory',
                           default='tz_world_mp.sqlite')
    argparser.add_argument('-m', action='store_true',
                           help='merge into existing SQLite DB; will re-create table "tz"')
    argparser.add_argument('-f', action='store_true',
                           help='overwrite existing SQLite DB')
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

    outdirtest = os.path.dirname(args.out)
    if len(outdirtest) > 0 and not os.path.isdir():
        print('The output directory does not exist: ' + outdirtest)
        sys.exit(1)

    if os.path.isfile(args.out):
        if args.f:
            os.remove(args.out)
        elif not args.m:
            print('The output file exists: ' + args.out)
            sys.exit(3)

    # processing
    try:
        ret = shapefile_to_sqlite(dbfile, args.out, args.v)
        if ret != 0:
            sys.exit(ret)
    except:
        print('Unexpected error: ', sys.exc_info()[0])


if __name__ == '__main__':
    main()
