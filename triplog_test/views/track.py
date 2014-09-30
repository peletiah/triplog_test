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
    gpxtools,
    maptools
)

from modify_track import generate_json_from_tracks

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
    session = request.session
    if 'features' in session:
        session['features'] = {} #page has been reloaded, so features have to be reloaded too
    if 'counter' in session:
        session['counter'] = 0 #page has been reloaded, so features have to be reloaded too
 
    tour = DBSession.query(Tour).one()
    features = list()
    features.append((dict(type='Feature',
                        geometry=dict(
                            type="MultiLineString",
                            coordinates=json.loads(tour.reduced_trackpoints)
                            ))))
    track_json = json.dumps(dict(type='FeatureCollection', features=features))
    return {
        'track_json': track_json,
    }


@view_config(route_name='features_in_extent')
def features_in_extent(request):
    ## get request variables
    session = request.session
    if 'features' not in session:
        session['features'] = {}

    if 'counter' not in session:
        session['counter'] = 1
        log.debug('not here')
    else:
        log.debug('yess')

    zoomlevel = int(request.GET.get('zoomlevel'))

    #- set zoomlevels
    zoom_low = 5
    zoom_medium = 10
    if zoomlevel <= zoom_low:
        zoomlevel = 'low'
    elif zoomlevel > zoom_low and zoomlevel <= zoom_medium:
        zoomlevel = 'medium'
    elif zoomlevel > zoom_medium:
        zoomlevel = 'high'
    
    zoomlevel = 'low'

    if zoomlevel not in session['features']:
        session['features'][zoomlevel] = []


    maxx, maxy, minx, miny = request.GET.get('extent').split(',')

    #- define viewport for query

    viewport = u'POLYGON(( \
                {maxx} {maxy}, \
                {maxx} {miny}, \
                {minx} {miny}, \
                {minx} {maxy}, \
                {maxx} {maxy}))'.format( \
                maxx=maxx, maxy=maxy, minx=minx, miny=miny)
    viewport = select([func.ST_GeomFromText(viewport, 4326)]).label("viewport")

 
    ## query tracks which are not yet loaded
        
 
    if len(session['features'][zoomlevel]) > 0:
        tracks = DBSession.query(Track).filter(and_( \
                            or_(
                                func.ST_Intersects(viewport, Track.extent), \
                                func.ST_Contains(viewport, Track.extent) \
                            ), \
                            Track.id.notin_(session['features'][zoomlevel]))).all()
    else:
        tracks = DBSession.query(Track).filter(or_( \
                                func.ST_Intersects(viewport, Track.extent), \
                                func.ST_Contains(viewport, Track.extent) \
                            )).all()

    ## get GeoJSON-features depending on zoomlevel
    if tracks:
        features = maptools.get_features(tracks, session, zoomlevel)
    else:
        features = list()
    log.debug(len(features))
    if len(features) > 0:
        session['counter']=session['counter']+1
    log.debug(session['counter'])
    track_json = Response(json.dumps(dict(type='FeatureCollection', features=features)))
    track_json.content_type = 'application/json'
    return(track_json)

