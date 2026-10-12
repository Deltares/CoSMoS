// ui/legend.js — cosmos.ui.legend
// Bottom-right map legend showing the contour bands of the current variable.

(function () {

/**
 * Build a Leaflet control for the current variable's legend.
 * Returns null if the variable has no `legend.contours` block (in which case
 * no legend is shown). Caller is responsible for adding/removing from map.
 */
function makeContourLegend(variable) {
  if (!variable.legend || !variable.legend.contours) return null;

  const control = L.control({ position: 'bottomright' });
  control.onAdd = function () {
    const div = L.DomUtil.create('div', 'info legend');
    const title = document.createElement('span');
    title.className = 'title';
    title.innerHTML = '<b>' + variable.legend.text + '</b>';
    div.appendChild(title);
    div.appendChild(document.createElement('br'));

    variable.legend.contours.forEach(function (c) {
      const swatch = document.createElement('i');
      swatch.setAttribute('style', 'background:' + c.color);
      const span = document.createElement('span');
      span.textContent = c.text;
      div.appendChild(swatch);
      div.appendChild(span);
      div.appendChild(document.createElement('br'));
    });

    // Wind layer puts its current time-step here so the user can see which
    // forecast time the animated field corresponds to.
    if (variable.name === 'wind') {
      const timeText = document.createElement('span');
      timeText.id = 'wind_time_string';
      div.appendChild(timeText);
    }
    return div;
  };
  return control;
}

cosmos.ui.legend = { makeContourLegend };

})();
