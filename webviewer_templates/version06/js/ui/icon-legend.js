// ui/icon-legend.js — cosmos.ui.iconLegend
// Top-left legend with checkboxes to toggle marker overlays
// (tide gauges, wave buoys, cyclone track, ensemble tracks).
//
// Each row is described by an OverlayToggle:
//   - label:      text shown next to the marker preview
//   - markerHtml: optional <img> HTML for the marker preview
//   - onShow:     callback when the user re-enables the layer
//   - onHide:     callback when the user disables it
//   - initial:    starting checked state (default true)

(function () {

function makeIconLegend(toggles) {
  const control = L.control({ position: 'topleft' });
  control.onAdd = function () {
    const div = L.DomUtil.create('div', 'info legend');
    // Block click/drag from propagating to the underlying map.
    L.DomEvent.disableClickPropagation(div);
    toggles.forEach(function (t) { div.appendChild(makeRow(t)); });
    return div;
  };
  return control;
}

function makeRow(toggle) {
  const wrapper = document.createElement('div');
  const checkbox = document.createElement('input');
  checkbox.type    = 'checkbox';
  checkbox.checked = toggle.initial != null ? toggle.initial : true;
  checkbox.addEventListener('change', function (e) {
    if (e.currentTarget.checked) toggle.onShow();
    else                          toggle.onHide();
  });
  wrapper.appendChild(checkbox);
  if (toggle.markerHtml) {
    const span = document.createElement('span');
    span.innerHTML = ' ' + toggle.markerHtml + ' ';
    wrapper.appendChild(span);
  }
  wrapper.appendChild(document.createTextNode(toggle.label));
  return wrapper;
}

cosmos.ui.iconLegend = { makeIconLegend };

})();
