// layers/cyclone.js — cosmos.layers.cyclone
// Cyclone deterministic track (per-point markers with category-coded icons)
// and ensemble-track lines.

(function () {

const { ICONS } = cosmos.config;
const { state } = cosmos;
const { tryLoadGlobal, cyclePath } = cosmos.loaders;

function trackPointTooltip(props) {
  const vmaxUnit = props.vmax_unit || 'knots';
  const vmaxStr  = props.vmax != null ? props.vmax.toFixed(0) : 'NA';
  const pcStr    = props.pc   != null ? props.pc.toFixed(0)   : 'NA';
  return [
    'Time: '      + props.time,
    'Category: '  + props.category,
    'Latitude: '  + props.lat.toFixed(1),
    'Longitude: ' + props.lon.toFixed(1),
    'Vmax: '      + vmaxStr + ' ' + vmaxUnit,
    'Pressure: '  + pcStr   + ' hPa',
  ].map(function (s) { return s + '<br/>'; }).join('');
}

// --- Deterministic best-track ---

async function addCycloneTrack() {
  if (state.markers.cycloneTrack) state.markers.cycloneTrack.remove();
  const data = await tryLoadGlobal(
    cyclePath(state.currentScenario.name, state.currentCycle, 'track.geojson.js'),
    'track_data',
  );
  if (!data) return;

  state.markers.cycloneTrack = L.geoJson(data, {
    onEachFeature: function (feature, layer) {
      // The track line itself is feature.id === '0' — skip its tooltip; only
      // attach details to the per-time-step Point features.
      if (feature.id === '0' || feature.geometry.type !== 'Point') return;
      const html = trackPointTooltip(feature.properties);
      layer.bindTooltip(L.tooltip({ direction: 'top' }).setContent(html));
      layer.bindPopup(html);
    },
    pointToLayer: function (feature, latlng) {
      const icon = ICONS[feature.properties.category] || ICONS.TD;
      return L.marker(latlng, { icon: icon });
    },
  });
  state.markers.cycloneTrack.addTo(state.map);
}

// --- Ensemble tracks (thin white lines) ---

async function addCycloneTrackEnsemble() {
  if (state.markers.cycloneEnsemble) state.markers.cycloneEnsemble.remove();
  const data = await tryLoadGlobal(
    cyclePath(state.currentScenario.name, state.currentCycle, 'track_ensemble.geojson.js'),
    'track_ensemble_data',
  );
  if (!data) return;

  state.markers.cycloneEnsemble = L.geoJson(data, {
    style: { color: 'white', weight: 1, opacity: 0.4 },
  });
  state.markers.cycloneEnsemble.addTo(state.map);
}

cosmos.layers.cyclone = { addCycloneTrack, addCycloneTrackEnsemble };

})();
