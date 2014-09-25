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



def coordinate_string_from_tracks(tracks, coordinates, session, zoom):
    for track in tracks:
        session['features'].append(track.id)
        session['features'] = list(set(session['features'])) #get rid of duplicates
        for reduced_trackpoints in track.reduced_trackpoints:
            if reduced_trackpoints.zoomlevel == zoom:
                coordinates.append(reduced_trackpoints.reduced_trackpoints)
    return coordinates


def get_features(tracks, session, zoom):
    features = list()

    ## ZOOM 'low'
    if zoom == 'low':
        etappe_ids = [track.etappe for track in tracks if track.etappe]
        # only query for tours if the tracks are linked to etappes (track.etappe != NULL)
        if len(etappe_ids) > 0:
            tours = DBSession.query(Tour).filter(Tour.id.in_(etappe_ids)).all()
        else:
            tours = list()
        for tour in tours:
            etappe_list = [etappe.id for etappe in tour.etappes]
            track_groups = group_by_etappe(tracks, etappe_list)
            coordinates = list()
            for etappe, tracks in track_groups.items():
                coordinates = coordinate_string_from_tracks(tracks,coordinates, session, zoom)
            center = coordinates[len(coordinates)/2][len(coordinates[len(coordinates)/2])/2] #TODO The middle coord-pair of the middle track
            feature = GeoJSON(geotype = 'MultiLineString', coordinates=coordinates, zoomlevel=zoom, uuid=tour.uuid, center=center)
            feature = feature.jsonify_feature()
            features.append(feature)


    ## ZOOM 'medium'
    elif zoom == 'medium':

        etappe_list = [track.etappe for track in tracks]
        track_groups = group_by_etappe(tracks, etappe_list)

        # create GeoJSON for each etappe
        for etappe, tracks in track_groups.items():
            coordinates = coordinate_string_from_tracks(tracks, list(), session, zoom)
            etappe = DBSession.query(Etappe).filter(Etappe.id == etappe).one()
            center = coordinates[len(coordinates)/2][len(coordinates[len(coordinates)/2])/2] #TODO The middle coord-pair of the middle track
            feature = GeoJSON(geotype = 'MultiLineString', coordinates=coordinates, zoomlevel=zoom, uuid=etappe.uuid, center=center)
            feature = feature.jsonify_feature()
            features.append(feature)

    ## ZOOM 'high'
    elif zoom == 'high':
        for track in tracks:
            for reduced_trackpoints in track.reduced_trackpoints:
                if reduced_trackpoints.zoomlevel == zoom:
                    coordinates=reduced_trackpoints.reduced_trackpoints
            center = coordinates[len(coordinates)/2]
            feature = GeoJSON(geotype = 'LineString', coordinates=coordinates, zoomlevel=zoom, uuid=track.uuid, center=center)
            feature = feature.jsonify_feature()
            features.append(feature)

    return features

