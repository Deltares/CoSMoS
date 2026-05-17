// layers/wind.js — cosmos.layers.wind
// Wrapper around the vendored leaflet-velocity plugin for the animated wind
// field overlay. Reads wind.json.js from the current cycle.

(function () {

const { WIND_COLOR_SCALE } = cosmos.config;
const { state }            = cosmos;
const { loadGlobal, cyclePath } = cosmos.loaders;

/**
 * Create a leaflet-velocity layer and return a promise that resolves with it
 * once `wind.json.js` has loaded. Resolves to `null` on failure.
 */
async function makeWindLayer(scenarioName, cycleString) {
  const url = cyclePath(scenarioName, cycleString, 'wind.json.js');
  try {
    const data = await loadGlobal(url, 'wind');
    return L.velocityLayer({
      displayValues: true,
      displayOptions: {
        velocityType:       'Global Wind',
        displayPosition:    'bottomleft',
        displayEmptyString: 'No wind data',
      },
      data: data,
      maxVelocity:   state.maxWindVelocity,
      velocityScale: 0.01,
      colorScale:    WIND_COLOR_SCALE,
    });
  } catch (err) {
    console.warn(err.message);
    return null;
  }
}

cosmos.layers.wind = { makeWindLayer };

})();
