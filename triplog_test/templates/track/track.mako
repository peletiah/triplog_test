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
                  color: 'rgba(255,0,0,0.4)',
                  width: 4
                })
              })

      var styleMotor = new ol.style.Style({
                stroke: new ol.style.Stroke({
                  color: 'rgba(0,0,0,0.4)',
                  width: 4
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


 
      var bing = new ol.layer.Tile({
              source: new ol.source.BingMaps({
              key: 'AtMGNogEVUyszAs35iHA_9N3Sse3BG9YQfrtZAoom1YZg_WPZzGp8CLWyDfNPAqf',
              imagerySet: 'Road'
            }),
            minResolution: 0,
            maxResolution: 3000          
          })


        var natural = new ol.layer.Tile({
              source: new ol.source.TileJSON({
                url: 'http://api.tiles.mapbox.com/v3/' +
                    'mapbox.natural-earth-hypso-bathy.jsonp',
                crossOrigin: 'anonymous'
              }),
              minResolution: 3000,
            })

//      var track = new ol.layer.Vector({
//        source: new ol.source.GeoJSON({
//          projection: 'EPSG:3857',
//          object: '${track_json | n}'
//          }),
//        style: getStyle ,
//        });



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


// TESTING ServerVector
// --------------------------------------------



//var extent_old;
//
//      var vectorSource = new ol.source.ServerVector({
//        format: new ol.format.GeoJSON(),
//        loader: function(extent, resolution, projection) {
//          zoomlevel = view.getZoom()
//          extent = view.calculateExtent(map.getSize())
//          if (JSON.stringify(extent) != JSON.stringify(extent_old)) {
//            bottomXY = ol.proj.transform([extent[0], extent[1]], 'EPSG:3857', 'EPSG:4326')
//            topXY = ol.proj.transform([extent[2], extent[3]], 'EPSG:3857', 'EPSG:4326')
//            minx = bottomXY[0]
//            miny = bottomXY[1]
//            maxx = topXY[0]
//            maxy = topXY[1]
//            var url = '/features_in_extent?extent='+maxx+','+maxy+','+minx+','+miny+'&zoomlevel='+zoomlevel
//            console.log(url)
//            $.ajax({
//              url: url,
//              dataType: 'jsonp'
//            });
//          };
//          extent_old = extent;
//        },
//        strategy: ol.loadingstrategy.createTile(new ol.tilegrid.XYZ({
//          maxZoom: 19
//        })),
//        projection: 'EPSG:3857'
//      });
//       
//      var loadFeatures = function(response) {
//        vectorSource.addFeatures(vectorSource.readFeatures(response));
//      };
// 
//      var features = new ol.layer.Vector({
//        source: vectorSource,
//        style: getStyle
//      });


// MAP SETUP
// --------------------------------------------




      var view = new ol.View({
          center: ol.proj.transform([52.0392288, 35.7925984], 'EPSG:4326', 'EPSG:3857'),
          zoom: 3
        });

      var map = new ol.Map({
        target: 'map',
        layers: [bing,natural],
        view: view,
        overlays: [overlay],
        interactions: ol.interaction.defaults().extend([selectMouseMove, selectClick, pan])
      });


// FETCH FEATURES AFTER MAP MOVE
      map.on('moveend', function() {
        zoomlevel = view.getZoom();
        extent = view.calculateExtent(map.getSize())
        bottomXY = [extent[0], extent[1]]
        topXY = [extent[2], extent[3]]
        minx = bottomXY[0]
        miny = bottomXY[1]
        maxx = topXY[0]
        maxy = topXY[1]
        //console.log(maxx,maxy,minx,miny)
        //console.log('POLYGON(('+maxx+' '+maxy+', '+ maxx+' '+miny+', '+minx+' '+miny+', '+minx+' '+maxy+', '+maxx+' '+maxy+'))')
        //console.log(zoomlevel)
        console.log('/features_in_extent?extent='+maxx+','+maxy+','+minx+','+miny+'&zoomlevel='+zoomlevel)
        source = new ol.source.GeoJSON({
            projection: 'EPSG:3857',
            url: '/features_in_extent?extent='+maxx+','+maxy+','+minx+','+miny+'&zoomlevel='+zoomlevel
          })


        
        features = new ol.layer.Vector({
          source: source, 
          style: getStyle,
        });



        map.addLayer(features)

      //features.setVisible(false)
      //if ((zoomlevel > 5) && (zoomlevel <= 10)) {
      //    features.setVisible(true)
      //};


//        zoom_low = 5
//        zoom_medium = 10
//        if (zoomlevel <= zoom_low) {
//          zoomlevel = 'low'
//        } else if ((zoomlevel > zoom_low) && (zoomlevel <= zoom_medium)) {
//          zoomlevel = 'medium'
//        } else if (zoomlevel > zoom_medium) {
//          zoomlevel = 'high'
//        };
//
//      map.getLayers().forEach( function(e) {
//        try {
//          console.log(zoomlevel)
//          e.getSource().getFeatures().forEach( function(p) {
//            console.log(p)
//          })
//        }
//        catch(err) {}
//      });
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
        console.log(e.element.getProperties())
        map.beforeRender(pan, zoom);
        f_extent = e.element.p.geometry.extent
        bottomXY_L = [f_extent[0], f_extent[1]]
        topXY_R = [f_extent[2], f_extent[3]];
        bottomXY_R = [f_extent[2], f_extent[1]]
        topXY_L = [f_extent[0], f_extent[3]]
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



//// zoom map to feature extent after vector has finished loading ('change')
//      track.on('change', function(event) {
//        if (track.getSource().getState() == 'ready') {
//          var extent = track.getSource().getExtent();
//          map.getView().fitExtent(extent, map.getSize());
//        };
//      });

 

</script>

