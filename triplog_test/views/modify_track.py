from pyramid.response import Response
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound,
    )
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from triplog_test.models.db_model import (
    DBSession,
    Tour,
    Etappe,
    Track,
    Trackpoint,
    Mode,
    Image
    )

from triplog_test.helpers import (
    gpxtools
)

from geopy.distance import VincentyDistance

from triplog_test.helpers.ramerdouglaspeucker import reduce_trackpoints

from sqlalchemy import and_,or_, select, func

from datetime import timedelta
import time,datetime,json,os,uuid,numpy

from decimal import Decimal, ROUND_HALF_UP

import logging
log = logging.getLogger(__name__)

def generate_json_from_tracks(tracks):
    features=list()
    for row in tracks:
        if row.reduced_trackpoints:
            for rtp in row.reduced_trackpoints:
                if rtp.zoomlevel == 'low':
                    rounded_distance='<b>distance:</b> %skm<br />' % (str(Decimal(row.distance).quantize(Decimal("0.01"), ROUND_HALF_UP)))
                    total_mins = row.timespan.seconds / 60
                    mins = total_mins % 60
                    hours = total_mins / 60
                    timespan = '<b>duration:</b> %sh%smin<br />' % (str(hours),str(mins))
                    date=row.start_timestamp.strftime('%B %d, %Y')
                    reduced_track = list()
                    features.append(
                        (dict(
                        type='Feature',
                        geometry=dict(
                            type="LineString",
                            coordinates=rtp.reduced_trackpoints
                            ),
                        properties=dict(
                            type = 'line',
                            id = row.id,
                            date = date,
                            distance = rounded_distance,
                            timespan = timespan,
                            mode = row.mode_ref.type,
                            center_point = rtp.reduced_trackpoints[len(rtp.reduced_trackpoints)/2]
                            ),
                        )))
    tracks_json = json.dumps(dict(type='FeatureCollection', features=features))
    return tracks_json

@view_config(route_name='set_mode')
def set_mode(request):
    tracks = DBSession.query(Track).all()
    track_json = generate_json_from_tracks(tracks)
    return {
        'track_json': track_json,
    }


def add_trackpoints_to_db(trackpoints, track):
    for trackpoint in trackpoints:
        trackpoint.track = track

        try:
            DBSession.add(trackpoint)
            DBSession.flush()
            print((trackpoint.timestamp))
        except Exception as e:
            print("\n\nTrackpoint could not be added!\n\n")
            print(e)
            DBSession.rollback()


def add_track_to_db(track_details):
    track = track_details['track']
    trackpoints = track_details['trackpoints']

    print((type(track.reduced_trackpoints)))
    track.uuid = str(uuid.uuid4())
    track.start_timestamp = trackpoints[0].timestamp
    track.end_timestamp = trackpoints[-1].timestamp
    try:
        DBSession.add(track)
        DBSession.flush()
    except Exception as e:
        DBSession.rollback()
        print("\n\nTrack could not be added!\n\n")
        print(e)
        return None
    return track


@view_config(route_name='add_track')
def add_track(request):
    tracks_in_db = list()
    tracks_not_in_db = list()

    for dir,subdir,files in os.walk('/srv/trackdata/WSG2000/collect'):
        for file in files:
            if file.endswith('gpx'):
                print((os.path.join(dir, file)))
                print('\n\n\n\n\n')
                parsed_tracks = gpxtools.parse_gpx(os.path.join(dir,file))
                print('FINISHED parsing GPX\n\n\n')
                for track_details in parsed_tracks:
                    if track_details['trackpoints'][0].timestamp > datetime.datetime.strptime('2014-02-01','%Y-%m-%d'):
                        track = add_track_to_db( track_details)
                        if track:
                            add_trackpoints_to_db( track_details['trackpoints'], track )
                            tracks_in_db.append(os.path.join(dir,file))
                            print('\n\n\n\n\n\n\n')
                            print((track.start_timestamp,track.distance))
                            print('\n\n\n\n\n\n\n')
                        else:
                           tracks_not_in_db.append(os.path.join(dir,file))
    return Response(str(tracks_in_db))

    

# find the bbox for track
@view_config(route_name='track_bbox')
@view_config(route_name='track_bbox:trackid')
def track_bbox(request):
    if request.matchdict:
        #track_id = request.matchdict['trackid']
        #track = Track.get_track_by_id(track_id)
        #etappes = DBSession.query(Etappe).all()
        tours = DBSession.query(Tour).all()
        #tracks = DBSession.query(Track).all()
        for tour in tours:
            trkpts = list()
            for etappe in tour.etappes:
                for track in etappe.tracks:
                    trkpts = list()
                    for pt in track.trackpoints:
                        trkpts.append([pt.latitude,pt.longitude])
                    log.debug(track.id)
                    #maxx,maxy = numpy.max(trkpts, axis=0)
                    #minx,miny = numpy.min(trkpts, axis=0)
                    #bbox = u'POLYGON(( \
                    #                    {maxx} {maxy}, \
                    #                    {maxx} {miny}, \
                    #                    {minx} {miny}, \
                    #                    {minx} {maxy}, \
                    #                    {maxx} {maxy}))'.format( \
                    #                    maxx=maxx, maxy=maxy, minx=minx, miny=miny)
                    #track.bbox = DBSession.query(select([func.ST_AsText(func.ST_Transform(func.ST_GeomFromText(bbox, 4326),3857))]).label("bbox")).one()[0]
            DBSession.flush()
        
    return Response(tour.bbox)



@view_config(route_name='reduce_trackpoints')
def reduce_tracks(request):
    if request.query_string:
        track_id = request.GET.get('trackid')
        epsilon = Decimal(request.GET.get('epsilon'))
        log.debug(epsilon)
        #track = Track.get_track_by_id(track_id)
        #tracks = DBSession.query(Track).filter(Track.id == track_id).all()
        #tracks = DBSession.query(Track).all()
        #etappes = DBSession.query(Etappe).all()
        tours = DBSession.query(Tour).all()
        for tour in tours:
            rtp = list()
            for etappe in tour.etappes:
                for track in etappe.tracks:
                    rtp.append(reduce_trackpoints(track.trackpoints, 0.005))
            tour.reduced_trackpoints = json.dumps(rtp)
            DBSession.flush()
        
    return Response('OK')
 
       
@view_config(route_name = 'get_center')
def get_center(request):
    tours = DBSession.query(Tour).all()
    for tour in tours:
        distance = 0
        #get the total distance of tour
        for etappe in tour.etappes:
            for track in etappe.tracks:
                previous_trkpt = [track.trackpoints[0].latitude,track.trackpoints[0].longitude]
                for trkpt in track.trackpoints:
                    curr_trkpt = [trkpt.latitude,trkpt.longitude]
                    dist = VincentyDistance()
                    distance = distance + dist.measure(previous_trkpt,curr_trkpt)
                    previous_trkpt = curr_trkpt
                #log.debug('old : {0}, new: {1}'.format(old_distance, distance))
        halfway = distance/2
        distance = 0
        #find the trackpoint that is closest to distance/2
        for etappe in tour.etappes:
            for track in etappe.tracks:
                previous_trkpt = [track.trackpoints[0].latitude,track.trackpoints[0].longitude]
                for trkpt in track.trackpoints:
                    curr_trkpt = [trkpt.latitude,trkpt.longitude]
                    dist = VincentyDistance()
                    #log.debug(trkpt.timestamp)
                    if distance <= halfway:
                        distance = distance + dist.measure(previous_trkpt,curr_trkpt)
                        previous_trkpt = curr_trkpt
                        #center=[previous_trkpt[1], previous_trkpt[0]]
                        log.debug(trkpt.latitude)
                        log.debug(previous_trkpt[0])
                        center=trkpt.id
                        #log.debug('{0}, distance: {1}, halfway {2}'.format(distance > halfway, distance,halfway))
        tour.center_id = center
        #log.debug(center)

    etappes = DBSession.query(Etappe).all()
    for etappe in etappes:
        distance = 0
        for track in etappe.tracks:
            previous_trkpt = [track.trackpoints[0].latitude,track.trackpoints[0].longitude]
            for trkpt in track.trackpoints:
                curr_trkpt = [trkpt.latitude,trkpt.longitude]
                dist = VincentyDistance()
                distance = distance + dist.measure(previous_trkpt,curr_trkpt)
                previous_trkpt = curr_trkpt
            #log.debug('old : {0}, new: {1}'.format(old_distance, distance))
        halfway = distance/2
        distance = 0
        for track in etappe.tracks:
            previous_trkpt = [track.trackpoints[0].latitude,track.trackpoints[0].longitude]
            for trkpt in track.trackpoints:
                curr_trkpt = [trkpt.latitude,trkpt.longitude]
                dist = VincentyDistance()
                #log.debug(trkpt.timestamp)
                if distance <= halfway:
                    distance = distance + dist.measure(previous_trkpt,curr_trkpt)
                    previous_trkpt = curr_trkpt
                    #center=[previous_trkpt[1], previous_trkpt[0]]
                    center=trkpt.id
                    log.debug(trkpt.id)
                    #log.debug('{0}, distance: {1}, halfway {2}'.format(distance > halfway, distance,halfway))
        etappe.center_id = center

    tracks = DBSession.query(Track).all()
    for track in tracks:
        distance = 0
        previous_trkpt = [track.trackpoints[0].latitude,track.trackpoints[0].longitude]
        for trkpt in track.trackpoints:
            curr_trkpt = [trkpt.latitude,trkpt.longitude]
            dist = VincentyDistance()
            distance = distance + dist.measure(previous_trkpt,curr_trkpt)
            previous_trkpt = curr_trkpt
        #log.debug('old : {0}, new: {1}'.format(old_distance, distance))
        halfway = distance/2
        distance = 0
        previous_trkpt = [track.trackpoints[0].latitude,track.trackpoints[0].longitude]
        for trkpt in track.trackpoints:
            curr_trkpt = [trkpt.latitude,trkpt.longitude]
            dist = VincentyDistance()
            #log.debug(trkpt.timestamp)
            if distance <= halfway:
                distance = distance + dist.measure(previous_trkpt,curr_trkpt)
                previous_trkpt = curr_trkpt
                center_old=[previous_trkpt[1], previous_trkpt[0]]
                center=trkpt.id
        track.center_id = center

    #DBSession.flush()
        
    return Response(str(center))


@view_config(route_name='link_etappe_image')
def link_etappe_image(request):
    etappes = DBSession.query(Etappe).all()
    for etappe in etappes:
        images = sum([trackpoint.images for trackpoint in sum([track.trackpoints for track in etappe.tracks],[])],[])
        for image in images:
            etappe.images.append(image)
    DBSession.flush()
    return Response('OK')

