// ui/panel.js — cosmos.ui.panel
// Right-hand side panel: scenario picker, cycle picker, variable list,
// time-step slider and play/pause controls. Pure DOM construction —
// callbacks are passed in from main.js, which owns the selection flow.

(function () {

function clear(el) {
  while (el.firstChild) el.removeChild(el.firstChild);
}

/** Build the Storm Scenario fieldset. */
function renderScenarioPicker(scenarios, onChange) {
  const fieldset = document.getElementById('scenarios');
  clear(fieldset);

  const legend = document.createElement('legend');
  legend.textContent = 'Storm Scenario';
  fieldset.appendChild(legend);

  const select = document.createElement('select');
  select.addEventListener('change', function (e) { onChange(e.target.value); });
  scenarios.forEach(function (s) {
    const opt = document.createElement('option');
    opt.value = s.name;
    opt.textContent = s.long_name;
    select.appendChild(opt);
  });
  fieldset.appendChild(select);
}

/**
 * Build (or rebuild) the cycle picker inside the Storm Scenario fieldset.
 * Only appears for scenarios with multiple cycles. Removes any existing
 * picker first.
 */
function renderCyclePicker(scenario, onChange) {
  const existing = document.getElementById('cycle_selector');
  if (existing) existing.remove();
  if (!scenario.previous_cycles) return;

  const select = document.createElement('select');
  select.id = 'cycle_selector';
  select.addEventListener('change', function (e) { onChange(e.target.value); });
  scenario.previous_cycles.forEach(function (cycle) {
    const opt = document.createElement('option');
    opt.value = cycle;
    opt.textContent = cycle;
    select.appendChild(opt);
  });
  document.getElementById('scenarios').appendChild(select);
}

/** Build the Map layers fieldset (radio buttons, one per variable). */
function renderVariablePicker(variables, onChange) {
  const fieldset = document.getElementById('variables');
  clear(fieldset);

  const legend = document.createElement('legend');
  legend.textContent = 'Map layers';
  fieldset.appendChild(legend);

  variables.forEach(function (v, i) {
    const label = document.createElement('label');
    label.className = 'pure-radio';
    label.htmlFor = v.name;

    const input = document.createElement('input');
    input.type    = 'radio';
    input.id      = 'variable_' + v.name;
    input.name    = 'optionsLayer';
    input.value   = v.name;
    input.checked = i === 0;
    input.addEventListener('change', function () { onChange(v.name); });
    // Wind is re-enabled by layers/wind.js once its data has loaded.
    if (v.name === 'wind') input.disabled = true;

    label.appendChild(input);
    label.appendChild(document.createTextNode(' ' + v.long_name));
    fieldset.appendChild(label);
  });
}

/**
 * Build the time-step selector + play/pause buttons. Returns early if the
 * variable is not time-stepped, in which case the fieldset is left empty.
 */
function renderTimePicker(variable, onChange, onPlay, onPause) {
  const fieldset = document.getElementById('times');
  clear(fieldset);
  if (!variable.times || variable.times.length === 0) return;

  const legend = document.createElement('legend');
  legend.textContent = 'Times';
  fieldset.appendChild(legend);

  const select = document.createElement('select');
  select.id = 'timeselector';
  select.className = 'timeselector';
  select.addEventListener('change', function (e) { onChange(Number(e.target.value)); });
  variable.times.forEach(function (t, i) {
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = t.string || t.name;
    select.appendChild(opt);
  });
  fieldset.appendChild(select);

  fieldset.appendChild(makeButton('fa-play',  onPlay));
  fieldset.appendChild(makeButton('fa-pause', onPause));
}

function makeButton(faClass, onClick) {
  const btn = document.createElement('button');
  btn.innerHTML = '<i class="fa ' + faClass + '"></i>';
  btn.style.padding = '5px';
  btn.style.marginLeft = '5px';
  btn.addEventListener('click', onClick);
  return btn;
}

/** Set the status line at the bottom of the page. */
function renderStatus(scenario, cycle) {
  let s = 'Updated: ' + scenario.last_update;
  if (cycle)                s += '&nbsp;&nbsp;&nbsp;&nbsp;CoSMoS: ' + cycle;
  if (scenario.meteo_string) s += '&nbsp;&nbsp;&nbsp;&nbsp;meteo: ' + scenario.meteo_string;
  document.getElementById('status_text').innerHTML = s;
}

/** Set the description paragraph below the scenario picker. */
function renderDescription(text) {
  document.getElementById('description_text').textContent = text;
}

cosmos.ui.panel = {
  renderScenarioPicker, renderCyclePicker, renderVariablePicker,
  renderTimePicker, renderStatus, renderDescription,
};

})();
