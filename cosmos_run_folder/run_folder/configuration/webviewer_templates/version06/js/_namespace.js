// _namespace.js
// Create the single global namespace used by every other script in the
// viewer. Must be loaded first.
//
// Layout:
//   window.cosmos = {
//     config:    { ...constants, icons, colour scales },
//     state:     { ...mutable runtime state },
//     loaders:   { loadScript, loadGlobal, tryLoadGlobal, cyclePath },
//     layers:    { tile, geojson, wind, stations, cyclone },
//     ui:        { panel, legend, iconLegend },
//     timeseries:{ core, plotTypes },
//   };
//
// Each module assigns its exports to the appropriate sub-namespace at the
// end of its file. Inside the module body we destructure dependencies up
// front so the rest of the code reads as if `import` had happened.

window.cosmos = window.cosmos || {};
window.cosmos.layers     = window.cosmos.layers     || {};
window.cosmos.ui         = window.cosmos.ui         || {};
window.cosmos.timeseries = window.cosmos.timeseries || {};
