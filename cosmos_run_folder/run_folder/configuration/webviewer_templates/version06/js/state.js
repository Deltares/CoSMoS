// state.js
// Single mutable state object shared by all modules. Replaces the ~17 loose
// `var` globals used in version05's init-scenarios.js / init-stations.js.
//
// Convention: modules read from `cosmos.state` but only main.js and the
// scenario/variable/time selection flow mutate the "current" pointers.

cosmos.state = {
  // The Leaflet map itself. Assigned by main.js after the map is created.
  map: null,

  // Currently selected scenario / cycle / variable / animation frame.
  currentScenario: null,
  currentCycle:    null,
  currentVariable: null,
  currentTime:     0,
  previousTime:   -1,

  // The Leaflet layer currently visible on the map.
  currentLayer: null,

  // Map legend (bottom right) and the icon legend (top left).
  controlLegend: null,
  iconLegend:    null,

  // Animation timeout id, for the play/pause buttons.
  animationTimeout: null,

  // Variable-name → array of Leaflet layers. For time-stepped variables, the
  // array index is the frame; otherwise it has a single entry at index 0.
  layers: {},

  // Persistent marker / outline overlays, kept across variable changes.
  markers: {
    tideGauges:      null,
    waveBuoys:       null,
    xbeach:          null,
    modelOutlines:   null,
    cycloneTrack:    null,
    cycloneEnsemble: null,
  },

  // Wind layer needs peak velocity to size the animated particles. Set by
  // variablesLoaded() from the variables.js manifest.
  maxWindVelocity: null,
};
