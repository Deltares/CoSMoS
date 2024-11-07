function thresholdsRUNUP(value) {
  // Low vulnerability: < 100 m
  // Moderate vulnerability: 100 - 300 m/yr
  // High vulnerability: 300 - 1000 m
  // Very high vulnerability: > 1000 m
  let color = cviColors[4]
  if( value < 1) {
    color = cviColors[0]
  } else if ( value < 2) {
    color = cviColors[1]
  } else if ( value < 4) {
    color = cviColors[2]
  } else if ( value >= 4) {
    color = cviColors[3]
  }
  return color
}

const onEachFeatureTWL50 = function (feature, layer) {
  const html = 'Location nr: &#9;' + feature.properties.LocNr + '<br />' +
  'Latitude: &#9;' + parseFloat(feature.properties.Lat).toFixed(3)  + ' [dgr N] &#9;' + '<br />' +
  'Longitude: &#9;' + parseFloat(feature.properties.Lon).toFixed(3) + ' [dgr E] &#9;' + '<br />' +
  'Wave run-up height: &#9;' + feature.properties.TWL +
  ' [m above MSL] &#9;' + '<br />'
  layer.bindTooltip(L.tooltip({ direction: 'top' }).setContent(html));
//  layer.bindPopup(html);

  var popup = L.popup({"maxWidth": "100%"});
  wlurl = 'html/total_water_level_timeseries.html?'
  wlurl = wlurl +       `name=${feature.properties.LocNr}`
  wlurl = wlurl + '&' + `longname=${feature.properties.LocNr}`
//  wlurl = wlurl +       `name=` + '0074'
//  wlurl = wlurl + '&' + `longname=${feature.properties.LocNr}`
  wlurl = wlurl + '&' + `id=${feature.properties.id}`
  wlurl = wlurl + '&' + `cycle=${currentScenario["cycle"]}`
  wlurl = wlurl + '&' + `duration=${currentScenario["duration"]}`
  wlurl = wlurl + '&' + `model_name=${feature.properties.model_name}`
  wlurl = wlurl + '&' + `scenario=${currentScenario["name"]}`
  var content = `<iframe src="${wlurl}" width="730" height="500"></iframe>`
  popup.setContent(content);
  layer.bindPopup(popup,{maxWidth : "auto"});


};

// Format for the points:
const pointToLayerTWL = function (feature, latlng) {
//	console.log(latlng)
  return new L.CircleMarker(latlng, {
    radius: 3,
    fillOpacity: 0.7,
	opacity: 0,
    color: thresholdsRUNUP(feature.properties.TWL)
  });
};


function makeExtremeRunupLayer() {
  // Add point markers for nearshore extremes
  var lyr = L.geoJson(undefined, {
    pointToLayer: pointToLayerTWL,
    onEachFeature: onEachFeatureTWL50
  })
  layers["extreme_runup_height"].push(lyr);
//  layers["extreme_runup_height"] = lyr;
  loadjs("data/" + currentScenario["name"] + "/extreme_runup_height/extreme_runup_height.geojson.js", runupLoaded, runupFailed);
}

function runupLoaded() {
//	console.log(runup)
  layers["extreme_runup_height"][0].addData(runup);
}

function runupFailed() {
	console.log('Could not load extreme_runup_height.geojson.js');
}


// SWL layers
const pointToLayerSWL = function (feature, latlng) {
  return new L.CircleMarker(latlng, {
    radius: 3,
    fillOpacity: 0.25,
	opacity: 0,
    color: 'blue'
  });
};

const onEachFeatureSWL50 = function (feature, layer) {
  const html = 'Location nr: &#9;' + feature.properties.LocNr + '<br />' +
    'Latitude: &#9;' + feature.properties.Lat + ' [dgr N] &#9;' + '<br />' +
    'Longitude: &#9;' + feature.properties.Lon + ' [dgr E] &#9;' + '<br />' +
    'Significant wave height: &#9;' + feature.properties.Hs + ' [m] &#9;' +
    '<br />' +
	'Peak wave period: &#9;' + feature.properties.Tp + ' [m] &#9;' +
    '<br />' +
    'Still Water Level: &#9;' + feature.properties.WL +
    ' [m above MSL] &#9;' + '<br />'
  layer.bindTooltip(L.tooltip({ direction: 'top' }).setContent(html));
  layer.bindPopup(html);
};

const onEachFeatureSWL100 = function (feature, layer) {
  const html = 'Location nr: &#9;' + feature.properties.LocNr + '<br />' +
    'Latitude: &#9;' + feature.properties.Lat + ' [dgr N] &#9;' + '<br />' +
    'Longitude: &#9;' + feature.properties.Lon + ' [dgr E] &#9;' + '<br />' +
    'Significant wave height: &#9;' + feature.properties.Hs + ' [m] &#9;' +
    '<br />' +
	'Peak wave period: &#9;' + feature.properties.Tp + ' [m] &#9;' +
    '<br />' +
    'Still Water Level: &#9;' + feature.properties.WL +
    ' [m above MSL] &#9;' + '<br />'
  layer.bindTooltip(L.tooltip({ direction: 'top' }).setContent(html));
  layer.bindPopup(html);
};


function makeExtremeSWLLayer() {
  // Add point markers for nearshore extremes
  var lyr = L.geoJson(undefined, {
    pointToLayer: pointToLayerSWL,
    onEachFeature: onEachFeatureSWL50
  })
  layers["extreme_sea_level_and_wave_height"].push(lyr);
  loadjs("data/" + currentScenario["name"] + "/extreme_sea_level_and_wave_height/extreme_sea_level_and_wave_height.geojson.js", swlLoaded, swlFailed);
}

function swlLoaded() {
  layers["extreme_sea_level_and_wave_height"][0].addData(swl);
}

function swlFailed() {
	console.log('Could not load extreme_sea_level_and_wave_height.geojson.js');
}
