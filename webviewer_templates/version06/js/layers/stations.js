// layers/stations.js — cosmos.layers.stations
// Marker layers for tide gauges, wave buoys, XBeach output points, and
// model-outline polygons. Each function loads its source data, attaches it
// to the map, and stores the resulting layer in cosmos.state.markers.* so
// the icon legend's checkboxes can toggle it later.

(function () {

const { ICONS } = cosmos.config;
const { state } = cosmos;
const { tryLoadGlobal, cyclePath } = cosmos.loaders;

function makeStationLayer(data, icon, popupBuilder) {
  return L.geoJson(data, {
    pointToLayer:  function (_f, latlng) { return L.marker(latlng, { icon: icon }); },
    onEachFeature: function (feature, layer) { popupBuilder(feature, layer); },
  });
}

function timeseriesUrl(plotType, props) {
  const params = new URLSearchParams({
    type:         plotType,
    name:         props.name || '',
    longname:     props.long_name || '',
    id:           props.id || '',
    cycle:        state.currentCycle,
    cycle_string: state.currentCycle,
    scenario:     state.currentScenario.name,
    duration:     state.currentScenario.duration || '',
    model_name:   props.model_name || '',
    mllw:         props.mllw || '',
    obsfile:      props.obs_file || '',
    prdfile:      props.prd_file || '',
    ensemble:     props.model_ensemble || '',
  });
  return 'html/timeseries.html?' + params.toString();
}

function bindIframePopup(layer, plotType, props) {
  const url = timeseriesUrl(plotType, props);
  layer.bindPopup(
    L.popup({ maxWidth: 'auto' }).setContent(
      '<iframe src="' + url + '" width="730" height="500" frameborder="0"></iframe>',
    ),
  );
}

// --- Tide gauges ---

async function addTideGauges() {
  if (state.markers.tideGauges) state.markers.tideGauges.remove();
  const data = await tryLoadGlobal(
    cyclePath(state.currentScenario.name, state.currentCycle, 'stations.geojson.js'),
    'stations',
  );
  if (!data) return;
  state.markers.tideGauges = makeStationLayer(data, ICONS.tide_gauge,
    function (feature, layer) {
      bindIframePopup(layer, 'water_level_ensemble', feature.properties);
    },
  );
  state.markers.tideGauges.addTo(state.map);
}

// --- Wave buoys ---

async function addWaveBuoys() {
  if (state.markers.waveBuoys) state.markers.waveBuoys.remove();
  const data = await tryLoadGlobal(
    cyclePath(state.currentScenario.name, state.currentCycle, 'wavebuoys.geojson.js'),
    'buoys',
  );
  if (!data) return;
  state.markers.waveBuoys = makeStationLayer(data, ICONS.wave_buoy,
    function (feature, layer) {
      bindIframePopup(layer, 'wave', feature.properties);
    },
  );
  state.markers.waveBuoys.addTo(state.map);
}

// --- XBeach model markers ---

async function addXBeachMarkers() {
  if (state.markers.xbeach) state.markers.xbeach.remove();
  const data = await tryLoadGlobal(
    cyclePath(state.currentScenario.name, state.currentCycle, 'xbeach.geojson.js'),
    'xb_markers',
  );
  if (!data) return;
  state.markers.xbeach = L.geoJson(data, {
    pointToLayer: function (_f, latlng) { return L.marker(latlng, { icon: ICONS.xbeach }); },
    onEachFeature: function (feature, layer) {
      const html = 'Model: ' + feature.properties.long_name + '<br/>';
      layer.bindTooltip(L.tooltip({ direction: 'top' }).setContent(html));
      layer.bindPopup(html);
    },
  });
  state.markers.xbeach.addTo(state.map);
}

// --- Model outline polygons ---

async function addModelOutlines() {
  if (state.markers.modelOutlines) state.markers.modelOutlines.remove();
  const data = await tryLoadGlobal(
    cyclePath(state.currentScenario.name, state.currentCycle, 'xb.geojson.js'),
    'xb_models',
  );
  if (!data) return;
  state.markers.modelOutlines = L.geoJson(data);
  state.markers.modelOutlines.addTo(state.map);
}

cosmos.layers.stations = {
  addTideGauges, addWaveBuoys, addXBeachMarkers, addModelOutlines,
};

})();
