// config.js
// Static configuration: colour scales, default layer options, and the icon
// registry. Pure data — no DOM access. Attached to cosmos.config.

(function () {

// Wind speed colour ramp for the leaflet-velocity wind layer.
// Index 0 = lowest speed, last = highest.
const WIND_COLOR_SCALE = [
  'rgb(0,255,255)',  'rgb(61,255,195)', 'rgb(122,255,134)', 'rgb(182,255,73)',
  'rgb(243,255,12)', 'rgb(255,239,0)',  'rgb(255,219,0)',   'rgb(255,199,0)',
  'rgb(255,178,0)',  'rgb(255,158,0)',  'rgb(255,138,0)',   'rgb(255,116,12)',
  'rgb(255,91,37)',  'rgb(255,67,61)',  'rgb(255,43,85)',   'rgb(255,18,110)',
  'rgb(248,0,127)',  'rgb(218,0,121)',  'rgb(189,0,116)',   'rgb(159,0,111)',
  'rgb(130,0,105)',  'rgb(100,0,100)',
];

// Coastal vulnerability index colours (low → very high).
const CVI_COLORS = ['#00ff00', '#ffff00', '#ffa500', '#ff0000'];

// Default options for raster tile layers emitted by CoSMoS.
// `maxNativeZoom` is per-variable and overridden in layers/tile.js.
const TILE_LAYER_DEFAULTS = {
  detectRetina: false,
  opacity: 0.7,
  maxZoom: 22,
  minZoom: 0,
  noWrap: false,
  subdomains: 'abc',
  zIndex: 10,
  tms: false,
};

// Base map definitions. Realised as Leaflet tile layers in layers/tile.js.
const BASE_MAPS = {
  esri: {
    label: 'Esri WorldImagery',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    options: {
      attribution: 'Tiles © Esri — Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
      opacity: 0.8, maxNativeZoom: 19, maxZoom: 19, minZoom: 0,
    },
  },
  osm: {
    label: 'OpenStreetMap',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    options: {
      attribution: '© <a href="https://openstreetmap.org">OpenStreetMap</a>, <a href="http://www.openstreetmap.org/copyright">ODbL</a>',
      opacity: 0.8, maxNativeZoom: 19, maxZoom: 19, minZoom: 0,
      subdomains: 'abc',
    },
  },
  cartodb: {
    label: 'CartoDB',
    url: 'https://cartodb-basemaps-{s}.global.ssl.fastly.net/rastertiles/voyager/{z}/{x}/{y}.png',
    options: {
      attribution: '© <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> © <a href="http://cartodb.com/attributions">CartoDB</a>',
      opacity: 0.8, maxNativeZoom: 19, maxZoom: 19, minZoom: 0,
      subdomains: 'abc',
    },
  },
};

// Icon factories. Cyclone-category icons are keyed by the `category` string
// emitted in track GeoJSONs ("TD", "TS", "1".."5" plus Philippine "STS",
// "TY", "STY").
const makeIcon = (url, size, opts = {}) => L.icon({
  iconUrl: `img/markers/${url}`,
  iconSize:    [size, size],
  iconAnchor:  [size / 2, size / 2],
  popupAnchor: [size / 2, size / 2],
  ...opts,
});

const makeCycloneIcon = (url) => L.icon({
  iconUrl: `img/markers/${url}`,
  iconSize:    [16, 32],
  iconAnchor:  [8, 16],
  popupAnchor: [8, 16],
});

const ICONS = {
  tide_gauge: makeIcon('tide_gauge.png', 16),
  wave_buoy:  makeIcon('wave_buoy.png',  16),
  xbeach:     makeIcon('erosion_marker_rw.png', 24),

  TD:  makeCycloneIcon('Tropical_depression_icon_c2.png'),
  TS:  makeCycloneIcon('Tropical_storm_icon_c2.png'),
  '1': makeCycloneIcon('Category_1_hurricane_icon_c2.png'),
  '2': makeCycloneIcon('Category_2_hurricane_icon_c2.png'),
  '3': makeCycloneIcon('Category_3_hurricane_icon_c2.png'),
  '4': makeCycloneIcon('Category_4_hurricane_icon_c2.png'),
  '5': makeCycloneIcon('Category_5_hurricane_icon_c2.png'),
  STS: makeCycloneIcon('severe_tropical_storm_icon.png'),
  TY:  makeCycloneIcon('typhoon_icon.png'),
  STY: makeCycloneIcon('super_typhoon_icon.png'),
};

// Time between successive frames in the time-step animation (ms).
const ANIMATION_FRAME_MS = 500;
// Delay before removing the previous tile layer — smooths flicker.
const LAYER_SWAP_DELAY_MS = 200;

cosmos.config = {
  WIND_COLOR_SCALE, CVI_COLORS, TILE_LAYER_DEFAULTS, BASE_MAPS, ICONS,
  ANIMATION_FRAME_MS, LAYER_SWAP_DELAY_MS,
};

})();
