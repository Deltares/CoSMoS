// layers/geojson.js — cosmos.layers.geojson
// Table-driven GeoJSON point-layer factories.
//
// In version05 there were six near-duplicate functions (makeExtremeRunupLayer,
// makeExtremeSWLLayer, makeExtremeRunupLayer_H, makeExtremeRunupLayer_prob,
// makeEstimatedTotalWaterLevelLayer, makeTrackEnsemble) that differed only in:
//   • which colour-threshold function to apply
//   • which CSV column to read
//   • which timeseries plot type to open on click
//   • which extra fields to show in the tooltip
//
// Here they collapse to one `makeGeoJsonLayer(specName, scenario, cycle)`
// driven by a config record. Add new variable types by appending to
// GEOJSON_SPECS below — no new function needed.

(function () {

const { CVI_COLORS }         = cosmos.config;
const { state }              = cosmos;
const { loadGlobal, cyclePath } = cosmos.loaders;

// --- Colour thresholds ---

function thresholdsRunup(value) {
  if (value < 1) return CVI_COLORS[0];
  if (value < 2) return CVI_COLORS[1];
  if (value < 4) return CVI_COLORS[2];
  return CVI_COLORS[3];
}

// --- Tooltip / popup helpers ---

function fmt(v, digits) {
  if (v == null || Number.isNaN(parseFloat(v))) return 'NA';
  return parseFloat(v).toFixed(digits != null ? digits : 1);
}

function tooltipHtml(fields) {
  return fields.map(function (f) { return f.label + ': ' + f.value + '<br/>'; }).join('');
}

function timeseriesUrl(plotType, props, scenarioName, cycleString) {
  const params = new URLSearchParams({
    type:         plotType,
    name:         props.name || props.LocNr || props.station_name || '',
    longname:     props.long_name || props.LocNr || props.station_name || '',
    id:           props.id || '',
    cycle:        cycleString,
    cycle_string: cycleString,
    scenario:     scenarioName,
    duration:     (state.currentScenario && state.currentScenario.duration) || '',
    model_name:   props.model_name || '',
    mllw:         props.mllw || '',
    obsfile:      props.obs_file || '',
    prdfile:      props.prd_file || '',
    ensemble:     props.model_ensemble || '',
  });
  return 'html/timeseries.html?' + params.toString();
}

function bindTimeseriesPopup(layer, plotType, props, scenarioName, cycleString) {
  const url = timeseriesUrl(plotType, props, scenarioName, cycleString);
  layer.bindPopup(
    L.popup({ maxWidth: 'auto' }).setContent(
      '<iframe src="' + url + '" width="730" height="500" frameborder="0"></iframe>',
    ),
  );
}

// --- Spec table ---

const GEOJSON_SPECS = {
  extreme_runup_height: {
    filePattern: function (s, c) {
      return cyclePath(s, c, 'extreme_runup_height/extreme_runup_height.geojson.js');
    },
    globalName: 'runup',
    colorField: 'TWL',
    threshold:  thresholdsRunup,
    radius:     3,
    timeseriesType: 'total_water_level',
    tooltipFields: function (p) { return [
      { label: 'Location nr', value: p.LocNr },
      { label: 'Latitude',    value: fmt(p.Lat, 3) + ' °N' },
      { label: 'Longitude',   value: fmt(p.Lon, 3) + ' °E' },
      { label: 'TWL',         value: p.TWL + ' m above MSL' },
    ]; },
  },

  extreme_horizontal_runup_height: {
    filePattern: function (s, c) {
      return cyclePath(s, c, 'extreme_horizontal_runup_height/extreme_horizontal_runup_height.geojson.js');
    },
    globalName: 'runup_vert',
    colorField: 'TWL',
    threshold:  thresholdsRunup,
    radius:     3,
    tooltipFields: function (p) { return [
      { label: 'Location nr', value: p.LocNr },
      { label: 'Latitude',    value: fmt(p.Lat, 3) + ' °N' },
      { label: 'Longitude',   value: fmt(p.Lon, 3) + ' °E' },
      { label: 'TWL',         value: p.TWL + ' m above MSL' },
    ]; },
  },

  extreme_runup_height_prc95: {
    filePattern: function (s, c) {
      return cyclePath(s, c, 'extreme_runup_height_prc95/extreme_runup_height_prc95.geojson.js');
    },
    globalName: 'runup_prc95',
    colorField: 'TWL',
    threshold:  thresholdsRunup,
    radius:     3,
    timeseriesType: 'total_water_level_prob',
    tooltipFields: function (p) { return [
      { label: 'Location nr', value: p.LocNr },
      { label: 'Latitude',    value: fmt(p.Lat, 3) + ' °N' },
      { label: 'Longitude',   value: fmt(p.Lon, 3) + ' °E' },
      { label: 'TWL',         value: p.TWL + ' m above MSL' },
    ]; },
  },

  extreme_sea_level_and_wave_height: {
    filePattern: function (s, c) {
      return cyclePath(s, c, 'extreme_sea_level_and_wave_height/extreme_sea_level_and_wave_height.geojson.js');
    },
    globalName:  'swl',
    colorField:  null,
    threshold:   function () { return 'blue'; },
    radius:      3,
    fillOpacity: 0.25,
    tooltipFields: function (p) { return [
      { label: 'Location nr',             value: p.LocNr },
      { label: 'Latitude',                value: p.Lat + ' °N' },
      { label: 'Longitude',               value: p.Lon + ' °E' },
      { label: 'Significant wave height', value: p.Hs + ' m' },
      { label: 'Peak wave period',        value: p.Tp + ' s' },
      { label: 'Still Water Level',       value: p.WL + ' m above MSL' },
    ]; },
  },

  estimated_total_water_level: {
    filePattern: function (s, c) {
      return cyclePath(s, c, 'estimated_total_water_level.geojson.js');
    },
    globalName: 'etwl',
    colorField: 'TWLminusHAT',
    threshold:  thresholdsRunup,
    radius:     5,
    timeseriesType: 'estimated_total_water_level',
    tooltipFields: function (p) { return [
      { label: 'TWL',       value: p.TWL + ' m above MSL' },
      { label: 'HAT',       value: p.HAT + ' m above MSL' },
      { label: 'TWL − HAT', value: p.TWLminusHAT + ' m' },
    ]; },
  },

  track_ensemble: {
    filePattern: function (s, c) { return cyclePath(s, c, 'ensemble.geojson.js'); },
    globalName:  'track_ens',
    isLineStyle: true,
    lineStyle:   { color: 'white', opacity: 0.5, weight: 1 },
    tooltipFields: function (p) { return [{ label: 'ID', value: p.id }]; },
  },
};

// --- Layer factory ---

function makeGeoJsonLayer(specName, scenarioName, cycleString) {
  const spec = GEOJSON_SPECS[specName];
  if (!spec) throw new Error('Unknown geojson spec: ' + specName);

  const layerOpts = spec.isLineStyle
    ? { style: spec.lineStyle, onEachFeature: bindTooltip(spec) }
    : {
        pointToLayer:  makePointFactory(spec),
        onEachFeature: bindTooltip(spec, scenarioName, cycleString),
      };
  const layer = L.geoJson(undefined, layerOpts);

  loadGlobal(spec.filePattern(scenarioName, cycleString), spec.globalName)
    .then(function (data) { if (data) layer.addData(data); })
    .catch(function (err) { console.warn(err.message); });

  return layer;
}

function makePointFactory(spec) {
  return function (feature, latlng) {
    return L.circleMarker(latlng, {
      radius:      spec.radius,
      fillOpacity: spec.fillOpacity != null ? spec.fillOpacity : 0.7,
      opacity:     0,
      color:       spec.colorField
        ? spec.threshold(feature.properties[spec.colorField])
        : spec.threshold(),
    });
  };
}

function bindTooltip(spec, scenarioName, cycleString) {
  return function (feature, layer) {
    const html = tooltipHtml(spec.tooltipFields(feature.properties));
    layer.bindTooltip(L.tooltip({ direction: 'top' }).setContent(html));
    if (spec.timeseriesType) {
      bindTimeseriesPopup(layer, spec.timeseriesType, feature.properties,
                          scenarioName, cycleString);
    } else {
      layer.bindPopup(html);
    }
  };
}

cosmos.layers.geojson = { GEOJSON_SPECS, makeGeoJsonLayer };

})();
