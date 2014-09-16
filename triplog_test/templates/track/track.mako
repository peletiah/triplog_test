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

      var styleExtentMarker = new ol.style.Style({
                stroke: new ol.style.Stroke({
                  color: 'rgba(0,192,0,0.8)',
                  width: 2
                }),
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
   
    
// Act on Change of ZOOMLEVEL and/or PAN
      view.on(['change:resolution','change:center'], function() {
        zoomlevel = view.getZoom();
        extent = view.calculateExtent(map.getSize())
        bottomXY = ol.proj.transform([extent[0], extent[1]], 'EPSG:3857', 'EPSG:4326')
        topXY = ol.proj.transform([extent[2], extent[3]], 'EPSG:3857', 'EPSG:4326')
        minx = bottomXY[0]
        miny = bottomXY[1]
        maxx = topXY[0]
        maxy = topXY[1]
        console.log('POLYGON(('+maxx+' '+maxy+', '+ maxx+' '+miny+', '+minx+' '+miny+', '+minx+' '+maxy+', '+maxx+' '+maxy+'))')
        if (zoomlevel > 8) {
          //track.setVisible(false)
          track.setVisible(true)
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
        bottomXY_L = [f_extent[0], f_extent[1]]
        topXY_R = [f_extent[2], f_extent[3]];
        bottomXY_R = [f_extent[2], f_extent[1]]
        topXY_L = [f_extent[0], f_extent[3]]
        extentMarker = new ol.source.GeoJSON(
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
                                'coordinates': [[topXY_R, topXY_L, bottomXY_L, bottomXY_R]]
                              }
                            }
                          ]
                        }})),
     
        extentMarker.addFeature(new ol.Feature(new ol.geom.Circle(bottomXY_L, 1000)));
        var extentMarkerVector = new ol.layer.Vector({
          source: extentMarker,
          style: styleExtentMarker
        });    
        map.addLayer(extentMarkerVector);
        map.getView().fitExtent(e.element.p.geometry.extent, map.getSize());
        var coordinate = ol.proj.transform(e.element.get('center_point'), 'EPSG:4326', 'EPSG:3857');
        overlay.setPosition(coordinate);
        content.innerHTML = '<code> ID: ' + e.element.p.id + '</code>' +
                            '<p><code>' + e.element.p.distance + '</code></p>' +
                            '<p><code>' + e.element.get('center_point') + '</code></p>' + 
                            '<p><code> topXY_R: ' + ol.proj.transform(topXY_R, 'EPSG:3857', 'EPSG:4326') + '</code></p>' + 
                            '<p><code> topXY_L: ' + ol.proj.transform(topXY_L, 'EPSG:3857', 'EPSG:4326') + '</code></p>' + 
                            '<p><code> bottomXY_R: ' + ol.proj.transform(bottomXY_R, 'EPSG:3857', 'EPSG:4326') + '</code></p>' + 
                            '<p><code> bottomXY_L: ' + ol.proj.transform(bottomXY_L, 'EPSG:3857', 'EPSG:4326') + '</code></p>'; 
                            '<p><code> bottomXY_L: ' + ol.proj.transform(bottomXY_L, 'EPSG:3857', 'EPSG:4326') + '</code></p>'; 
        container.style.display = 'block';
      });



// zoom map to feature extent after vector has finished loading ('change')
      track.on('change', function(event) {
        if (track.getSource().getState() == 'ready') {
          var extent = track.getSource().getExtent();
          map.getView().fitExtent(extent, map.getSize());
        };
      });

 

</script>

