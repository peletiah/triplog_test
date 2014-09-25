from lxml import etree
from xml.etree import ElementTree

from datetime import timedelta
import time,datetime

import json,re,uuid

from decimal import Decimal, ROUND_HALF_UP

import triplog_test.helpers.ramerdouglaspeucker as rdp


from triplog_test.models.db_model import (
    Track,
    Trackpoint,
    )


def reduce_trackpoints(trackpoints, factor):
    points = list()
    reduced_trackpoints = list() 
    for pt in trackpoints:
        points.append(rdp.Vec2D( float(pt.longitude) , float(pt.latitude) ))
    line = rdp.Line(points)
    rdp_trkpts_reduced = line.simplify(factor) #simplified douglas peucker line
    for trackpoint in rdp_trkpts_reduced.points:
        reduced_trackpoints.append([trackpoint.coords[0],trackpoint.coords[1]]) #list of simplified trackpoints
    return reduced_trackpoints



def trackpoints_to_geojson(reduced_trkpts):
            json_string=json.dumps(dict(type='Feature',geometry=dict(type='LineString',coordinates=reduced_trkpts)))
            return json_string


def parse_track_description(track_desc):
    #regex match of track description, save values in re-groups
    print track_desc
    metrics=re.compile(r'Total Track Points: (?P<pt_count>\d+). Total time: (?P<h>\d+)h(?P<m>\d+)m(?P<s>\d+)s. Journey: (?P<distance>\d+.\d+)Km').match(track_desc)
    pt_count = int(metrics.group("pt_count")) #number of trackpoints in this track
    hours = int(metrics.group("h"))
    minutes = int(metrics.group("m"))
    seconds = int(metrics.group("s"))
    timespan = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    distance = str(metrics.group("distance"))
    return pt_count, timespan, distance


def parse_trackpoint_xml(trackpoint_xml, gpx_ns, ext_ns):
    latitude = trackpoint_xml.attrib['lat']
    longitude = trackpoint_xml.attrib['lon']

    elevation = trackpoint_xml.find('{%s}ele'% gpx_ns).text
    elevation = int(float(elevation))
    time_str = trackpoint_xml.find('{%s}time'% gpx_ns).text.replace('T',' ')[:-1]
    time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

    temperature=trackpoint_xml.find("{%s}extensions/{%s}TrackPointExtension/{%s}Temperature" % (gpx_ns,ext_ns,ext_ns)).text
    pressure=trackpoint_xml.find("{%s}extensions/{%s}TrackPointExtension/{%s}Pressure" % (gpx_ns,ext_ns,ext_ns)).text

    desc = trackpoint_xml.find('{%s}desc'% gpx_ns).text
    desc_re=re.compile(r'.*Speed=(?P<speed>\d+)Km/h, Course=(?P<course>\d+)deg.').match(desc)
    speed=None
    course=None
    if desc_re:
        speed=desc_re.group("speed")
        course=desc_re.group("course")
    trackpoint = Trackpoint(track_id=None, latitude=latitude, longitude=longitude, altitude=elevation, velocity=speed, temperature=temperature, direction=course, pressure=pressure, timestamp=time, uuid=str(uuid.uuid4())) 
    return trackpoint


def parse_gpx(gpxfile):
    rdp_factor=0.0002
    file = open(gpxfile,'r')
    gpx_ns = "http://www.topografix.com/GPX/1/1"
    ext_ns = "http://gps.wintec.tw/xsd/"
    root = etree.parse(gpxfile).getroot()
    tracks_xml = root.getiterator("{%s}trk"%gpx_ns)
    parsed_tracks = list()

    for track_xml in tracks_xml:

        tracksegments = track_xml.getiterator("{%s}trkseg"%gpx_ns)
        trackpoints=list()

        for tracksegment in tracksegments:
            for trackpoint_xml in tracksegment:
                trackpoint=parse_trackpoint_xml(trackpoint_xml, gpx_ns, ext_ns)
                trackpoints.append(trackpoint) #returns list of trackpoint-objects
            #TODO: And what about the other segments in this track?

        trackpoints.sort(key = lambda trackpoint: trackpoint.timestamp)

        track_desc = track_xml.find('{%s}desc'% gpx_ns).text
        trackpoint_count, timespan, distance = parse_track_description(track_desc)
        print len(trackpoints)
        print distance
        if not distance == '0.000': #TODO DP-calc hangs when there was no movement in the track
            reduced_trkpts=reduce_trackpoints(trackpoints, rdp_factor) #reduces the trackpoints with Douglas Peucker Algorithm
            track = Track(reduced_trackpoints=reduced_trkpts, timespan=timespan, distance=distance, trackpoint_count=trackpoint_count, 
                        start_time=None, end_time=None, uuid=None, mode=1)

            parsed_tracks.append({'track':track,'trackpoints':trackpoints})

    return parsed_tracks

    







