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
                    color: 'rgba(30,107,148,0.7)',
                    pointRadius: 8,
                    width: 6
                  })
                });

      var styleRed = new ol.style.Style({
            stroke: new ol.style.Stroke({
                  color: 'rgba(255,0,0,0.4)',
                  pointRadius: 4,
                  width: 6
                  })
                });

      var styleBlue = new ol.style.Style({
            stroke: new ol.style.Stroke({
                  color: 'rgba(0,0,255,0.4)',
                  pointRadius: 4,
                  width: 6
                  })
                });

      var styleGreen = new ol.style.Style({
            stroke: new ol.style.Stroke({
                  color: 'rgba(0,255,0,0.4)',
                  pointRadius: 4,
                  width: 6
                  })
                });




      var getStyle = function(level) {
          //return [styleRed]
          if (level == 'tour') {
            return [styleBlue]
          } else if (level == 'etappe') {
            return [styleGreen]
          } else if (level == 'track') {
            return [styleRed]
          } else {
            return [styleMoto]
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


// MAP SETUP
// --------------------------------------------



      var view = new ol.View({
          center: [5719495.643944736, 4335033.122424604],
          zoom: 8
        });

      var map = new ol.Map({
        target: 'map',
        layers: [osm,natural],
        view: view,
        overlays: [overlay],
        interactions: ol.interaction.defaults().extend([selectMouseMove, selectClick, pan])
      });



var fetchFeatures = function() {
        bbox = view.calculateExtent(map.getSize())
        call = $.ajax({
          url: '/features_in_bbox?bbox='+bbox
        })
        return call
        
    };



var tracks = {}
tracks['tour'] = {}
tracks['etappe'] = {}
tracks['track'] = {}

var createLayer = function(feature) {
  level = feature.getProperties().level
  featureId = feature.getProperties().id
  var source = new ol.source.Vector({
      features: [feature],
      projection: 'EPSG:3857'
  })
  if (typeof tracks[level][featureId] === 'undefined') { //don't create duplicate layers
    tracks[level][featureId] = new ol.layer.Vector({
        source: source,
        style: getStyle(level)
      })
    console.log(typeof tracks[level][featureId])
    map.addLayer(tracks[level][featureId])
  }
}

    

// FETCH FEATURES AFTER MAP MOVE
    map.on('moveend', function() {
          console.log('map moveend')
          fetchFeatures().done( function(response) {
            var format = new ol.format.GeoJSON()
            relatives = response[0]
            features = format.readFeatures(response[1])
            if (features.length > 0) {
              features.forEach( function(feature) {
                feature.getGeometry().transform('EPSG:4326', 'EPSG:3857')
                createLayer(feature)
              })
            }
            levels = new Array('tour','etappe','track')
            for (var i in levels) {
              level = levels[i]
              if (typeof relatives[level] !== 'undefined') {
                relatives[level].forEach( function(id) {
                  if (typeof tracks[level][id] !== 'undefined') {
                    //console.log('hiding '+level+','+id)
                    tracks[level][id].setVisible(false)
                  }
                })
              }
            }
            relatives['self'].forEach( function(r) {
              id = r['id']
              level = r['level']
              tracks[level][id].setVisible(true)
            })
          })
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
        properties = e.element.getProperties()
        //console.log(e)
        map.beforeRender(pan, zoom);
        f_extent = e.element.p.geometry.extent
        bottomXY_L = [f_extent[0], f_extent[1]]
        topXY_R = [f_extent[2], f_extent[3]];
        bottomXY_R = [f_extent[2], f_extent[1]]
        topXY_L = [f_extent[0], f_extent[3]]
        map.getView().fitExtent(e.element.p.geometry.extent, map.getSize());
        properties = e.element.getProperties()
        center = properties.center
        var coord = ol.proj.transform([center[0], center[1]], 'EPSG:4326', 'EPSG:3857')
        overlay.setPosition(coord);
        $.ajax({
                    url: '/map_popup/'+properties.level+'?id='+properties.id
                  }).done( function(response) { 
                    console.log(response)
                    content.innerHTML = response 
                  })
        //content.innerHTML = '<p><code>' + properties.level + ' ' + properties.id + '</code></p>' 
        container.style.display = 'block';
      });



//// zoom map to feature extent after vector has finished loading ('change')
//      track.on('change', function(event) {
//        if (track.getSource().getState() == 'ready') {
//          var extent = track.getSource().getExtent();
//          map.getView().fitExtent(extent, map.getSize());
//        };
//      });

