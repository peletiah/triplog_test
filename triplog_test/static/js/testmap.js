// STYLING
 
var styleRed = new ol.style.Style({
    stroke: new ol.style.Stroke({
          color: 'rgba(255,0,0,0.5)',
        pointRadius: 8,
        width: 4
        })
});
 
// SETTING UP THE MAP
 
var osm = new ol.layer.Tile({
    source: new ol.source.OSM({
          url: 'http://{a-c}.tile.thunderforest.com/landscape/{z}/{x}/{y}.png'
        }),
      maxResolution: 2000
})

var natural = new ol.layer.Tile({
  source: new ol.source.TileJSON({
    url: 'http://api.tiles.mapbox.com/v3/' +
          'mapbox.natural-earth-hypso-bathy.jsonp',
    crossOrigin: 'anonymous'
    }),
    minResolution: 2000,
  })


var view = new ol.View({
      center: [5719495.643944736, 4335033.122424604],
        zoom: 7
    });
 
var map = new ol.Map({
    target: 'map',
      layers: [osm,natural],
      view: view
});
 
// FETCH AND DRAW THE GEOJSON-DATA
 
var tracks = {}
 
var fetchFeatures = function() {
    bbox = view.calculateExtent(map.getSize())
        call = $.ajax({
              url: '/testmap?bbox='+bbox
            })
      return call
};
 
var createLayer = function(feature) {
    featureId = feature.getProperties().id
        var source = new ol.source.Vector({
              features: [feature],
                projection: 'EPSG:3857'
            })
      if (typeof tracks[featureId] === 'undefined') { //don't create duplicate layers
            tracks[featureId] = new ol.layer.Vector({
                    source: source,
                    style: styleRed
                  })
                map.addLayer(tracks[featureId])
                console.log('New Layer added')
                    }
}
 
map.on('moveend', function() {
    console.log('the map has been moved, fetching GeoJSON for current viewport')
    fetchFeatures().done( function(response) {
          var format = new ol.format.GeoJSON()
          features = format.readFeatures(response)
          if (features.length > 0) {
                  features.forEach( function(feature) {
                            feature.getGeometry().transform('EPSG:4326', 'EPSG:3857') //The GeoJSON from the DB is still in WGS84
                            createLayer(feature)
                          })
                      }
      })
});
