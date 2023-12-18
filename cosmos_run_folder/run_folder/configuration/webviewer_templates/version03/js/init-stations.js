var tide_gauges
var wave_buoys
var xbeach_markers

var tidegauge_icon = L.icon({
    iconUrl: 'img/markers/tide_gauge.png',
    iconSize:     [16, 16], // size of the icon
    shadowSize:   [36, 42], // size of the shadow
    iconAnchor:   [8, 8], // point of the icon which will correspond to marker's location
    shadowAnchor: [8, 8],  // the same for the shadow
    popupAnchor:  [8, 8] // point from which the popup should open relative to the iconAnchor
});

var wavebuoy_icon = L.icon({
    iconUrl: 'img/markers/wave_buoy.png',
    iconSize:     [16, 16], // size of the icon
    shadowSize:   [36, 42], // size of the shadow
    iconAnchor:   [8, 8], // point of the icon which will correspond to marker's location
    shadowAnchor: [8, 8],  // the same for the shadow
    popupAnchor:  [8, 8] // point from which the popup should open relative to the iconAnchor
});

var xbeach_icon = L.icon({
    iconUrl: 'img/markers/erosion_marker_rw.png',
    iconSize:     [24, 24], // size of the icon
    shadowSize:   [54, 63], // size of the shadow
    iconAnchor:   [12, 12], // point of the icon which will correspond to marker's location
    shadowAnchor: [12, 12],  // the same for the shadow
    popupAnchor:  [12, 12] // point from which the popup should open relative to the iconAnchor
});

var ts_icon = L.icon({
    iconUrl: 'img/markers/Tropical_storm_icon_c2.png',
    iconSize:     [16, 32], // size of the icon
    shadowSize:   [36, 84], // size of the shadow
    iconAnchor:   [ 8, 16], // point of the icon which will correspond to marker's location
    shadowAnchor: [ 8, 16],  // the same for the shadow
    popupAnchor:  [ 8, 16] // point from which the popup should open relative to the iconAnchor
});

var c1_icon = L.icon({
    iconUrl: 'img/markers/Category_1_hurricane_icon_c2.png',
    iconSize:     [16, 32], // size of the icon
    shadowSize:   [36, 84], // size of the shadow
    iconAnchor:   [ 8, 16], // point of the icon which will correspond to marker's location
    shadowAnchor: [ 8, 16],  // the same for the shadow
    popupAnchor:  [ 8, 16] // point from which the popup should open relative to the iconAnchor
});

var c2_icon = L.icon({
    iconUrl: 'img/markers/Category_2_hurricane_icon_c2.png',
    iconSize:     [16, 32], // size of the icon
    shadowSize:   [36, 84], // size of the shadow
    iconAnchor:   [ 8, 16], // point of the icon which will correspond to marker's location
    shadowAnchor: [ 8, 16],  // the same for the shadow
    popupAnchor:  [ 8, 16] // point from which the popup should open relative to the iconAnchor
});

var c3_icon = L.icon({
    iconUrl: 'img/markers/Category_3_hurricane_icon_c2.png',
    iconSize:     [16, 32], // size of the icon
    shadowSize:   [36, 84], // size of the shadow
    iconAnchor:   [ 8, 16], // point of the icon which will correspond to marker's location
    shadowAnchor: [ 8, 16],  // the same for the shadow
    popupAnchor:  [ 8, 16] // point from which the popup should open relative to the iconAnchor
});

var c4_icon = L.icon({
    iconUrl: 'img/markers/Category_4_hurricane_icon_c2.png',
    iconSize:     [16, 32], // size of the icon
    shadowSize:   [36, 84], // size of the shadow
    iconAnchor:   [ 8, 16], // point of the icon which will correspond to marker's location
    shadowAnchor: [ 8, 16],  // the same for the shadow
    popupAnchor:  [ 8, 16] // point from which the popup should open relative to the iconAnchor
});

var c5_icon = L.icon({
    iconUrl: 'img/markers/Category_5_hurricane_icon_c2.png',
    iconSize:     [16, 32], // size of the icon
    shadowSize:   [36, 84], // size of the shadow
    iconAnchor:   [ 8, 16], // point of the icon which will correspond to marker's location
    shadowAnchor: [ 8, 16],  // the same for the shadow
    popupAnchor:  [ 8, 16] // point from which the popup should open relative to the iconAnchor
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
      wlurl = wlurl + '&' + `obs_file=${feature.properties.obs_file}`
	  wlurl = wlurl + '&' + `obs_folder=${feature.properties.obs_folder}`
      wlurl = wlurl + '&' + `model_name=${feature.properties.model_name}`
      wlurl = wlurl + '&' + `scenario=${currentScenario["name"]}`
      var content = `<iframe src="${wlurl}" width="730" height="500"></iframe>`
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
		wlurl = wlurl + '&' + `cycle=${currentScenario["cycle"]}`
		wlurl = wlurl + '&' + `duration=${currentScenario["duration"]}`
        wlurl = wlurl + '&' + `model_name=${feature.properties.model_name}`
        wlurl = wlurl + '&' + `scenario=${currentScenario["name"]}`
        wlurl = wlurl + '&' + `model_name=${feature.properties.model_name}`
		wlurl = wlurl + '&' + `obs_file=${feature.properties.obs_file}`
		wlurl = wlurl + '&' + `obs_folder=${feature.properties.obs_folder}`
        var content = `<iframe src="${wlurl}" width="730" height="500"></iframe>`
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

function addXBeachMarkers() {

  if (xbeach_markers) {
	  // Remove old xbeach_markers
	  xbeach_markers.remove();
  }
   if (xb_markers) {

      xbeach_markers = L.geoJson(xb_markers, {onEachFeature: function (feature, layer) {
		const html = 'Model : &#9;' + feature.properties.long_name + '<br />'
		  layer.bindTooltip(L.tooltip({ direction: 'top' }).setContent(html));
		  layer.bindPopup(html);
      },
      pointToLayer: function(feature,latlng){
      return L.marker(latlng,{icon: xbeach_icon});
      }
    }
    );
    xbeach_markers.addTo(map);

   }

}

function addCycloneTrack() {

if (cyclone_track) {
    // Remove old cyclone_track
    cyclone_track.remove();
}

if (track_data) {
    cyclone_track = L.geoJson(track_data, {onEachFeature: function (feature, layer) {
        if ('lon' in feature.properties) {
		const html = 'Time: &#9;' + feature.properties.time + '<br />' +
			'Category: &#9;' + feature.properties.category + ' &#9;' + '<br />' +
			'Latitude: &#9;' + feature.properties.lat.toFixed(1) + ' &#9;' + '<br />' +
			'Longitude: &#9;' + feature.properties.lon.toFixed(1) + ' &#9;' + '<br />' +
			'Vmax: &#9;' + feature.properties.vmax.toFixed(0) + ' knots &#9;' + '<br />' +
			'Pressure: &#9;' + (0.01*feature.properties.pc).toFixed(0) + ' mbar &#9;' + '<br />'

		  layer.bindTooltip(L.tooltip({ direction: 'top' }).setContent(html));
		  layer.bindPopup(html);
	  }

        },
        pointToLayer: function(feature,latlng){

                if (feature.properties.category=="TS") {
                    var tcicon=ts_icon
                }
                else if (feature.properties.category=="1") {
                    var tcicon=c1_icon
                }
                else if (feature.properties.category=="2") {
                    var tcicon=c2_icon
                }
                else if (feature.properties.category=="3") {
                    var tcicon=c3_icon
                }
                else if (feature.properties.category=="4") {
                    var tcicon=c4_icon
                }
                else if (feature.properties.category=="5") {
                    var tcicon=c5_icon
                }

          return L.marker(latlng,{icon: tcicon});
        }

      }
    );

    cyclone_track.addTo(map);
  }

}
