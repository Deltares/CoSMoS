.. _webviewer:

Web viewer
----------

CoSMoS presents its results in an interactive web viewer: a map with flood,
water level, and wave layers, cyclone tracks, and time series at the
observation stations. The web viewer is a static website (HTML and
JavaScript) that CoSMoS fills with data after each cycle. It does not need a
web server to run; it can be opened from disk or copied to any web server.

Setting up a web viewer
^^^^^^^^^^^^^^^^^^^^^^^

The web viewer is set in the ``[webviewer]`` section of the
:ref:`configuration file <configuration>`:

.. code-block:: toml

    [webviewer]
    name    = "my_viewer"
    version = "version06"

- ``name`` is the name of the web viewer folder: ``webviewers/<name>`` in the
  run folder. One web viewer can show several scenarios.
- ``version`` is the template that is used, from the ``webviewer_templates``
  folder in the CoSMoS repository. Use the most recent version,
  ``version06``. Older versions do not show all current output.

The first time CoSMoS runs with a new web viewer name, it copies the template
to ``webviewers/<name>``. After that, the existing folder is reused and only
the data is updated. To switch to another template version, delete the web
viewer folder (or use a new name), so that the new template is copied.

Viewing the results
^^^^^^^^^^^^^^^^^^^

Open ``webviewers/<name>/index.html`` in a web browser. Select the scenario and
cycle, and switch map layers on and off in the panel. Click a station to see
its time series.

An internet connection is needed for the background maps and for the
observed water levels at NOAA CO-OPS stations (see
:ref:`Observation stations <stations>`).

Publishing the web viewer
^^^^^^^^^^^^^^^^^^^^^^^^^

With ``upload = true`` in the ``[run]`` section of the configuration file,
CoSMoS publishes the web viewer after each cycle:

- in ``serial`` and ``parallel`` run mode, it copies the web viewer to the
  folder set in ``[webserver] path``;
- in ``cloud`` run mode, it uploads the data to AWS S3.

Folder structure
^^^^^^^^^^^^^^^^

.. code-block:: text

    webviewers
    └── <name>
        ├── index.html
        ├── css
        ├── html
        ├── img
        ├── js
        └── data
            ├── scenarios.js
            └── <scenario_name>
                └── <cycle>
                    ├── variables.js
                    ├── stations.geojson.js
                    ├── wavebuoys.geojson.js
                    ├── track.geojson.js
                    ├── track_ensemble.geojson.js
                    ├── timeseries
                    ├── flood_map
                    ├── water_level
                    ├── hm0
                    └── ...

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - File or folder
     - Description

   * - ``index.html``
     - Open this file to view the web viewer.

   * - ``css``, ``html``, ``img``, ``js``
     - The web viewer itself, copied from the template.

   * - ``data/scenarios.js``
     - List of all scenarios and cycles in the web viewer, with their names
       and initial map view.

   * - ``data/<scenario>/<cycle>/variables.js``
     - The map layers available for this cycle, with their legends.

   * - ``stations.geojson.js``, ``wavebuoys.geojson.js``
     - Locations of the water level stations and wave buoys with model
       results.

   * - ``track.geojson.js``, ``track_ensemble.geojson.js``
     - Cyclone track and ensemble tracks (if any).

   * - ``timeseries``
     - Model and observation time series at the stations.

   * - ``flood_map``, ``water_level``, ``storm_surge``, ``hm0``,
       ``precipitation``, ...
     - Map tiles for each layer. Ensemble results get ``_90`` added to the
       name (e.g. ``flood_map_90``).

The data files are JavaScript files that assign the data to a variable (for
example ``var scenario = ...``). This lets the web viewer load them directly
from disk, without a web server.

Which map layers appear depends on the ``make_*_maps`` settings in the
configuration file and the ``make_*_map`` settings in ``model.toml`` (see
:ref:`Model database <models>`).