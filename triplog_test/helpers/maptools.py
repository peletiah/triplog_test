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


# Returns JSON-Features(features), related elements below or above(relatives),
# element_ids(element_id_list) and DB-rows(elements) depending on input
#
# If branch is "True", we are not interested in JSON-features or the current session, but need
# element_id_list to query for the elements children later
# If branch is "False", we return JSON-features to display them on the map. We only return
# features of elements which are not in the session-list (B/c then they already exist on the map)

def query_features(query, branch, features=None, relatives=None, session=list(), level=None):
    if query.count() > 0 and branch == False:
        relatives = dict(tour=[], etappe=[],track=[], self=[])
        element_id_list=list()
        elements = query.all()
        for element in elements:
            element_id_list.append(element.id)

            properties = element.reprGeoJSON()

            if element.id not in session:
                feature = GeoJSON(coordinates=json.loads(element.reduced_trackpoints), properties=properties)
                feature = feature.jsonify_feature()
                features.append(feature)

            grandparent = properties['grandparent']
            parent = properties['parent']
            children = properties['children']
            grandchildren = properties['grandchildren']

            if grandparent['id_list']:
                level = grandparent['level']
                relatives[level] = list(set(relatives[level]+grandparent['id_list']))

            if parent['id_list']:
                level = parent['level']
                relatives[level] = list(set(relatives[level]+parent['id_list']))

            if children['id_list']:
                level = children['level']
                relatives[level] = list(set(relatives[level]+children['id_list']))

            if grandchildren['id_list']:
                level = grandchildren['level']
                relatives[level] = list(set(relatives[level]+grandchildren['id_list']))

            relatives['self'].append(dict(id=properties['id'], level=properties['level']))

        return features, relatives, element_id_list, elements


    if query.count() > 0 and branch == True:
        element_id_list=list()
        elements = query.all()

        for element in elements:
            element_id_list.append(element.id)

        return features, relatives, element_id_list, elements

    else:
        return features, relatives, list(), list()
