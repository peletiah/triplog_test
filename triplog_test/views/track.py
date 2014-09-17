from pyramid.response import Response
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound,
    )
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from triplog_test.models import (
    DBSession,
    Track,
    Trackpoint
    )

from triplog_test.helpers import (
    gpxtools
)

from sqlalchemy import and_,select,func

from datetime import timedelta
import time,datetime,json,os,uuid

from decimal import Decimal, ROUND_HALF_UP

import logging
log = logging.getLogger(__name__)


def generate_json_from_tracks(tracks):
    features=list()
    for row in tracks:
        if row.reduced_trackpoints:
            rounded_distance='<b>distance:</b> %skm<br />' % (str(Decimal(row.distance).quantize(Decimal("0.01"), ROUND_HALF_UP)))
            total_mins = row.timespan.seconds / 60
            mins = total_mins % 60
            hours = total_mins / 60
            timespan = '<b>duration:</b> %sh%smin<br />' % (str(hours),str(mins))
            date=row.start_time.strftime('%B %d, %Y')
            reduced_track = list()
            features.append(
                (dict(
                type='Feature',
                geometry=dict(
                    type="LineString",
                    coordinates=row.reduced_trackpoints
                    ),
                properties=dict(
                    type = 'line',
                    id = row.id,
                    date = date,
                    distance = rounded_distance,
                    timespan = timespan,
                    mode = row.mode_ref.type,
                    center_point = row.reduced_trackpoints[len(row.reduced_trackpoints)/2]
                    ),
                )))
    tracks_json = json.dumps(dict(type='FeatureCollection', features=features))
    return tracks_json


@view_config(route_name='track_json',
)
def track_json(request):
    tracks = DBSession.query(Track).all()
    track_json = Response(generate_json_from_tracks(tracks))
    track_json.content_type = 'application/json'
    return(track_json)



@view_config(route_name='track',
            renderer='track/track.mako',
)
def track_view(request):
    tracks = DBSession.query(Track).all()
    track_json = generate_json_from_tracks(tracks)
    return {
        'track_json': track_json,
    }


@view_config(route_name='features_in_extent')
def features_in_extent(request):
    if request.query_string:
        extent = request.GET.get('extent')
        log.debug(len(extent.split(',')))
        maxx, maxy, minx, miny = extent.split(',')
        log.debug('{0},{1},{2},{3}'.format(maxx, maxy, minx, miny))
        viewport = u'POLYGON(( \
                    {maxx} {maxy}, \
                    {maxx} {miny}, \
                    {minx} {miny}, \
                    {minx} {maxy}, \
                    {maxx} {maxy}))'.format( \
                    maxx=maxx, maxy=maxy, minx=minx, miny=miny)
        viewport = select([func.ST_GeomFromText(viewport, 4326)]).label("viewport")
        tracks_contained = DBSession.query(Track).filter(func.ST_Contains(viewport, Track.extent)).all()
        tracks_overlapping = DBSession.query(Track).filter(func.ST_Overlaps(viewport, Track.extent)).all()
        tracks = tracks_contained + tracks_overlapping
        track_json = Response(generate_json_from_tracks(tracks))
        track_json.content_type = 'application/json'
        return(track_json)
    return Response('OK')

