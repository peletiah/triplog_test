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
                  color: 'rgba(255,0,0,0.2)',
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


// MAP SETUP
// --------------------------------------------



      var view = new ol.View({
          center: [5719495.643944736, 4335033.122424604],
          zoom: 8
        });

      var map = new ol.Map({
        target: 'map',
        layers: [bing,natural],
        view: view,
        overlays: [overlay],
        interactions: ol.interaction.defaults().extend([selectMouseMove, selectClick, pan])
      });





var fetchGeojson = function() {
        zoomlevel = view.getZoom();
        extent = view.calculateExtent(map.getSize())
        minx = extent[0]
        miny = extent[1]
        maxx = extent[2]
        maxy = extent[3]
        //console.log(maxx,maxy,minx,miny)
        //console.log('POLYGON(('+maxx+' '+maxy+', '+ maxx+' '+miny+', '+minx+' '+miny+', '+minx+' '+maxy+', '+maxx+' '+maxy+'))')
        console.log('/features_in_extent?extent='+maxx+','+maxy+','+minx+','+miny)
        var featureSource = new ol.source.GeoJSON({
            projection: 'EPSG:3857',
            url: '/features_in_extent?extent='+maxx+','+maxy+','+minx+','+miny
          })

        return featureSource
    };



var createLayer = function(feature) {
  console.log(feature.getProperties())
  var source = new ol.source.Vector({
      features: [feature],
      projection: 'EPSG:3857'
  })
  var tracks = new ol.layer.Vector({
    source: source,
    style: styleBike
  })
  map.addLayer(tracks)
}

    
       


// FETCH FEATURES AFTER MAP MOVE
    map.on('moveend', function() {
          console.log('map moveend')
          map.getLayers().forEach( function(e) {
            try {
              console.log(e.getSource().getFeatures())
            }
            catch(err) {}
          })
          featureSource = fetchGeojson()
          featureSource.on('change', function() {
            if (featureSource.getState() == 'ready') {
              if (featureSource.getFeatures().length > 0) {
                featureSource.getFeatures().forEach( function(f) {
                  createLayer(f)
                })
              }
            }
          });
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
        type = e.element.getProperties().zoomlevel
        map.beforeRender(pan, zoom);
        f_extent = e.element.p.geometry.extent
        bottomXY_L = [f_extent[0], f_extent[1]]
        topXY_R = [f_extent[2], f_extent[3]];
        bottomXY_R = [f_extent[2], f_extent[1]]
        topXY_L = [f_extent[0], f_extent[3]]
        map.getView().fitExtent(e.element.p.geometry.extent, map.getSize());
        center = e.element.getProperties().center
        var coord = ol.proj.transform([center[0], center[1]], 'EPSG:4326', 'EPSG:3857')
        overlay.setPosition(coord);
        content.innerHTML = '<p><code>' + e.element.getProperties().zoomlevel + '</code></p>' 
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

