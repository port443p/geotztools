#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Simple tool to convert a single Time Zone boundaries from OpenStreetMap (online) to a kml file;
mainly for display and verification purposes.
Tool uses Overpass API (http://wiki.openstreetmap.org/wiki/Overpass_API) off overpass-api.de site.
"""
import argparse
from datetime import datetime
import json
import urllib.request
import sys

__author__ = 'Andrey Maslyuk'
__license__ = 'MIT'
__version__ = '1.0.0'


class Location:
    def __init__(self, longitude, latitude):
        self.longitude = longitude
        self.latitude = latitude


def osm_tz_to_kml(tzname, opapitimeout, kmlfile, verbose):
    url = 'http://overpass-api.de/api/interpreter?data=[out:json]' +\
          '[timeout:{0}];' +\
          '(relation[%22timezone%22=%22{1}%22];)' +\
          ';out%20body;%3E;out%20skel%20qt;'
    url = url.format(opapitimeout, tzname)

    if verbose:
        print('Querying OpenStreetMap...')
    now = datetime.utcnow()
    raw = urllib.request.urlopen(url).read()
    if verbose:
        print('processing...')
    parsed = json.loads(raw.decode(encoding='UTF-8'), encoding='UTF-8')

    nodes = {}
    for e in parsed['elements']:
        if e['type'] != 'node':
            continue
        nodes[e['id']] = Location(e['lon'], e['lat'])

    if 0 == len(nodes):
        print('Time Zone not found: ' + tzname)
        return 2

    ways = {}
    for e in parsed['elements']:
        if e['type'] != 'way':
            continue
        ns = []
        for nid in e['nodes']:
            ns.append(nodes[nid])
        ways[e['id']] = ns

    if verbose:
        print('Found regions: ' + str(len(ways)))

    with open(kmlfile, 'w') as kmlFile:
        kmlFile.write('<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Placemark>')

        kmlFile.write('<name>' + tzname + '</name>')
        kmlFile.write('<description>Time zone borders for ' + tzname +
                      ' as retrieved from OpenStreetMap on ' + now.isoformat() +
                      'Z</description>')

        for w in ways.values():
            kmlFile.write('<Polygon><extrude>1</extrude><altitudeMode>relativeToGround</altitudeMode>')
            kmlFile.write('<outerBoundaryIs><LinearRing><coordinates>')
            for p in w:
                kmlFile.write(str(p.longitude) + ',' + str(p.latitude) + ',0 ')
            kmlFile.write('</coordinates></LinearRing></outerBoundaryIs></Polygon>')

        kmlFile.write('</Placemark></kml>')

    if verbose:
        print('Done')
    return 0


def main():
    # arguments definition
    argparser = argparse.ArgumentParser(description='Converts a named Time Zone from OpenStreetMap ' +
                                                    '(using Overpass API) to KML format.')
    argparser.add_argument('tz', metavar='name',
                           help='Time Zone to convert (e.g. America/New_York)')
    argparser.add_argument('-out', metavar='kml_file',
                           help='output kml file path/name; defaults to Time Zone name-derived in current directory',
                           default='auto')
    argparser.add_argument('-v', action='store_true',
                           help='verbose output')
    args = argparser.parse_args()

    # arguments checks
    if args.out == 'auto':
        outfile = args.tz.replace('/', '_') + '.kml'
    else:
        outfile = args.out

    # processing
    try:
        ret = osm_tz_to_kml(args.tz, 25, outfile, args.v)
        if ret != 0:
            sys.exit(ret)
    except:
        print('Unexpected error: ', sys.exc_info()[0])


if __name__ == '__main__':
    main()
