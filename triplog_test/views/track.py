from pyramid.response import Response
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound,
    )
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from triplog_test.models import (
    DBSession,
    Tour,
    Etappe,
    Track,
    ReducedTrackpoints,
    Trackpoint
    )

from triplog_test.helpers import (
    gpxtools
)

from sqlalchemy import and_,or_,select,func

from datetime import timedelta
import time,datetime,json,os,uuid

from decimal import Decimal, ROUND_HALF_UP

import logging
log = logging.getLogger(__name__)


def generate_json_from_tracks(tracks, epsilon):
    features=list()
    for track in tracks:
        for reduced_trackpoints in track.reduced_trackpoints:
            if reduced_trackpoints.epsilon == epsilon:
                rtp = reduced_trackpoints.reduced_trackpoints
                features.append(
                    (dict(
                        type='Feature',
                        geometry=dict(
                            type="LineString",
                            coordinates=rtp
                            ),
                        properties=dict(
                            type = 'line',
                            id = track.id,
                            mode = track.mode_ref.type,
                            uuid = track.uuid,
                            center_point = rtp[len(rtp)/2]
                            ),
                        ))
                    )
    tracks_json = json.dumps(dict(type='FeatureCollection', features=features))
    return tracks_json

def multilinestring_from_tracks(tracks):
    features=list()
    coordinates = list()
    for track in tracks:
        if track.reduced_trackpoints:
            coordinates.append(track.reduced_trackpoints)
    features.append(
        (dict(
        type='Feature',
        geometry=dict(
            type="MultiLineString",
            coordinates=coordinates
            ),
        )))
    tracks_json = json.dumps(dict(type='FeatureCollection', features=features))
    return tracks_json




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
    if request.query_string:
        maxx, maxy, minx, miny = request.GET.get('extent').split(',')
        if request.POST.get('featureList'):
            feature_uuid_list = request.POST.get('featureList').split(',')
            feature_uuid_list = [item for item in feature_uuid_list if len(item) != 0 ] #weed out empty strings like u''
        else:
            feature_uuid_list = list()
        zoomlevel = int(request.GET.get('zoomlevel'))
        log.debug('FEATUREIDs: {0}, LENGTH: {1}'.format(feature_uuid_list, len(feature_uuid_list)))
        log.debug('{0},{1},{2},{3}'.format(maxx, maxy, minx, miny))
        viewport = u'POLYGON(( \
                    {maxx} {maxy}, \
                    {maxx} {miny}, \
                    {minx} {miny}, \
                    {minx} {maxy}, \
                    {maxx} {maxy}))'.format( \
                    maxx=maxx, maxy=maxy, minx=minx, miny=miny)
        viewport = select([func.ST_GeomFromText(viewport, 4326)]).label("viewport")
        if zoomlevel <= 7:
            epsilon = Decimal('0.005')
        elif zoomlevel > 7 and zoomlevel <= 13:
            epsilon = Decimal('0.0005')
        elif zoomlevel > 13:
            epsilon = Decimal('0.00002')
            log.debug(epsilon)
        
            
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
        track_json = Response(generate_json_from_tracks(tracks, epsilon))
        track_json.content_type = 'application/json'
        return(track_json)
    return Response('OK')

