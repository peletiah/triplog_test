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
    Image,
    Log
    )

from triplog_test.models.geojson import GeoJSON
from sqlalchemy import and_,or_,select,func

from datetime import timedelta
import time,datetime,json,os,uuid

from decimal import Decimal, ROUND_HALF_UP

from time import sleep

import logging
log = logging.getLogger(__name__)

def convert_to_geojson_featurecollection(tracks):
    features=list()
    for track in tracks:
        reduced_track = list()
        features.append(
            (dict(
            type='Feature',
            geometry=dict(
                type="LineString",
                coordinates=json.loads(track.reduced_trackpoints)
                ),
            properties=dict(
                type = 'line',
                id = track.id,
                ),
            )))
    return features
 
@view_config(route_name='testmap')
def testmap(request):
    maxx, maxy, minx, miny = request.GET.get('bbox').split(',')
 
    #- define viewport for query
 
    viewport = u'POLYGON(( \
                {maxx} {maxy}, \
                {maxx} {miny}, \
                {minx} {miny}, \
                {minx} {maxy}, \
                {maxx} {maxy}))'.format( \
                maxx=maxx, maxy=maxy, minx=minx, miny=miny)
    viewport = select([func.ST_GeomFromText(viewport, 4326)]).label("viewport")
 
    tracks_in_viewport = DBSession.query(Track).filter(or_(
      func.ST_Overlaps(viewport, Track.bbox),
      func.ST_Contains(viewport, Track.bbox)
    )).all()
 
    features = convert_to_geojson_featurecollection(tracks_in_viewport)
    response = Response(json.dumps(dict(type='FeatureCollection', features=features)))
    response.content_type = 'application/json'
    return(response)
