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

from triplog_test.helpers import (
    gpxtools,
    maptools
)

from .modify_track import generate_json_from_tracks

from sqlalchemy import and_,or_,select,func

from datetime import timedelta
import time,datetime,json,os,uuid

from decimal import Decimal, ROUND_HALF_UP

import logging
log = logging.getLogger(__name__)


@view_config(route_name = 'map_popup_tour',
            renderer='track/popup_tour.mako')
def map_popup_tour(request):
    id = request.GET.get('id')
    tour = DBSession.query(Tour).filter(Tour.id == id).one()

    return {'tour': tour}



@view_config(route_name = 'map_popup_etappe',
            renderer='track/popup_etappe.mako')
def map_popup_etappe(request):
    id = request.GET.get('id')
    etappe = DBSession.query(Etappe).filter(Etappe.id == id).one()

    return {'etappe': etappe}




@view_config(route_name = 'map_popup_track',
            renderer='track/popup_track.mako')
def map_popup_track(request):
    id = request.GET.get('id')
    track = DBSession.query(Track).filter(Track.id == id).one()

    return {'track': track}


@view_config(route_name='track',
        renderer='track/track.mako',
)
def track_view(request):
    session = request.session
    if 'features' in session:
        session['features'] = {} #page has been reloaded, so features have to be reloaded too
 
    #tour = DBSession.query(Tour).one()
    #features = list()
    #features.append((dict(type='Feature',
    #                    geometry=dict(
    #                        type="MultiLineString",
    #                        coordinates=json.loads(tour.reduced_trackpoints)
    #                        ))))
    #track_json = json.dumps(dict(type='FeatureCollection', features=features))
    track_json = ''
    return {
        'track_json': track_json,
    }


@view_config(route_name='features_in_bbox')
def features_in_bbox(request):
    ## get request variables
    session = request.session
    if 'features' not in session:
        session['features'] = {}

    if 'tour' not in session['features']:
        session['features']['tour'] = []
    if 'etappe' not in session['features']:
        session['features']['etappe'] = []
    if 'track' not in session['features']:
        session['features']['track'] = []


    maxx, maxy, minx, miny = request.GET.get('bbox').split(',')

    #- define viewport for query

    viewport = 'POLYGON(( \
                {maxx} {maxy}, \
                {maxx} {miny}, \
                {minx} {miny}, \
                {minx} {maxy}, \
                {maxx} {maxy}))'.format( \
                maxx=maxx, maxy=maxy, minx=minx, miny=miny)
    viewport = select([func.ST_GeomFromText(viewport, 4326)]).label("viewport")

 
    ## query tracks which are not yet loaded
        

    features = list()
    relatives = dict(tour=[], etappe=[],track=[], self=[])

# /// FETCH TOURS IN VIEWPORT ///

    tours_contained_query = DBSession.query(Tour).filter(func.ST_Contains(viewport, Tour.bbox))
    features, relatives, tour_ids, tours = maptools.query_features(
            tours_contained_query, False, features, relatives, session=session['features']['tour'], level='tour'
            ) #Tours contained
    session['features']['tour'] = list(
            set(session['features']['tour'] + tour_ids)
            )


# /// FETCH ETAPPES IN VIEWPORT ///

    tour_partial_query = DBSession.query(Tour).filter(or_(
        func.ST_Overlaps(viewport, Tour.bbox), 
        func.ST_Contains(Tour.bbox, viewport) # !!viewport is INSIDE of Tour.bbox!!
        ))
    features, relatives, tour_id_list, tours = maptools.query_features(
            tour_partial_query, branch=True, features=features, relatives=relatives,  level='tour'
            )
    if tour_id_list:
        # we need to limit the query to elements(etappe) that are children of
        # the parent_partial-query above, otherwise we would return elements 
        # fully contained in the same viewport as it's parent, 
        # displaying both concurrently

        etappes_contained_query = DBSession.query(Etappe).filter(and_(
            or_(
                func.ST_Overlaps(viewport, Etappe.bbox),
                func.ST_Contains(viewport, Etappe.bbox),
                ),
                Etappe.tour.in_(tour_id_list)
            ))
        features, relatives, etappe_ids, etappes = maptools.query_features(
                etappes_contained_query, False, features, relatives, session['features']['etappe'], level='etappe'
                )
        session['features']['etappe'] = list(
                set(session['features']['etappe'] + etappe_ids)
                )

# /// FETCH TRACKS IN VIEWPORT ///
        
        etappes_partial_query = DBSession.query(Etappe).filter(
            #or_(
             #   func.ST_Overlaps(viewport, Etappe.bbox), 
                func.ST_Contains(Etappe.bbox, viewport) # !!viewport is INSIDE of Etappe.bbox
            #)
            )
        features, relatives, etappe_id_list, etappes = maptools.query_features(
                etappes_partial_query, branch=True, features=features, relatives=relatives, level='etappe'
                )
        if etappe_id_list:
            tracks_contained_query = DBSession.query(Track).filter(and_(
                        or_(
                            func.ST_Overlaps(viewport, Track.bbox),
                            func.ST_Contains(viewport, Track.bbox),
                            func.ST_Contains(Track.bbox, viewport)
                            ), 
                        Track.etappe.in_(etappe_id_list)
                        ))   
            features, relatives, track_ids, tracks = maptools.query_features(
                    tracks_contained_query, False, features, relatives, session['features']['track'], level='track'
                    )
            session['features']['track'] = list(
                    set(session['features']['track'] + track_ids)
                    )

    # /// query for the remaining tracks which are not below a tour/etappe
    else:
        tracks_contained_query = DBSession.query(Track).filter(and_(
                    or_(
                        func.ST_Overlaps(viewport, Track.bbox),
                        func.ST_Contains(viewport, Track.bbox),
                        func.ST_Contains(Track.bbox, viewport)
                        ), 
                    Track.etappe == None
                    ))
        features, relatives, track_ids, tracks = maptools.query_features(
                tracks_contained_query, False, features, relatives, session['features']['track'], level='track'
                )
        session['features']['track'] = list(
                set(session['features']['track'] + track_ids)
                )


# /// RETURN FEATURES ///

    #track_json = Response(json.dumps(dict(type='FeatureCollection', features=features, crs=dict(type='name',properties=dict(name='urn:ogc:def:crs:OGC:1.3:CRS84')))))
    log.debug(json.dumps(dict(type='FeatureCollection', features=features)))
    track_json = Response(json.dumps([relatives, dict(type='FeatureCollection', features=features)]))
    track_json.content_type = 'application/json'
    return(track_json)

