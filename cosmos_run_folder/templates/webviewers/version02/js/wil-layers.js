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

function thresholdsHs(value) {
  let color = cviColors[4]
  if( value < 0) {
    color = '#CCFFFF00'
  } else if ( value < 2) {
    color = '#40E0D0'
  } else if ( value < 4) {
    color = '#40E0D0'
  } else if ( value < 6) {
    color = '#00BFFF'
  } else if ( value >= 6) {
    color = '#0909FF'
  }
  return color
}

const onEachFeatureTWL50 = function (feature, layer) {
  const html = 'Location nr: &#9;' + feature.properties.LocNr + '<br />' +
  'Latitude: &#9;' + feature.properties.Lat + ' [dgr N] &#9;' + '<br />' +
  'Longitude: &#9;' + feature.properties.Lon + ' [dgr E] &#9;' + '<br />' +
  'Wave run-up height: &#9;' + feature.properties.TWL +
  ' [m above MSL] &#9;' + '<br />'
  layer.bindTooltip(L.tooltip({ direction: 'top' }).setContent(html));
  layer.bindPopup(html);

  var popup = L.popup({"maxWidth": "100%"});
  wlurl = 'html/runup_timeseries.html?'
//  wlurl = wlurl +       `name=${feature.properties.LocNr}`
//  wlurl = wlurl + '&' + `longname=${feature.properties.LocNr}`
  wlurl = wlurl +       `name=` + '0074'
  wlurl = wlurl + '&' + `longname=${feature.properties.LocNr}`
  wlurl = wlurl + '&' + `id=${feature.properties.id}`
  wlurl = wlurl + '&' + `cycle=${currentScenario["cycle"]}`
  wlurl = wlurl + '&' + `duration=${currentScenario["duration"]}`
  wlurl = wlurl + '&' + `model_name=${feature.properties.model_name}`
  wlurl = wlurl + '&' + 'model_name=beware_puerto_rico'
  wlurl = wlurl + '&' + `scenario=${currentScenario["name"]}`
  var content = `<iframe src="${wlurl}" width="600" height="350"></iframe>`
  popup.setContent(content);
  layer.bindPopup(popup,{maxWidth : "auto"});

};


const onEachFeatureTWL100 = function (feature, layer) {
  const html = 'Location nr: &#9;' + feature.properties.LocNr + '<br />' +
    'Latitude: &#9;' + feature.properties.Lat + ' [dgr N] &#9;' + '<br />' +
    'Longitude: &#9;' + feature.properties.Lon + ' [dgr E] &#9;' + '<br />' +
    'Wave run-up height: &#9;' + feature.properties.TWL + ' [m above MSL] &#9;' + '<br />'
  layer.bindTooltip(L.tooltip({ direction: 'top' }).setContent(html));
  layer.bindPopup(html);

}

// Format for the points:
const pointToLayerTWL = function (feature, latlng) {
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
  layers["extreme_runup_height"] = lyr;
  var fname = "data/" + currentScenario["name"] + "/extreme_runup_height/extreme_runup_height.geojson.js"
  loadjs(fname, runupLoaded, runupFailed);
}

function runupLoaded() {
  layers["extreme_runup_height"].addData(runup);
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
    color: thresholdsHs(feature.properties.Hs)
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
  layers["extreme_sea_level_and_wave_height"] = lyr;
  loadjs("data/" + currentScenario["name"] + "/extreme_sea_level_and_wave_height/extreme_sea_level_and_wave_height.geojson.js", swlLoaded, swlFailed);
}

function swlLoaded() {
  layers["extreme_sea_level_and_wave_height"].addData(swl);
}

function swlFailed() {
	console.log('Could not load extreme_sea_level_and_wave_height.geojson.js');
}
