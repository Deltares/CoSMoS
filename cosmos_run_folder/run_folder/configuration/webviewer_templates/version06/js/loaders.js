// loaders.js
// Data loading for CoSMoS web viewer files. Attached to cosmos.loaders.
//
// JSONP contract
// --------------
// The Python side (cosmos.webviewer.WebViewer) writes data files as classic
// JavaScript files that begin with `var <name> = ...`. They are NOT JSON, and
// NOT ES modules — they're scripts that, when executed, attach a value to
// `window.<name>`. The known mapping is:
//
//   scenarios.js                          → window.scenario
//   <scenario>/<cycle>/variables.js       → window.map_variables
//   stations.geojson.js                   → window.stations
//   wavebuoys.geojson.js                  → window.buoys
//   xbeach.geojson.js                     → window.xb_markers
//   xb.geojson.js                         → window.xb_models
//   track.geojson.js                      → window.track_data
//   track_ensemble.geojson.js             → window.track_ensemble_data
//   wind.json.js                          → window.wind
//   extreme_runup_height.geojson.js       → window.runup
//   extreme_horizontal_runup_height...    → window.runup_vert
//   extreme_runup_height_prc95...         → window.runup_prc95
//   extreme_sea_level_and_wave_height...  → window.swl
//   estimated_total_water_level.geojson.js → window.etwl
//   ensemble.geojson.js                   → window.track_ens
//   timeseries CSVs                       → window.csv  (and window.csv_obs)
//
// `loadScript(url)` injects a non-module <script> tag and resolves once it
// fires `load`. The caller then reads the expected global. Failure (404,
// network error, parse error) rejects.

(function () {

/** Inject a classic <script> tag and resolve when it loads. */
function loadScript(url) {
  return new Promise(function (resolve, reject) {
    const tag = document.createElement('script');
    tag.src = url;
    tag.addEventListener('load',  function () { resolve(url); });
    tag.addEventListener('error', function () { reject(new Error('Failed to load ' + url)); });
    document.body.appendChild(tag);
  });
}

/**
 * Load a data script, then return the value assigned to window[globalName].
 *   const scenarios = await loadGlobal('data/scenarios.js', 'scenario');
 */
async function loadGlobal(url, globalName) {
  await loadScript(url);
  return window[globalName];
}

/**
 * Try to load — log a warning and resolve to null on failure. Use for
 * optional data sources (wave buoys, ensemble tracks) so that one missing
 * file doesn't break the whole page.
 */
async function tryLoadGlobal(url, globalName) {
  try {
    return await loadGlobal(url, globalName);
  } catch (err) {
    console.warn(err.message);
    return null;
  }
}

/** Build the path to a per-cycle data file:
 *  data/<scenario_name>/<cycle_string>/<rest> */
function cyclePath(scenarioName, cycleString, rest) {
  return 'data/' + scenarioName + '/' + cycleString + '/' + (rest || '');
}

cosmos.loaders = { loadScript, loadGlobal, tryLoadGlobal, cyclePath };

})();
