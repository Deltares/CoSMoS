// layers/tile.js — cosmos.layers.tile
// Builds Leaflet tile layers for variables with format `xyz_tile_layer`.
//
// CoSMoS publishes raster maps as standard XYZ tile pyramids under:
//   data/<scenario>/<cycle>/<variable>/[<time>/]{z}/{x}/{y}.png
//
// Time-stepped variables have one tile pyramid per time slice; static
// variables have one pyramid directly under <variable>/.

(function () {

const { TILE_LAYER_DEFAULTS } = cosmos.config;
const { cyclePath }           = cosmos.loaders;

/**
 * Build the array of Leaflet tile layers for a single variable.
 * Returns one layer per time-step, or a single-element array if the variable
 * has no time dimension.
 */
function makeTileLayers(scenarioName, cycleString, variable) {
  const baseUrl = cyclePath(scenarioName, cycleString, variable.name);
  const opts = Object.assign({}, TILE_LAYER_DEFAULTS, {
    maxNativeZoom: variable.max_native_zoom != null ? variable.max_native_zoom : 16,
  });

  if (!variable.times || variable.times.length === 0) {
    return [L.tileLayer(baseUrl + '/{z}/{x}/{y}.png', opts)];
  }
  return variable.times.map(function (t) {
    return L.tileLayer(baseUrl + '/' + t.name + '/{z}/{x}/{y}.png', opts);
  });
}

/** Base maps for the L.control.layers switcher. */
function makeBaseLayers(baseMaps) {
  const out = {};
  Object.values(baseMaps).forEach(function (def) {
    out[def.label] = L.tileLayer(def.url, def.options);
  });
  return out;
}

cosmos.layers.tile = { makeTileLayers, makeBaseLayers };

})();
