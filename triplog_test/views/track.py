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
    ReducedTrackpoints,
    Trackpoint
    )

from triplog_test.models.geojson import GeoJSON

from triplog_test.helpers import (
    gpxtools
)


from sqlalchemy import and_,or_,select,func

from datetime import timedelta
import time,datetime,json,os,uuid

from decimal import Decimal, ROUND_HALF_UP

import logging
log = logging.getLogger(__name__)


@view_config(route_name='track_json',
)
def track_json(request):
    tracks = DBSession.query(Track).all()
    track_json = Response(multilinestring_from_tracks(tracks))
    track_json.content_type = 'application/json'
    return(track_json)



@view_config(route_name='track',
        renderer='track/track.mako',
)
def track_view(request):
#tracks = DBSession.query(Track).all()
#track_json = generate_json_from_tracks(tracks)
    return {
    'track_json': 'bla',
    }


@view_config(route_name='features_in_extent')
def features_in_extent(request):
    zoom_low = 7
    zoom_medium = 13
    maxx, maxy, minx, miny = request.GET.get('extent').split(',')
    if request.POST.get('featureList'):
        feature_uuid_list = request.POST.get('featureList').split(',')
        feature_uuid_list = [item for item in feature_uuid_list if len(item) != 0 ] #weed out empty strings like u''
    else:
        feature_uuid_list = list()
    zoomlevel = int(request.GET.get('zoomlevel'))

    viewport = u'POLYGON(( \
                {maxx} {maxy}, \
                {maxx} {miny}, \
                {minx} {miny}, \
                {minx} {maxy}, \
                {maxx} {maxy}))'.format( \
                maxx=maxx, maxy=maxy, minx=minx, miny=miny)
    viewport = select([func.ST_GeomFromText(viewport, 4326)]).label("viewport")


    if zoomlevel <= zoom_low:
        zoom = u'low'
    elif zoomlevel > zoom_low and zoomlevel <= zoom_medium:
        zoom = u'medium'
    elif zoomlevel > zoom_medium:
        zoom = u'high'
    
        
    if len(feature_uuid_list) > 0:
        tracks = DBSession.query(Track).filter(and_( \
                            or_(
                                func.ST_Intersects(viewport, Track.extent), \
                                func.ST_Contains(viewport, Track.extent) \
                            ), \
                            Track.uuid.notin_(feature_uuid_list))).all()
    else:
        tracks = DBSession.query(Track).filter(or_( \
                                func.ST_Intersects(viewport, Track.extent), \
                                func.ST_Contains(viewport, Track.extent) \
                            )).all()
    if zoom == 'medium':
        etappe_list = {}
        log.debug(len(tracks))
        tracks = DBSession.query(Track).filter(Track.etappe.in_([track.etappe for track in tracks])).all() # query for tracks where etappe_id is like etappe-id of tracks in viewport
        for track in tracks: 
            if not track.etappe in etappe_list and track.etappe is not None:
                etappe_list[track.etappe] = [track]
            elif track.etappe is not None:
                etappe_list[track.etappe].append(track)
        features = list()
        for etappe, track_list in etappe_list.items():
            coordinates = list()
            log.debug(etappe)
            log.debug('COORDINATES: {0}, LEN TRACKLIST: {1}'.format(len(coordinates), len(track_list)))
            for track in track_list:
                for reduced_trackpoints in track.reduced_trackpoints:
                    log.debug('ZOOMLEVEL: {0}, {1}'.format(reduced_trackpoints.zoomlevel, zoom))
                    if reduced_trackpoints.zoomlevel == zoom:
                        coordinates.append(reduced_trackpoints.reduced_trackpoints)
            etappe = DBSession.query(Etappe).filter(Etappe.id == etappe).one()
            center = coordinates[len(coordinates)/2][len(coordinates[len(coordinates)/2])/2] #TODO The middle coord-pair of the middle track
            feature = GeoJSON(geotype = 'MultiLineString', coordinates=coordinates, zoomlevel=zoom, uuid=etappe.uuid, center=center)
            feature = feature.jsonify_feature()
            features.append(feature)
        track_json = Response(GeoJSON.jsonify_collection(features))
    track_json.content_type = 'application/json'
    return(track_json)

