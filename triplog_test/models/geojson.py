import json

import logging
log = logging.getLogger(__name__)


class GeoJSON():
    def __init__(self, geotype, coordinates, center, zoomlevel):
        self.geotype = geotype
        self.coordinates = coordinates
        self.center = center
        self.zoomlevel = zoomlevel

    def jsonify_feature(self):
        feature = (dict(
            type='Feature',
            geometry=dict(
                type=self.geotype,
                coordinates=self.coordinates
            ),
            properties=dict(
                zoomlevel = self.zoomlevel,
                center = self.center
            ),
            ))
        return feature
