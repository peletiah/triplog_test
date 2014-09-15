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

from sqlalchemy import and_

from datetime import timedelta
import time,datetime,json,os,uuid

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
                    mode = row.mode_ref.type,
                    center_point = row.reduced_trackpoints[len(row.reduced_trackpoints)/2]
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
        trackpoint.track_id = track.id

        try:
            DBSession.add(trackpoint)
            DBSession.flush()
            print trackpoint.timestamp
        except Exception, e:
            print "\n\nTrackpoint could not be added!\n\n"
            print e
            DBSession.rollback()


def add_track_to_db(track_details):
    track = track_details['track']
    trackpoints = track_details['trackpoints']

    print type(track.reduced_trackpoints)
    track.uuid = str(uuid.uuid4())
    track.start_time = trackpoints[0].timestamp
    track.end_time = trackpoints[-1].timestamp
    try:
        DBSession.add(track)
        DBSession.flush()
    except Exception, e:
        DBSession.rollback()
        print "\n\nTrack could not be added!\n\n"
        print e
        return None
    return track


@view_config(route_name='add_track')
def add_track(request):
    tracks_in_db = list()
    tracks_not_in_db = list()

    for dir,subdir,files in os.walk('/srv/trackdata/WSG2000/collect'):
        for file in files:
            if file.endswith('gpx'):
                print os.path.join(dir, file)
                print '\n\n\n\n\n'
                parsed_tracks = gpxtools.parse_gpx(os.path.join(dir,file))
                print 'FINISHED parsing GPX\n\n\n'
                for track_details in parsed_tracks:
                    if track_details['trackpoints'][0].timestamp > datetime.datetime.strptime('2014-02-01','%Y-%m-%d'):
                        track = add_track_to_db( track_details)
                        if track:
                            add_trackpoints_to_db( track_details['trackpoints'], track )
                            tracks_in_db.append(os.path.join(dir,file))
                            print '\n\n\n\n\n\n\n'
                            print track.start_time,track.distance
                            print '\n\n\n\n\n\n\n'
                        else:
                           tracks_not_in_db.append(os.path.join(dir,file))
    return Response(str(tracks_in_db))

    

