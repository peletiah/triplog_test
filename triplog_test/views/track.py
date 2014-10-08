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
    #tracks = DBSession.query(Track).all()
    #track_json = Response(multilinestring_from_tracks(tracks))
    #track_json.content_type = 'application/json'
    tour = DBSession.query(Tour).one()
    features = list()
    features.append((dict(type='Feature',
                        geometry=dict(
                            type="MultiLineString",
                            coordinates=json.loads(tour.reduced_trackpoints)
                            ))))                    
    track_json = Response(json.dumps(dict(type='FeatureCollection', features=features)))
    track_json.content_type = 'application/json'
    return track_json


@view_config(route_name='track',
        renderer='track/track.mako',
)
def track_view(request):
    session = request.session
    if 'features' in session:
        session['features'] = {} #page has been reloaded, so features have to be reloaded too
    if 'counter' in session:
        session['counter'] = 0 #page has been reloaded, so features have to be reloaded too
 
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


@view_config(route_name='features_in_extent')
def features_in_extent(request):
    ## get request variables
    session = request.session
    if 'features' not in session:
        session['features'] = {}

    if 'counter' not in session:
        session['counter'] = 1

#    #- set zoomlevels
#    zoom_low = 5
#    zoom_medium = 10
#    if zoomlevel <= zoom_low:
#        zoomlevel = 'low'
#    elif zoomlevel > zoom_low and zoomlevel <= zoom_medium:
#        zoomlevel = 'medium'
#    elif zoomlevel > zoom_medium:
#        zoomlevel = 'high'
    
    if 'tour' not in session['features']:
        session['features']['tour'] = []
    if 'etappe' not in session['features']:
        session['features']['etappe'] = []
    if 'track' not in session['features']:
        session['features']['track'] = []




    maxx, maxy, minx, miny = request.GET.get('extent').split(',')

    #- define viewport for query

    viewport = u'POLYGON(( \
                {maxx} {maxy}, \
                {maxx} {miny}, \
                {minx} {miny}, \
                {minx} {maxy}, \
                {maxx} {maxy}))'.format( \
                maxx=maxx, maxy=maxy, minx=minx, miny=miny)
#    log.debug(viewport)
    viewport = select([func.ST_GeomFromText(viewport, 4326)]).label("viewport")

 
    ## query tracks which are not yet loaded
        
 
#    if len(session['features'][zoomlevel]) > 0:
#        tracks = DBSession.query(Track).filter(and_( \
#                            or_(
#                                func.ST_Intersects(viewport, Track.extent), \
#                                func.ST_Contains(viewport, Track.extent) \
#                            ), \
#                            Track.id.notin_(session['features'][zoomlevel]))).all()
#    else:
#        tracks = DBSession.query(Track).filter(or_( \
#                                func.ST_Intersects(viewport, Track.extent), \
#                                func.ST_Contains(viewport, Track.extent) \
#                            )).all()
#


#    q_tours_contained = DBSession.query(Tour).filter(func.ST_Contains(viewport, Tour.extent))
#    q_tours_intersect = DBSession.query(Tour).filter(func.ST_Intersects(viewport, Tour.extent))
#    ## get GeoJSON-features depending on zoomlevel
#    features = list()
#    if q_tours_contained.count() > 0:
#        for tour in q_tours_contained.all():
#            log.debug('Tour contained')
#            feature = GeoJSON(geotype = 'MultiLineString', coordinates=json.loads(tour.reduced_trackpoints), zoomlevel='low', center='72.9211072, 33.7250752')
#            feature = feature.jsonify_feature()
#            features.append(feature)
#    if q_tours_intersect.count() > 0:
#        log.debug('Tour intersecting')
#        for tour in q_tours_intersect.all():
#            q_etappes_contained = DBSession.query(Etappe).filter(and_(func.ST_Contains(viewport, Etappe.extent), Etappe.tour == tour.id))
#            q_etappes_intersect = DBSession.query(Etappe).filter(and_(func.ST_Intersects(viewport, Etappe.extent), Etappe.tour == tour.id))
#            log.debug(q_etappes_intersect.count() > 0)
#            if q_etappes_contained.count() > 0:
#                log.debug('Etappe contained')
#                for etappe in q_etappes_contained.all():
#                    feature = GeoJSON(geotype = 'MultiLineString', coordinates=json.loads(etappe.reduced_trackpoints), zoomlevel='medium', center='72.9211072, 33.7250752')
#                    feature = feature.jsonify_feature()
#                    features.append(feature)
#            if q_etappes_intersect.count() > 0:
#                log.debug('Etappe intersecting')
#                for etappe in q_etappes_intersect.all():
#                    q_tracks = DBSession.query(Track).filter(and_(
#                                or_(
#                                    func.ST_Intersects(viewport, Track.extent),
#                                    func.ST_Contains(viewport, Track.extent)
#                                ), Track.etappe == etappe.id
#                             ))
#                    if q_tracks.count() > 0:
#                        log.debug('Tracks found')
#                        for track in q_tracks.all():
#                            feature = GeoJSON(geotype = 'LineString', coordinates=json.loads(track.reduced_trackpoints), zoomlevel='high', center='72.9211072, 33.7250752')
#                            feature = feature.jsonify_feature()
#                            features.append(feature)
#    else:
#        features = list()


    features = list()
    tours_contained_query = DBSession.query(Tour).filter(func.ST_Contains(viewport, Tour.extent))
    features, tour_ids, tours = maptools.query_features(tours_contained_query, False, features, session=session['features']['tour'], type='tour') #Tours contained
    session['features']['tour'] = list(
                                        set(session['features']['tour'] + tour_ids)
                                    )



    tour_overlap_query = DBSession.query(Tour).filter(or_(func.ST_Overlaps(viewport, Tour.extent), func.ST_Contains(Tour.extent, viewport)))
    features, tour_id_list, tours = maptools.query_features(tour_overlap_query, branch=True, features=features, type='tour')
    if tour_id_list:
        for tour in tours:
            etappes_contained_query = DBSession.query(Etappe).filter(and_(or_(func.ST_Overlaps(viewport, Etappe.extent), func.ST_Contains(viewport, Etappe.extent)), Etappe.tour.in_(tour_id_list)))
            features, etappe_ids, etappes = maptools.query_features(etappes_contained_query, False, features, session['features']['etappe'], type='etappe') #Etappes contained
            session['features']['etappe'] = list(
                                                set(session['features']['etappe'] + etappe_ids)
                                            )
    #        etappes_intersect_query = DBSession.query(Etappe).filter(and_(
    #                                                                func.ST_Intersects(viewport, Etappe.extent), 
    #                                                                Etappe.tour == tour.id
    #                                                                ))
    #        features, etappe_id_list, etappes = maptools.query_features(etappes_intersect_query, branch=True, features=features, type='etappe')
    #        session['features']['etappe'] = session['features']['etappe'] + etappe_ids
    #        log.debug(session['features']['etappe'])
    #        if tour_id_list:
    #            log.debug('Etappe intersects')
    #            for etappe in etappes:
    #                tracks_query = DBSession.query(Track).filter(and_(
    #                            or_(
    #                                func.ST_Contains(viewport, Track.extent),
    #                                func.ST_Intersects(viewport, Track.extent)
    #                            ), 
    #                            Track.etappe == etappe.id
    #                         ))        
    #                features, track_ids, tracks = maptools.query_features(tracks_query, False, features, type='track')
    #                session['features']['track'] = session['features']['track'] + track_ids
    #    
    #elif len(features) == 0:
    #    features = list()
    #log.debug(len(features))
    if len(features) > 0:
        session['counter']=session['counter']+1
    #log.debug(session['counter'])
    #track_json = Response(json.dumps(dict(type='FeatureCollection', features=features, crs=dict(type='name',properties=dict(name='urn:ogc:def:crs:OGC:1.3:CRS84')))))
    track_json = Response(json.dumps(dict(type='FeatureCollection', features=features)))
    track_json.content_type = 'application/json'
    return(track_json)

