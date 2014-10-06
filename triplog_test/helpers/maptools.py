from triplog_test.models.db_model import (
    DBSession,
    Track,
    Etappe,
    Tour
)

from triplog_test.models.geojson import (
    GeoJSON
)

import json

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



# Returns JSON-Features(features), element_ids(element_id_list) and DB-rows(elements) depending on input
# If branch is "True", we are not interested in JSON-features or the current session, but need
# element_id_list to query for the elements children later
# If branch is "False", we return JSON-features to display them on the map. We only return
# features of elements which are not in the session-list (B/c they already exist on the map)

def query_features(query, branch, geotype=None, features=None, session=list(), type=None):
    if query.count() > 0 and branch == False:
        element_id_list=list()
        elements = query.all()

        for element in elements:
            element_id_list.append(element.id)
            #log.debug(session)

            if element.id not in session:
                #log.debug('{0},{1},{2}'.format(geotype,element.reduced_trackpoints,element.center))
                feature = GeoJSON(geotype = geotype, coordinates=json.loads(element.reduced_trackpoints), zoomlevel=type+' '+str(element.id), center=element.center)
                feature = feature.jsonify_feature()
                features.append(feature)

        return features, element_id_list, elements


    if query.count() > 0 and branch == True:
        element_id_list=list()
        elements = query.all()

        for element in elements:
            element_id_list.append(element.id)

        return features, element_id_list, elements

    else:
        return features, list(), list()
