import json

import logging
log = logging.getLogger(__name__)


class GeoJSON():
    def __init__(self, coordinates, properties, level):
        if level == 'track':
            geotype = 'LineString'
        else:
            geotype = 'MultiLineString'
        self.level = level
        self.geotype = geotype
        self.coordinates = coordinates
        self.properties = properties

    def jsonify_feature(self):
        feature = (dict(
            type='Feature',
            geometry = dict(
                type = self.geotype,
                coordinates = self.coordinates
            ),
            properties = dict(
                    self.properties,
                    level = self.level
                    )
            ))
        return feature
