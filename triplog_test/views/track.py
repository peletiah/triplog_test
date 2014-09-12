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

from sqlalchemy import and_

from datetime import timedelta
import time,datetime, json

from decimal import Decimal, ROUND_HALF_UP

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


