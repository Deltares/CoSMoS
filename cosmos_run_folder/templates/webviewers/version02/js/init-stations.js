function thresholdsRUNUP(value) {
  let color = cviColors[4]
  if( value <= 0) {
    color = '#CCFFFF00'
  } else if ( value < 1) {
    color = cviColors[1]
  } else if ( value < 2) {
    color = cviColors[1]
  } else if ( value < 4) {
    color = cviColors[2]
  } else if ( value >= 4) {
    color = cviColors[3]
  }
  return color
}
var tide_gauges
var wave_buoys
var twl_locs

var tidegauge_icon = L.icon({
    iconUrl: 'img/markers/tide_gauge.png',
    iconSize:     [24, 24], // size of the icon
    shadowSize:   [50, 64], // size of the shadow
    iconAnchor:   [12, 12], // point of the icon which will correspond to marker's location
    shadowAnchor: [12, 12],  // the same for the shadow
    popupAnchor:  [12, 12] // point from which the popup should open relative to the iconAnchor
});

var wavebuoy_icon = L.icon({
    iconUrl: 'img/markers/wave_buoy.png',
    iconSize:     [24, 24], // size of the icon
    shadowSize:   [50, 64], // size of the shadow
    iconAnchor:   [12, 12], // point of the icon which will correspond to marker's location
    shadowAnchor: [12, 12],  // the same for the shadow
    popupAnchor:  [12, 12] // point from which the popup should open relative to the iconAnchor
});


function addStations() {

  if (tide_gauges) {
	  // Remove old stations
	  tide_gauges.remove();
  }

  if (stations) {
  tide_gauges = L.geoJson(stations, {onEachFeature: function (feature, layer) {
      var popup = L.popup({"maxWidth": "100%"});
      wlurl = 'html/water_level_timeseries.html?'
      wlurl = wlurl +       `name=${feature.properties.name}`
      wlurl = wlurl + '&' + `longname=${feature.properties.long_name}`
      wlurl = wlurl + '&' + `id=${feature.properties.id}`
      wlurl = wlurl + '&' + `mllw=${feature.properties.mllw}`
      wlurl = wlurl + '&' + `cycle=${currentScenario["cycle"]}`
      wlurl = wlurl + '&' + `duration=${currentScenario["duration"]}`
      wlurl = wlurl + '&' + `obsfile=${feature.properties.obs_file}`
      wlurl = wlurl + '&' + `model_name=${feature.properties.model_name}`
      wlurl = wlurl + '&' + `scenario=${currentScenario["name"]}`
      var content = `<iframe src="${wlurl}" width="730" height="480"></iframe>`
      popup.setContent(content);
      layer.bindPopup(popup,{maxWidth : "auto"});
      },
      pointToLayer: function(feature,latlng){
        return L.marker(latlng,{icon: tidegauge_icon});
      }
    }
  );
  tide_gauges.addTo(map);

  }

}


function addBuoys() {

  if (wave_buoys) {
	  // Remove old buoys
	  wave_buoys.remove();
  }

   if (buoys) {

      wave_buoys = L.geoJson(buoys, {onEachFeature: function (feature, layer) {
            var popup = L.popup({"maxWidth": "100%"});
        wlurl = 'html/wave_timeseries.html?'
        wlurl = wlurl +       `name=${feature.properties.name}`
        wlurl = wlurl + '&' + `longname=${feature.properties.long_name}`
        wlurl = wlurl + '&' + `id=${feature.properties.id}`
//        wlurl = wlurl + '&' + `cycle=${cycle}`
//        wlurl = wlurl + '&' + `duration=${duration}`
        wlurl = wlurl + '&' + `model_name=${feature.properties.model_name}`
        wlurl = wlurl + '&' + `scenario=${currentScenario["name"]}`
        var content = `<iframe src="${wlurl}" width="730" height="480"></iframe>`
        popup.setContent(content);
        layer.bindPopup(popup,{maxWidth : "auto"});
        },

      pointToLayer: function(feature,latlng){
      return L.marker(latlng,{icon: wavebuoy_icon});
      }
    }
    );
    wave_buoys.addTo(map);

   }

}

function addTWLs() {

  if (twl_locs) {
	  // Remove old stations
	  twl_locs.remove();
  }

  if (TWL) {
  twl_locs = L.geoJson(TWL, {onEachFeature: function (feature, layer) {
      var popup = L.popup({"maxWidth": "100%"});
      wlurl = 'html/total_water_level_timeseries.html?'
      wlurl = wlurl +       `name=${feature.properties.name}`
      wlurl = wlurl + '&' + `obsfile=${feature.properties.obs_file}`
      wlurl = wlurl + '&' + `scenario=${currentScenario["name"]}`
      var content = `<iframe src="${wlurl}" width="730" height="480"></iframe>`
      popup.setContent(content);
	  const html = 'Location nr: &#9;' + feature.properties.LocNr + '<br />' +
    'Latitude: &#9;' + feature.properties.Lat + ' [dgr N] &#9;' + '<br />' +
    'Longitude: &#9;' + feature.properties.Lon + ' [dgr E] &#9;' + '<br />' +
    'Wave run-up height: &#9;' + feature.properties.TWL + ' [m above MSL] &#9;' + '<br />'
	  layer.bindTooltip(L.tooltip({ direction: 'top' }).setContent(html));
      layer.bindPopup(popup,{maxWidth : "auto"});
      },
      pointToLayer: function(feature,latlng){
        return new L.CircleMarker(latlng, {
		 radius: 4,
		 fillOpacity: 0.7,
			opacity: 0,
		  color: thresholdsRUNUP(feature.properties.TWL)
		  });

      }
    }
  );
  twl_locs.addTo(map);

  }

}