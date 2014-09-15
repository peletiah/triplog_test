from lxml import etree
from xml.etree import ElementTree

from datetime import timedelta
import time,datetime

import json,re,uuid

from decimal import Decimal, ROUND_HALF_UP

import triplog_test.helpers.douglaspeucker as dp


from triplog_test.models import (
    DBSession,
    Track,
    Trackpoint,
    )


def reduce_trackpoints(trackpoints, factor):
    points = list()
    reduced_trackpoints = list() 
    for pt in trackpoints:
        points.append(dp.Vec2D( float(pt.longitude) , float(pt.latitude) ))
    line = dp.Line(points)
    dp_trkpts_reduced = line.simplify(factor) #simplified douglas peucker line
    for trackpoint in dp_trkpts_reduced.points:
        reduced_trackpoints.append([trackpoint.coords[0],trackpoint.coords[1]]) #list of simplified trackpoints
    return reduced_trackpoints



def create_json_for_db(reduced_trkpts):
            json_string=json.dumps(dict(type='Feature',geometry=dict(type='LineString',coordinates=reduced_trkpts)))
            return json_string


def geojson_from_gpx(gpxfile):
    file = open(gpxfile,'r')
    class trkpt:
        def __init__(self, latitude, longitude):
            self.latitude = latitude
            self.longitude = longitude

    trkptlist=list()

    gpx_ns = "http://www.topografix.com/GPX/1/1"

    root = etree.parse(gpxfile).getroot()
    trackSegments = root.getiterator("{%s}trkseg"%gpx_ns)
    for trackSegment in trackSegments:
        for trackPoint in trackSegment:
            lat=trackPoint.attrib['lat']
            lon=trackPoint.attrib['lon']
            new_trkpt=trkpt(lat,lon)
            trkptlist.append(new_trkpt)

    reduced_trkpts=reduce_trackpoints(trkptlist)
    json_string=create_json_for_db(reduced_trkpts)
    file.close()
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
    dp_factor=0.0002
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
            reduced_trkpts=reduce_trackpoints(trackpoints, dp_factor) #reduces the trackpoints with Douglas Peucker Algorithm
            track = Track(reduced_trackpoints=reduced_trkpts, timespan=timespan, distance=distance, trackpoint_count=trackpoint_count, 
                        start_time=None, end_time=None, uuid=None, mode=1)

            parsed_tracks.append({'track':track,'trackpoints':trackpoints})

    return parsed_tracks




def sync_image_trackpoint(image):
    print image.timestamp_original
    camera_offset = timedelta(seconds=0)
    tight_offset = timedelta(seconds=300) # match pic within 600 seconds (10min)
    max_offset = timedelta(seconds=43200) # match pic within 43200 seconds (12h)
    curr_offset =43200 # maximum timestamp-delta of closest trackpoint in seconds
    for offset in (tight_offset, max_offset):
        start_timestamp = image.timestamp_original-camera_offset-offset
        end_timestamp = image.timestamp_original-camera_offset+offset
        trackpoints = Trackpoint.get_trackpoints_by_timerange(start_timestamp, end_timestamp)
        if trackpoints:
            break
    if trackpoints:
        for trackpoint in trackpoints:
            timediff = image.timestamp_original - trackpoint.timestamp
            curr_diff = timediff.days*86400+timediff.seconds #delta between trackpoint and image in seconds
            if abs(curr_diff)<curr_offset: #is absolute value of curr_diff smaller than the last curr_offset-value?
                curr_offset = abs(curr_diff) #set delta to the current closest delta
                curr_trackpoint = trackpoint #set to current closest trackpoint-match
    else:
        curr_trackpoint = None
    return curr_trackpoint

    

    







