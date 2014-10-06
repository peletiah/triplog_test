import json

import logging
log = logging.getLogger(__name__)


class GeoJSON():
    def __init__(self, geotype, coordinates, center, layer):
        self.geotype = geotype
        self.coordinates = coordinates
        self.center = center
        self.layer = layer

    def jsonify_feature(self):
        feature = (dict(
            type='Feature',
            geometry=dict(
                type=self.geotype,
                coordinates=self.coordinates
            ),
            properties=dict(
                layer = self.layer,
                center = self.center
            ),
            ))
        return feature
