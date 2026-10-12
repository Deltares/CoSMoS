// main.js
// Entry point. Wires the UI panel, layer modules, and Leaflet map together,
// and owns the scenario → cycle → variable → time selection flow.
// Loaded last in index.html, after all cosmos.* modules.

(function () {

const { BASE_MAPS, ANIMATION_FRAME_MS, LAYER_SWAP_DELAY_MS } = cosmos.config;
const { state }       = cosmos;
const { loadGlobal }  = cosmos.loaders;

const { makeBaseLayers, makeTileLayers } = cosmos.layers.tile;
const { makeGeoJsonLayer, GEOJSON_SPECS } = cosmos.layers.geojson;
const { makeWindLayer }                   = cosmos.layers.wind;
const { addTideGauges, addWaveBuoys,
        addXBeachMarkers, addModelOutlines } = cosmos.layers.stations;
const { addCycloneTrack, addCycloneTrackEnsemble } = cosmos.layers.cyclone;

const { renderScenarioPicker, renderCyclePicker, renderVariablePicker,
        renderTimePicker, renderStatus, renderDescription } = cosmos.ui.panel;
const { makeContourLegend } = cosmos.ui.legend;
const { makeIconLegend }    = cosmos.ui.iconLegend;

// ---------------------------------------------------------------------------
// 1. Map and base layers
// ---------------------------------------------------------------------------

const baseLayers = makeBaseLayers(BASE_MAPS);

state.map = L.map('map', {
  center:       [18.2, -66.5],   // overridden by each scenario's lat/lon
  zoom:         10,
  minZoom:      0,
  maxZoom:      19,
  zoomControl:  true,
  preferCanvas: false,
  layers:       [baseLayers[BASE_MAPS.esri.label]],
});
L.control.scale({ imperial: false, position: 'bottomright' }).addTo(state.map);
L.control.layers(baseLayers, {}).addTo(state.map);

// ---------------------------------------------------------------------------
// 2. Bootstrap: load scenarios manifest, build picker, select first
// ---------------------------------------------------------------------------

loadGlobal('data/scenarios.js', 'scenario')
  .then(function (scenarios) {
    console.log(scenarios.length + ' scenarios found');
    renderScenarioPicker(scenarios, selectScenarioByName);
    selectScenario(scenarios[0]);
  })
  .catch(function (err) { console.error(err.message); });

function selectScenarioByName(name) {
  const s = window.scenario.find(function (x) { return x.name === name; });
  if (s) selectScenario(s);
}

function selectScenario(scenario) {
  state.currentScenario = scenario;
  state.currentCycle    = scenario.cycle_string;

  renderDescription(scenario.description);
  state.map.setView([scenario.lat, scenario.lon], scenario.zoom);
  renderCyclePicker(scenario, selectCycle);

  selectCycle(scenario.cycle_string);
}

// ---------------------------------------------------------------------------
// 3. Cycle selection: rebuild overlays and load the variable list
// ---------------------------------------------------------------------------

function selectCycle(cycleString) {
  state.currentCycle = cycleString;

  // Rebuild marker overlays.
  refreshIconLegend();
  addTideGauges();
  addWaveBuoys();
  addXBeachMarkers();
  addModelOutlines();
  addCycloneTrack();
  addCycloneTrackEnsemble();

  // Load the cycle's variable manifest and build layers.
  const variablesUrl = 'data/' + state.currentScenario.name + '/' + cycleString + '/variables.js';
  loadGlobal(variablesUrl, 'map_variables')
    .then(onVariablesLoaded)
    .catch(function (err) { console.warn('No variables: ' + err.message); });

  renderStatus(state.currentScenario, cycleString);
}

// ---------------------------------------------------------------------------
// 4. Variables loaded: build all layers, render the picker
// ---------------------------------------------------------------------------

function onVariablesLoaded(variables) {
  state.currentScenario.variable = variables;
  state.layers = {};

  variables.forEach(function (v) {
    v.ntimes = v.times ? v.times.length : 0;
    buildLayersForVariable(v);
  });

  renderVariablePicker(variables, selectVariableByName);
  state.currentVariable = variables[0];
  selectVariable();
}

function buildLayersForVariable(v) {
  const scenario = state.currentScenario.name;
  const cycle    = state.currentCycle;

  if (v.format === 'xyz_tile_layer') {
    state.layers[v.name] = makeTileLayers(scenario, cycle, v);
  } else if (v.format === 'geojson' && GEOJSON_SPECS[v.name]) {
    state.layers[v.name] = [makeGeoJsonLayer(v.name, scenario, cycle)];
  } else if (v.format === 'vector_field' && v.name === 'wind') {
    state.layers.wind = [];
    state.maxWindVelocity = v.max;
    makeWindLayer(scenario, cycle).then(function (layer) {
      if (!layer) return;
      state.layers.wind.push(layer);
      const radio = document.getElementById('variable_wind');
      if (radio) radio.disabled = false;
      if (state.currentVariable && state.currentVariable.name === 'wind') {
        state.currentLayer = layer;
        state.map.addLayer(layer);
      }
    });
  } else {
    console.warn('Unhandled variable: ' + v.name + ' (format=' + v.format + ')');
    state.layers[v.name] = [];
  }
}

// ---------------------------------------------------------------------------
// 5. Variable selection: rebuild legend, time picker, show frame 0
// ---------------------------------------------------------------------------

function selectVariableByName(name) {
  const v = state.currentScenario.variable.find(function (x) { return x.name === name; });
  if (v) {
    state.currentVariable = v;
    selectVariable();
  }
}

function selectVariable() {
  clearTimeout(state.animationTimeout);
  state.currentTime  = 0;
  state.previousTime = -1;

  if (state.currentLayer) state.currentLayer.remove();
  state.currentLayer = null;

  if (state.controlLegend) state.controlLegend.remove();
  state.controlLegend = makeContourLegend(state.currentVariable);
  if (state.controlLegend) state.controlLegend.addTo(state.map);

  // Update the right-hand iframe infographic if the variable has one.
  if (state.currentVariable.infographic) {
    const iframe = parent.document.getElementById('myIframe');
    if (iframe) iframe.src = 'img/infographics/' + state.currentVariable.infographic + '.html';
  }

  renderTimePicker(state.currentVariable,
                   function (idx) { state.currentTime = idx; selectTime(); },
                   playAnimation, pauseAnimation);
  selectTime();
}

// ---------------------------------------------------------------------------
// 6. Time selection: swap layers with a small delay to hide flicker
// ---------------------------------------------------------------------------

function selectTime() {
  const arr  = state.layers[state.currentVariable.name];
  const next = arr && arr[state.currentTime];
  if (!next) return;

  state.currentLayer = next;
  state.map.addLayer(next);
  setTimeout(removePreviousLayer, LAYER_SWAP_DELAY_MS);
}

function removePreviousLayer() {
  if (state.previousTime > -1) {
    const arr = state.layers[state.currentVariable.name];
    const prev = arr && arr[state.previousTime];
    if (prev) prev.remove();
  }
  state.previousTime = state.currentTime;
}

function playAnimation() {
  state.currentTime = (state.currentTime + 1) % state.currentVariable.ntimes;
  selectTime();
  const sel = document.getElementById('timeselector');
  if (sel) sel.value = state.currentTime;
  state.animationTimeout = setTimeout(playAnimation, ANIMATION_FRAME_MS);
}

function pauseAnimation() {
  clearTimeout(state.animationTimeout);
}

// ---------------------------------------------------------------------------
// 7. Icon legend (rebuilt every cycle in case overlay availability changed)
// ---------------------------------------------------------------------------

function refreshIconLegend() {
  if (state.iconLegend) state.iconLegend.remove();

  function markerImg(file, w, h) {
    return "<img src='./img/markers/" + file + "' height='" + h + "' width='" + w + "' style='margin:-1px 0'>";
  }

  state.iconLegend = makeIconLegend([
    { label: 'Tide gauge',     markerHtml: markerImg('tide_gauge.png', 25, 25),
      onShow: addTideGauges,
      onHide: function () { if (state.markers.tideGauges) state.markers.tideGauges.remove(); } },
    { label: 'Wave buoy',      markerHtml: markerImg('wave_buoy.png', 25, 25),
      onShow: addWaveBuoys,
      onHide: function () { if (state.markers.waveBuoys) state.markers.waveBuoys.remove(); } },
    { label: 'Storm track',    markerHtml: markerImg('Category_3_hurricane_icon_c2.png', 18, 36),
      onShow: addCycloneTrack,
      onHide: function () { if (state.markers.cycloneTrack) state.markers.cycloneTrack.remove(); } },
    { label: 'Track ensemble',
      onShow: addCycloneTrackEnsemble,
      onHide: function () { if (state.markers.cycloneEnsemble) state.markers.cycloneEnsemble.remove(); } },
  ]);
  state.iconLegend.addTo(state.map);
}

})();
