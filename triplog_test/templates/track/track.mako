<%inherit file="site.mako" />
<div id="map" class="map">
  <div id="popup" class="ol-popup">
      <a href="#" id="popup-closer" class="ol-popup-closer"></a>
      <div id="popup-content"></div>
  </div>
</div>
<script type="text/javascript">

// STYLE
      var styleBike = new ol.style.Style({
                stroke: new ol.style.Stroke({
                  color: 'red',
                  opacity: 0.7,
                  width: 4
                })
              })


      var styleMouseOver = new ol.style.Style({
                  stroke: new ol.style.Stroke({
                    color: '#1E6B94',
                    opacity : 0.2,
                    pointRadius: 8,
                    width: 6
                  })
                });

      var styleMouseOver = new ol.style.Style({
                  stroke: new ol.style.Stroke({
                    color: '#1E6B94',
                    opacity : 0.2,
                    pointRadius: 8,
                    width: 6
                  })
                });

      var styleClick = new ol.style.Style({
                  stroke: new ol.style.Stroke({
                    color: '#1E6B94',
                    opacity : 0.7,
                    pointRadius: 8,
                    width: 6
                  })
                });


// ELEMENTS

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



// SELECT EVENTS

      var selectMouseMove = new ol.interaction.Select({
        style :  styleMouseOver,
        condition: ol.events.condition.mouseMove
      });

      var selectClick = new ol.interaction.Select({
        style :  styleClick,
        condition: ol.events.condition.click,
        add: overlay
      });

      var pan = new ol.interaction.DragPan({
      });


      var getStyle = function(feature, resolution) {
          style = [styleBike] 
          return style
          }

      var track = new ol.layer.Vector({
        source: new ol.source.GeoJSON({
          projection: 'EPSG:3857',
          object: '${track_json | n}'
          }),
        style: getStyle ,
        });
     
  
      var tiles = new ol.layer.Tile({
              source: new ol.source.BingMaps({
              key: 'AtMGNogEVUyszAs35iHA_9N3Sse3BG9YQfrtZAoom1YZg_WPZzGp8CLWyDfNPAqf',
              imagerySet: 'Road'
            })
          })

      var map = new ol.Map({
        target: 'map',
        layers: [tiles,track],
        view: new ol.View({
          center: ol.proj.transform([37.41, 8.82], 'EPSG:4326', 'EPSG:3857'),
          zoom: 4
        }),
        overlays: [overlay],
      });
  
    map.addInteraction(selectMouseMove);
    map.addInteraction(selectClick);
    map.addInteraction(pan);


    map.on('click', function(evt) {
      var coordinate = evt.coordinate;
      var hdms = ol.coordinate.toStringHDMS(ol.proj.transform(
          coordinate, 'EPSG:3857', 'EPSG:4326'));
 
      overlay.setPosition(coordinate);
      content.innerHTML = '<p>You clicked here:</p><code>' + hdms +
          '</code>';
      container.style.display = 'block';
    });

     

</script>

