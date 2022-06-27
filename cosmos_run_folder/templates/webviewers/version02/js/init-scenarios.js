var currentScenario
var currentVariable
var currentLayer
var controlLegend
var currentTime = 0
var stations
var buoys

function loadjs(file_name, callback, failed) {

  let myScript = document.createElement("script");
  myScript.setAttribute("src", file_name);
  myScript.addEventListener("load", callback, false);
  myScript.addEventListener("error", failed, false);
  document.body.appendChild(myScript);
  console.log('request sent');

}


// Read in scenarios
loadjs("data/scenarios.js", scenariosLoaded, scenarioLoadError);

function scenarioLoadError() {
	console.log('Error! Could not load data/scenarios.js !');
}

function variableLoadError() {
	console.log('Error! Could not load variables !');
}

function stationsLoadError() {
	console.log('Error! Could not load stations !');
	stations = null;
	addStations();
}

function buoysLoadError() {
	console.log('Error! Could not load wave buoys !');
	buoys = null;
	addBuoys();
}

function scenariosLoaded() {

  console.log(scenario.length.toString() + " scenarios found !");

  currentScenario = scenario[0]
  console.log("Active scenario is " + currentScenario["name"]);

  var fieldset    = document.getElementById('scenarios');

  // Clear existing fieldset (legend + listbox)
  while (fieldset.hasChildNodes()) {
    fieldset.removeChild(fieldset.firstChild);
  }

  // Add legend
  var newLegend = document.createElement('legend');
  newLegend.innerHTML = "Storm Scenario";
  fieldset.appendChild(newLegend);

  // Listbox
  newSelect = document.createElement('select');
  newSelect.addEventListener("change", function(){changeScenario(this);});
  for (let i = 0; i < scenario.length; i++) {
      var newOption = document.createElement('option');
      var newInput = document.createElement('input');
      newInput.type       = "radio";
      newInput.id         = "";
      newInput.name       = "optionsLayer";
      newOption.value     = scenario[i].name;
      newOption.innerHTML = scenario[i].long_name;
      newSelect.appendChild(newOption);
  }

  fieldset.appendChild(newSelect);

  selectScenario();

}

function selectScenario() {
  // Read map variables
  loadjs("data/" + currentScenario["name"] + "/variables.js", variablesLoaded, variableLoadError);
  // Add tide stations
  loadjs("data/" + currentScenario["name"] + "/stations.geojson.js", addStations, stationsLoadError);
  // Add tide stations
  loadjs("data/" + currentScenario["name"] + "/wavebuoys.geojson.js", addBuoys, buoysLoadError);
  // Set new zoom
  map.setView([currentScenario["lat"], currentScenario["lon"]], currentScenario["zoom"]);
  document.getElementById("status_text").innerHTML = "Updated : " + currentScenario["last_update"];
}


function selectMode() {
	console.log('Selected ' + currentMode);
}

function variablesLoaded() {

  console.log("Finished reading the variables in scenario " + currentScenario["long_name"]);
  currentScenario["variable"] = map_variables
  currentVariable = currentScenario["variable"][0]

  // Make map layers

  layers = {};

  for (let i = 0; i < currentScenario["variable"].length; i++) {

	var variable_format = currentScenario["variable"][i].format
	var variable_name   = currentScenario["variable"][i].name
	if (currentScenario["variable"][i].times !== undefined) {
	  var times           = currentScenario["variable"][i].times
	  var ntimes          = times.length
    }

    else {
		var ntimes = 0
    }

    console.log("Making map layer : " + currentScenario["variable"][i].long_name);

    if (variable_format == "xyz_tile_layer") {
		layers[variable_name] = new Array()
		if (ntimes>0) {
            for (let j = 0; j < ntimes; j++) {
        		time_string = times[j]["name"]
                this_layer = L.tileLayer("data/" + currentScenario["name"] + '/' + variable_name + "/" + time_string + "/{z}/{x}/{-y}.png", layerOptions);
                layers[variable_name].push(this_layer);
            }
        }

        else {
            this_layer = L.tileLayer("data/" + currentScenario["name"] + '/' + variable_name + "/{z}/{x}/{-y}.png", layerOptions);
            layers[variable_name].push(this_layer);
        }

    }

    else if (variable_format == "geojson") {

		// Quite a few different options for geojson layers

		if (variable_name == 'extreme_runup_height') {
			makeExtremeRunupLayer();
	    }
	    else if (variable_name == 'extreme_sea_level_and_wave_height') {
			makeExtremeSWLLayer();
     	}
    }
  }

  var fieldset= document.getElementById('variables');

  // Clear existing fieldset (legend + variables)
  while (fieldset.hasChildNodes()) {
    fieldset.removeChild(fieldset.firstChild);
  }

  var newLegend = document.createElement('legend');
  newLegend.innerHTML = "Variables";
  fieldset.appendChild(newLegend);

  for (let i = 0; i < currentScenario["variable"].length; i++) {

      var newLabel = document.createElement('label');

      var newInput = document.createElement('input');
      newInput.type      = "radio";
      newInput.id        = "";
      newInput.name      = "optionsLayer";
      newInput.value     = currentScenario["variable"][i].name;
      newInput.addEventListener("change", function(){changeVariable(this);});
      if (i==0) {newInput.checked = true}

      newLabel.htmlFor = currentScenario["variable"][i].name;
      newLabel.setAttribute("class", "pure-radio");
      newLabel.appendChild(newInput);
      var newText = document.createTextNode(" " + currentScenario["variable"][i].long_name);
      newLabel.appendChild(newText);

      fieldset.appendChild(newLabel);

  }

  selectVariable();

}

function variableLoadError() {
	console.log('Could not load variables.js!')
}

function selectVariable() {

    setTimes();

}


function setTimes() {

  var fieldset    = document.getElementById('times');

  // Clear existing fieldset (legend + listbox)
  while (fieldset.hasChildNodes()) {
    fieldset.removeChild(fieldset.firstChild);
  }

  // Add legend
  var newLegend = document.createElement('legend');
  newLegend.innerHTML = "Times";
  fieldset.appendChild(newLegend);

  // Listbox
  newSelect = document.createElement('select');
  newSelect.addEventListener("change", function(){changeTime(this);});
  for (let i = 0; i < layers[currentVariable["name"]].length; i++) {
      var newOption = document.createElement('option');
      newOption.value     = i;
      newOption.innerHTML = i;
      newSelect.appendChild(newOption);
  }

  fieldset.appendChild(newSelect);

  currentTime = 0;

  selectTime();

}

function selectTime() {

//    oldLayer = currentLayer
    // Remove current layer
    if (currentLayer) {
      map.removeLayer(currentLayer);
      if (controlLegend) {
        controlLegend.remove();
      }
    }

    // Set new currentLayer
    currentLayer = layers[currentVariable["name"]][currentTime];

    // Add layer
    if (currentLayer) {

      map.addLayer(currentLayer);

      if (currentVariable["legend"]["contours"]) {

      // Add legend
      controlLegend = L.control({
        position: 'bottomright'
      });
      controlLegend.onAdd = function (map) {
        const div = L.DomUtil.create('div', 'info legend');
        var newSpan = document.createElement('span');
        newSpan.class = 'title';
        newSpan.innerHTML = '<b>' + currentVariable["legend"]["text"] + '</b>';
        div.appendChild(newSpan);
        div.appendChild(document.createElement("br"));
        for (let i = 0; i < currentVariable["legend"]["contours"].length; i++) {

            var newI = document.createElement('i');
            newI.setAttribute('style','background:' + currentVariable["legend"]["contours"][i].color);
            div.appendChild(newI);
            var newSpan = document.createElement('span');
            newSpan.innerHTML = currentVariable["legend"]["contours"][i].text;
            div.appendChild(newSpan);
            div.appendChild(document.createElement("br"));
  	    }
        return div;
      };

      controlLegend.addTo(map);
      }


    }

//    // Remove current layer
//    if (oldLayer) {
//      map.removeLayer(oldLayer);
//    }

}

// Called when scenario is selected from web gui
let changeScenario = function(element) {
  var name = element.value;
  currentScenario = scenario.find(x => x.name === name);
  selectScenario();
}

// Called when best track of ensemble is selected from web gui
let changeMode = function(element) {
  var name = element.getAttribute("value");
  currentMode = element.getAttribute("value");
  selectMode();
}

// Called when scenario is selected from web gui
let changeVariable = function(element) {
  var name = element.getAttribute("value");
  currentVariable = currentScenario["variable"].find(x => x.name === name);
  selectVariable();
}

// Called when scenario is selected from web gui
let changeTime = function(element) {
  var name = element.value;
  currentTime = element.value;
  selectTime();
}

