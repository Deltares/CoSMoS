// timeseries/plot-types.js — cosmos.timeseries.plotTypes
// One async function per supported plot type. Each function fetches its
// own data, constructs Plotly traces, and adds them to the plot element.
//
// The set of types here corresponds 1-to-1 with the seven separate HTML
// pages that existed in version05:
//
//   v06 type                    |  v05 HTML page
//   ----------------------------|---------------------------------------------
//   water_level                 |  water_level_timeseries.html
//   water_level_ensemble        |  water_level_timeseries_ensemble.html
//   wave                        |  wave_timeseries.html
//   runup                       |  runup_timeseries.html
//   total_water_level           |  total_water_level_timeseries.html
//   total_water_level_prob      |  total_water_level_timeseries_prob.html
//   estimated_total_water_level |  estimated_total_water_level_timeseries.html
//
// Adding a new type = add one function and one entry to PLOT_TYPES.

(function () {

const { loadCsvScript, parseCsv, fetchCoops,
        lineTrace, bandTraces, makeLayout } = cosmos.timeseries.core;

// --- Path helpers — keep CSV URL patterns in one place ---

const paths = {
  wl:      function (p) { return '../data/' + p.scenario + '/' + p.cycle_string + '/timeseries/wl.' + p.name + '.' + p.model_name + '.csv.js'; },
  waves:   function (p) { return '../data/' + p.scenario + '/' + p.cycle_string + '/timeseries/waves.' + p.name + '.' + p.model_name + '.csv.js'; },
  runup:   function (p) { return '../data/' + p.scenario + '/extreme_runup_height/extreme_runup_height.' + p.model_name + '.' + p.name + '.csv.js'; },
  twl:     function (p) { return '../data/' + p.scenario + '/timeseries/extreme_runup_height.' + p.model_name + '.' + p.name + '.csv.js'; },
  obsFile: function (p) { return '../data/' + p.scenario + '/timeseries/' + p.obsfile; },
  prdFile: function (p) { return '../data/' + p.scenario + '/' + p.cycle_string + '/timeseries/' + p.prdfile; },
};

// Try to fetch a single CSV-as-JS file. Logs and resolves null on failure so
// missing optional data doesn't break the whole plot.
async function tryCsv(url, numCols, globalName) {
  globalName = globalName || 'csv';
  try {
    const text = await loadCsvScript(url, globalName);
    return parseCsv(text, numCols);
  } catch (err) {
    console.warn(err.message);
    return null;
  }
}

// --- Plot type: water_level (deterministic single station) ---

async function plotWaterLevel(plot, p, win) {
  Plotly.newPlot(plot, [], makeLayout({
    title:  'Water level ' + p.longname,
    yLabel: 'Height in metres (MSL)',
    t0Axis: win.t0Axis, t1: win.t1,
  }));

  tryCsv(paths.wl(p), 1).then(function (csv) {
    if (!csv) return;
    Plotly.addTraces(plot, lineTrace(csv.times, csv.columns[0],
      { name: 'Computed', color: '#ff7f0e' }));
  });

  if (p.id && p.id !== 'Empty') {
    fetchCoops(p.id, win.t0, win.t1, 'water_level').then(function (d) {
      if (d.times.length) Plotly.addTraces(plot, lineTrace(d.times, d.values,
        { name: 'Observed', color: '#00cc00' }));
    });
    fetchCoops(p.id, win.t0, win.t1, 'predictions').then(function (d) {
      if (d.times.length) Plotly.addTraces(plot, lineTrace(d.times, d.values,
        { name: 'Astronomic prediction', color: '#0000ff' }));
    });
  }

  if (p.obsfile && p.obsfile !== 'Empty') {
    tryCsv(paths.obsFile(p), 1, 'csv_obs').then(function (csv) {
      if (csv) Plotly.addTraces(plot, lineTrace(csv.times, csv.columns[0],
        { name: 'Observed (file)', color: '#00cc00' }));
    });
  }
}

// --- Plot type: water_level_ensemble ---
// Deterministic CSV when ensemble=false, otherwise 4-column [best, 5%,
// median, 95%]; rendered as best-line + shaded 5–95% band.

async function plotWaterLevelEnsemble(plot, p, win) {
  Plotly.newPlot(plot, [], makeLayout({
    title:  'Water level ' + p.longname,
    yLabel: 'Height in metres (MSL)',
    t0Axis: win.t0Axis, t1: win.t1,
  }));

  if (p.ensemble === 'true') {
    tryCsv(paths.wl(p), 4).then(function (csv) {
      if (!csv) return;
      const best = csv.columns[0], low = csv.columns[1],
            median = csv.columns[2], high = csv.columns[3];
      Plotly.addTraces(plot, bandTraces(csv.times, high, low,
        { name: 'Ensemble 5–95%', fillColor: 'rgba(255,127,14,0.2)' }));
      Plotly.addTraces(plot, lineTrace(csv.times, median,
        { name: 'Ensemble median', color: '#ff7f0e', dash: 'dot' }));
      Plotly.addTraces(plot, lineTrace(csv.times, best,
        { name: 'Best track', color: '#ff7f0e' }));
    });
  } else {
    tryCsv(paths.wl(p), 1).then(function (csv) {
      if (!csv) return;
      Plotly.addTraces(plot, lineTrace(csv.times, csv.columns[0],
        { name: 'Computed', color: '#ff7f0e' }));
    });
  }

  // Live NOAA CO-OPS observations + astronomic prediction by station id.
  if (p.id && p.id !== 'Empty') {
    fetchCoops(p.id, win.t0, win.t1, 'water_level').then(function (d) {
      if (d.times.length) Plotly.addTraces(plot, lineTrace(d.times, d.values,
        { name: 'Observed', color: '#00cc00' }));
    });
    fetchCoops(p.id, win.t0, win.t1, 'predictions').then(function (d) {
      if (d.times.length) Plotly.addTraces(plot, lineTrace(d.times, d.values,
        { name: 'Astronomic prediction', color: '#0000ff' }));
    });
  }

  // File-based observations/predictions (labelled "(file)" to avoid clashing
  // with the CO-OPS traces above when a station has both).
  if (p.obsfile && p.obsfile !== 'Empty') {
    tryCsv(paths.obsFile(p), 1, 'csv_obs').then(function (csv) {
      if (csv) Plotly.addTraces(plot, lineTrace(csv.times, csv.columns[0],
        { name: 'Observed (file)', color: '#00cc00' }));
    });
  }
  if (p.prdfile && p.prdfile !== 'Empty') {
    tryCsv(paths.prdFile(p), 1, 'csvprd').then(function (csv) {
      if (csv) Plotly.addTraces(plot, lineTrace(csv.times, csv.columns[0],
        { name: 'Astronomic prediction (file)', color: '#0000ff' }));
    });
  }
}

// --- Plot type: wave (Hm0 + Tp on two y-axes) ---

async function plotWave(plot, p, win) {
  const layout = makeLayout({
    title:  'Waves at ' + p.longname,
    yLabel: 'Significant wave height Hm0 (m)',
    t0Axis: win.t0Axis, t1: win.t1,
    overrides: {
      yaxis2: {
        title: { text: 'Peak period Tp (s)', font: { color: '#000' } },
        overlaying: 'y', side: 'right',
        linecolor: '#000', hoverformat: '.1f',
      },
    },
  });
  Plotly.newPlot(plot, [], layout);

  tryCsv(paths.waves(p), 2).then(function (csv) {
    if (!csv) return;
    Plotly.addTraces(plot, lineTrace(csv.times, csv.columns[0],
      { name: 'Hm0', color: '#1f77b4' }));
    // Tp goes on the right-hand y-axis.
    Plotly.addTraces(plot, Object.assign(
      lineTrace(csv.times, csv.columns[1], { name: 'Tp', color: '#d62728' }),
      { yaxis: 'y2' },
    ));
  });
}

// --- Plot types: simple single-line CSV plots (runup, TWL, ETWL) ---

function makeSimpleLinePlot(spec) {
  return async function (plot, p, win) {
    Plotly.newPlot(plot, [], makeLayout({
      title:  spec.title(p),
      yLabel: spec.yLabel,
      t0Axis: win.t0Axis, t1: win.t1,
    }));
    tryCsv(spec.urlBuilder(p), 1).then(function (csv) {
      if (!csv) return;
      Plotly.addTraces(plot, lineTrace(csv.times, csv.columns[0],
        { name: 'Computed', color: '#ff7f0e' }));
    });
  };
}

const plotRunup = makeSimpleLinePlot({
  urlBuilder: paths.runup,
  title:  function (p) { return 'Extreme run-up — ' + p.longname; },
  yLabel: 'Run-up (m)',
});

const plotTotalWaterLevel = makeSimpleLinePlot({
  urlBuilder: paths.twl,
  title:  function (p) { return 'Total water level — Transect ' + p.name; },
  yLabel: 'Total water level (m above MSL)',
});

const plotEstimatedTotalWaterLevel = makeSimpleLinePlot({
  urlBuilder: paths.twl,
  title:  function (p) { return 'Total water level — ' + p.name; },
  yLabel: 'Total water level (m above MSL)',
});

// total_water_level_prob: CSV with 4 columns [best, 5%, ..., 95%] rendered
// as best-line + shaded 5–95% band.
async function plotTotalWaterLevelProb(plot, p, win) {
  Plotly.newPlot(plot, [], makeLayout({
    title:  'Total water level — Transect ' + p.name,
    yLabel: 'Total water level (m above MSL)',
    t0Axis: win.t0Axis, t1: win.t1,
  }));
  tryCsv(paths.twl(p), 4).then(function (csv) {
    if (!csv) return;
    const best = csv.columns[0], low = csv.columns[1], high = csv.columns[3];
    Plotly.addTraces(plot, bandTraces(csv.times, high, low,
      { name: '5–95% band', fillColor: 'rgba(255,127,14,0.2)' }));
    Plotly.addTraces(plot, lineTrace(csv.times, best,
      { name: 'Best track', color: '#ff7f0e' }));
  });
}

// --- Registry ---

cosmos.timeseries.plotTypes = {
  PLOT_TYPES: {
    water_level:                 plotWaterLevel,
    water_level_ensemble:        plotWaterLevelEnsemble,
    wave:                        plotWave,
    runup:                       plotRunup,
    total_water_level:           plotTotalWaterLevel,
    total_water_level_prob:      plotTotalWaterLevelProb,
    estimated_total_water_level: plotEstimatedTotalWaterLevel,
  },
};

})();
