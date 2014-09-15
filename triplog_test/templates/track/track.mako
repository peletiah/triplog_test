<%inherit file="site.mako" />

<div id="map" class="map">
  <div id="popup" class="ol-popup">
      <a href="#" id="popup-closer" class="ol-popup-closer"></a>
      <div id="popup-content"></div>
  </div>
</div>


<script type="text/javascript">

// STYLE
// --------------------------------------------
      var styleBike = new ol.style.Style({
                stroke: new ol.style.Stroke({
                  color: 'rgba(255,0,0,0.6)',
                  width: 4
                })
              })

      var styleMotor = new ol.style.Style({
                stroke: new ol.style.Stroke({
                  color: 'rgba(0,0,0,0.6)',
                  width: 4
                })
              })

      var styleRectangle = new ol.style.Style({
                stroke: new ol.style.Stroke({
                  color: 'rgba(0,192,0,0.8)',
                  width: 2
                })
              })




      var styleMouseOver = new ol.style.Style({
                  stroke: new ol.style.Stroke({
                    color: 'rgba(30,107,148,0.7)',
                    width: 6
                  })
                });

      var styleClick = new ol.style.Style({
                  stroke: new ol.style.Stroke({
                    color: 'rgba(30,107,148,0.7',
                    pointRadius: 8,
                    width: 6
                  })
                });


      var getStyle = function(feature, resolution) {
          if (feature.get('mode') === 'bicycle') {
            return [styleBike]
          } else {
            return [styleMotor]
          };
          }


// OVERLAYS
// --------------------------------------------

var container = document.getElementById('popup');
var content = document.getElementById('popup-content');
var closer = document.getElementById('popup-closer');

/**
 * Add a click handler to hide the popup.
 * @return {boolean} Don't follow the href.
 */
closer.onclick = function() {
  container.style.display = 'none';
  closer.blur();
  return false;
};
 
 
/**
 * Create an overlay to anchor the popup to the map.
 */
var overlay = new ol.Overlay({
  element: container
});


// LAYERS
// --------------------------------------------


      var track = new ol.layer.Vector({
        source: new ol.source.GeoJSON({
          projection: 'EPSG:3857',
          //object: '${track_json | n}'
          url: '/track_json',
          }),
        style: getStyle,
        });
     
  
      var bing = new ol.layer.Tile({
              source: new ol.source.BingMaps({
              key: 'AtMGNogEVUyszAs35iHA_9N3Sse3BG9YQfrtZAoom1YZg_WPZzGp8CLWyDfNPAqf',
              imagerySet: 'Road'
            }),
            minResolution: 0,
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



// INTERACTION
// --------------------------------------------

      var selectMouseMove = new ol.interaction.Select({
        style :  styleMouseOver,
        condition: ol.events.condition.mouseMove
      });

      var selectClick = new ol.interaction.Select({
        style :  styleClick,
        condition: ol.events.condition.click,
      });

      var pan = new ol.interaction.DragPan({});

// MAP SETUP
// --------------------------------------------

      var view = new ol.View({
          center: ol.proj.transform([40.9850008,29.0245040], 'EPSG:4326', 'EPSG:3857'),
          zoom: 2
        });

      var map = new ol.Map({
        target: 'map',
        layers: [bing,natural,track],
        view: view,
        overlays: [overlay],
        interactions: ol.interaction.defaults().extend([selectMouseMove, selectClick, pan])
      });
   
    
   
      view.on(['change:resolution','change:center'], function() {
        zoomlevel = view.getZoom();
        extent = view.calculateExtent(map.getSize())
        minxy = ol.proj.transform([extent[0], extent[1]], 'EPSG:3857', 'EPSG:4326')
        maxxy = ol.proj.transform([extent[2], extent[3]], 'EPSG:3857', 'EPSG:4326')
        if (zoomlevel > 8) {
          track.setVisible(false)
        } else if (zoomlevel <= 8) {
          track.setVisible(true)
        };
      });


// ZOOM TO SELECTION AND SHOW POPUP

      var collection = selectClick.getFeatures()
      collection.on('add', function(e) {
        var duration = 2000;
        var start = +new Date();
        var pan = ol.animation.pan({
          duration: duration,
          source: /** @type {ol.Coordinate} */ (view.getCenter()),
          start: start
        });
        var zoom = ol.animation.zoom({
          duration: duration,
          resolution: map.getView().getResolution(),
          start: start,
        });
        map.beforeRender(pan, zoom);
        f_extent = e.element.p.geometry.extent
        console.log(f_extent)
        delta_x = f_extent[2] - f_extent[0]
        delta_y = f_extent[3] - f_extent[1]
        console.log(delta_x, delta_y);
        minxy_l = [f_extent[0], f_extent[1]]
        maxxy_r = [f_extent[2], f_extent[3]];
        minxy_r = [f_extent[0]+delta_x, f_extent[1]]
        maxxy_l = [f_extent[0], f_extent[1]+delta_y]
        console.log(maxxy_r, maxxy_l, minxy_l, minxy_r)
        var rectangle = new ol.layer.Vector ({ 
            source: new ol.source.GeoJSON(
                      /** @type {olx.source.GeoJSONOptions} */ ({
                        object: {
                          'type': 'FeatureCollection',
                          'crs': {
                            'type': 'name',
                            'properties': {
                              'name': 'EPSG:3857'
                            }
                          },
                          'features': [
                            {
                              'type': 'Feature',
                              'geometry': {
                                'type': 'Polygon',
                                'coordinates': [[maxxy_r, maxxy_l, minxy_l, minxy_r]]
                              }
                            }
                          ]
                        }})),
            style: styleRectangle
        });
      
        map.addLayer(rectangle);
        map.getView().fitExtent(e.element.p.geometry.extent, map.getSize());
        var coordinate = ol.proj.transform(e.element.get('center_point'), 'EPSG:4326', 'EPSG:3857');
        overlay.setPosition(coordinate);
        content.innerHTML = '<code> ID: ' + e.element.p.id + '</code><p><code>' + e.element.p.distance + '</code></p>' +
          '<p><code>' + e.element.p.date + '</code></p>';
        container.style.display = 'block';
      });


      track.on('change', function(event) {
        console.log(track.getSource().getState())
        if (track.getSource().getState() == 'ready') {
          var extent = track.getSource().getExtent();
          map.getView().fitExtent(extent, map.getSize());
        };
      });

 

</script>

