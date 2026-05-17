// timeseries/core.js — cosmos.timeseries.core
// Shared helpers for the unified timeseries page (html/timeseries.html).
// Replaces the copy-pasted blocks (getUrlVars, getUrlParam, pad, loadjs,
// csvToArray*, the Plotly layout) that appeared in all seven v05 HTML files.

(function () {

const { loadScript, loadGlobal } = cosmos.loaders;

// --- URL parameters ---

/**
 * Read all query-string parameters into a plain object. Missing values
 * fall back to '' rather than `undefined` so callers can interpolate freely.
 */
function readParams() {
  const out = {};
  for (const pair of new URLSearchParams(window.location.search)) {
    out[pair[0]] = decodeURIComponent(pair[1]);
  }
  return out;
}

// --- Time window ---

/**
 * Build the t0 / t0Axis / t1 timestamps used by all timeseries plots.
 *   • cycle   = forecast cycle (Date)
 *   • t0      = cycle − 36 h  (data fetched from here)
 *   • t0Axis  = cycle − 24 h  (plot starts here)
 *   • t1      = cycle + duration h  (end of plot)
 */
function timeWindow(cycleString, durationHours) {
  const cycle = new Date(cycleString);
  return {
    cycle:  cycle,
    t0:     new Date(cycle.getTime() - 36 * 3600 * 1000),
    t0Axis: new Date(cycle.getTime() - 24 * 3600 * 1000),
    t1:     new Date(cycle.getTime() + durationHours * 3600 * 1000),
  };
}

/** Format a Date as `YYYYMMDD HH:00` (NOAA CO-OPS API format). */
function formatNoaaDate(d) {
  function pad(n) { return String(n).padStart(2, '0'); }
  return d.getUTCFullYear() + pad(d.getUTCMonth() + 1) + pad(d.getUTCDate()) +
         ' ' + pad(d.getUTCHours()) + ':00';
}

// --- CSV parsing ---

/**
 * Parse a CSV string into { times, columns }.
 *   - times    : array of Date.parse timestamps (ms) parsed from column 0
 *   - columns  : array of arrays; columns[k] is the values of column k+1
 *
 * Skips a single header line. Times are interpreted as UTC by appending 'Z'.
 * `numColumns` is the number of data columns expected (excluding time).
 */
function parseCsv(str, numColumns, delimiter) {
  delimiter = delimiter || ',';
  const lines = str.split('\n');
  const times = [];
  const columns = [];
  for (let k = 0; k < numColumns; k++) columns.push([]);
  for (let i = 1; i < lines.length; i++) {
    if (!lines[i].trim()) continue;
    const tv = lines[i].split(delimiter);
    times.push(Date.parse(tv[0] + 'Z'));
    for (let k = 0; k < numColumns; k++) {
      columns[k].push(parseFloat(tv[k + 1]));
    }
  }
  return { times: times, columns: columns };
}

// --- NOAA CO-OPS observations / predictions ---

async function fetchCoops(coopsId, t0, t1, product) {
  const url = 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter' +
    '?begin_date=' + formatNoaaDate(t0) + '&end_date=' + formatNoaaDate(t1) +
    '&station=' + coopsId + '&product=' + product +
    '&datum=msl&units=metric&time_zone=gmt&application=cosmos&format=json';
  const resp = await fetch(url).then(function (r) { return r.json(); });
  const rows = product === 'water_level' ? resp.data : resp.predictions;
  if (!rows) return { times: [], values: [] };
  return {
    times:  rows.map(function (r) { return Date.parse(r.t); }),
    values: rows.map(function (r) { return parseFloat(r.v); }),
  };
}

// --- Plotly trace + layout factories ---

function lineTrace(times, values, opts) {
  return {
    type: 'scatter', mode: 'lines',
    name: opts.name,
    x: times, y: values,
    line: { color: opts.color, dash: opts.dash || 'solid' },
    hovertemplate: (opts.hoverPrefix || opts.name) + ': %{y:0.1f}<extra></extra>',
  };
}

/**
 * Build a shaded-band pair (upper invisible + lower with fill:'tonexty').
 * Returns [upperTrace, lowerTrace] in the order Plotly expects.
 */
function bandTraces(times, upper, lower, opts) {
  return [
    {
      type: 'scatter', mode: 'lines', name: opts.name + ' upper',
      x: times, y: upper,
      line: { width: 0, color: opts.fillColor },
      showlegend: false, hoverinfo: 'skip',
    },
    {
      type: 'scatter', mode: 'lines', name: opts.name,
      x: times, y: lower,
      line: { width: 0, color: opts.fillColor },
      fill: 'tonexty', fillcolor: opts.fillColor,
      hoverinfo: 'skip',
    },
  ];
}

/**
 * Build the Plotly layout shared by every timeseries plot. Caller may
 * override any field (e.g. for two-y-axis wave plots).
 */
function makeLayout(opts) {
  const overrides = opts.overrides || {};
  return Object.assign({
    title: opts.title,
    plot_bgcolor: '#d7ecfc',
    width: 700,
    xaxis: {
      title: { text: 'Time (UTC)', font: { color: '#000' } },
      type: 'date',
      linecolor: '#000', gridwidth: 1, gridcolor: '#fff',
      tickmode: 'auto', tickangle: 0,
      tickfont: { color: '#000' },
      hoverformat: '%a %e %b %H:%M',
      range: [opts.t0Axis, opts.t1],
    },
    yaxis: {
      title: { text: opts.yLabel, font: { color: '#000' } },
      linecolor: '#000', gridwidth: 1, gridcolor: '#fff',
      zeroline: false, tickmode: 'auto',
      hoverformat: '.1f',
      tickfont: { color: '#000' },
    },
    legend: { orientation: 'h', y: 1.12 },
  }, overrides);
}

cosmos.timeseries.core = {
  // Re-exports of cosmos.loaders so callers don't need to import both.
  loadScript: loadScript,
  loadCsvScript: loadGlobal,
  // Local helpers
  readParams, timeWindow, formatNoaaDate, parseCsv, fetchCoops,
  lineTrace, bandTraces, makeLayout,
};

})();
