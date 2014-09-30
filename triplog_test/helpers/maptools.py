from triplog_test.models.db_model import (
    DBSession,
    Track,
    Etappe,
    Tour
)

from triplog_test.models.geojson import (
    GeoJSON
)

import logging
log = logging.getLogger(__name__)



def group_by_etappe(tracks, etappe_list):
        track_groups = {}
        tracks = DBSession.query(Track).filter(Track.etappe.in_(etappe_list)).all() # find additional tracks with the same etappe-ids
        # group by etappe
        for track in tracks:
            if not track.etappe in track_groups and track.etappe is not None:
                track_groups[track.etappe] = [track]
            elif track.etappe is not None:
                track_groups[track.etappe].append(track)
        return track_groups



# return a list of coordinates
def rtp_from_track(track, session, zoomlevel):
    if track.id not in session['features'][zoomlevel]:
        session['features'][zoomlevel].append(track.id)
    for reduced_trackpoints in track.reduced_trackpoints:
        if reduced_trackpoints.zoomlevel == zoomlevel:
            return reduced_trackpoints.reduced_trackpoints
    return list()

def get_features(tracks, session, zoomlevel):
    features = list()

    ## ZOOM 'low'
    if zoomlevel == 'low':
        etappe_ids = [track.etappe for track in tracks if track.etappe]
        # only query for tours if the tracks are linked to etappes (track.etappe != NULL)
        if len(etappe_ids) > 0:
            tours = DBSession.query(Tour).filter(Tour.id.in_(etappe_ids)).all()
        else:
            tours = list()

        for tour in tours:
            tour_rtp = list()
            etappe_list = [etappe.id for etappe in tour.etappes]
            track_groups = group_by_etappe(tracks, etappe_list)

            for etappe, tracks in track_groups.items():
                etappe_rtp = list()
            
                for track in tracks:
                    etappe_rtp = etappe_rtp+rtp_from_track(track, session, zoomlevel)
            
            tour_rtp.append(etappe_rtp)
                
            center = tour_rtp[len(tour_rtp)/2][len(tour_rtp[len(tour_rtp)/2])/2] #TODO The middle coord-pair of the middle track
            feature = GeoJSON(geotype = 'MultiLineString', coordinates=tour_rtp, zoomlevel=zoomlevel, center=center)
            feature = feature.jsonify_feature()
            features.append(feature)


    ## ZOOM 'medium'
    elif zoomlevel == 'medium':

        etappe_list = [track.etappe for track in tracks]
        track_groups = group_by_etappe(tracks, etappe_list)

        # create GeoJSON for each etappe
        for etappe, tracks in track_groups.items():
            etappe_rtp = list()
            for track in tracks:
                etappe_rtp.append(rtp_from_track(track, session, zoomlevel))

            center = etappe_rtp[len(etappe_rtp)/2][len(etappe_rtp[len(etappe_rtp)/2])/2] #TODO The middle coord-pair of the middle track

            feature = GeoJSON(geotype = 'MultiLineString', coordinates=etappe_rtp, zoomlevel=zoomlevel, center=center)
            feature = feature.jsonify_feature()

            features.append(feature)


    ## ZOOM 'high'
    elif zoomlevel == 'high':
        for track in tracks:
            track_rtp = rtp_from_track(track, session, zoomlevel)
            center = track_rtp[len(track_rtp)/2]

            feature = GeoJSON(geotype = 'LineString', coordinates=track_rtp, zoomlevel=zoomlevel, center=center)
            feature = feature.jsonify_feature()
            features.append(feature)

    return features

