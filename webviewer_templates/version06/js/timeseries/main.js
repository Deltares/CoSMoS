// timeseries/main.js
// Entry point for html/timeseries.html. Reads `?type=<plot type>&...` from
// the query string, looks up the corresponding function in PLOT_TYPES, and
// calls it with the parsed parameters and the time window.

(function () {

const { readParams, timeWindow } = cosmos.timeseries.core;
const { PLOT_TYPES }             = cosmos.timeseries.plotTypes;

const params  = readParams();
const plotEl  = document.getElementById('plot');
const modelEl = document.getElementById('model_text');

if (modelEl) modelEl.textContent = 'Model: ' + (params.model_name || '');

const plotFn = PLOT_TYPES[params.type];
if (!plotFn) {
  document.body.innerHTML =
    '<p style="font-family:sans-serif">Unknown plot type: <code>' +
    params.type + '</code></p>';
} else {
  const win = timeWindow(params.cycle, parseFloat(params.duration) || 24);
  plotFn(plotEl, params, win);
}

})();
