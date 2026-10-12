.. _scenario:

Scenario configuration
----------------------

A scenario file defines which models to run, for which period, and with which
meteorological forcing. It is a TOML file located at
``scenarios/<scenario_name>/scenario.toml`` in the run folder. The scenario
name is the name of this folder (see :ref:`Folder structure <folder_structure>`).

A scenario file consists of:

- general settings at the top of the file (see the tables below);
- one or more ``[[model]]`` sections that select the models to run
  (see :ref:`Selecting models <scenario_models>`);
- optionally, ``[[station]]`` sections that add observation stations
  (see :ref:`Adding stations <scenario_stations>`);
- optionally, ``[[cluster]]`` sections that only run the models where high
  water levels are expected (see :ref:`Model clusters <scenario_clusters>`).

Examples
^^^^^^^^

A deterministic hindcast of Hurricane Laura with gridded meteorological data:

.. code-block:: toml

    long_name     = "Hurricane Laura"
    cycle         = "20200826_00z"
    runtime       = 24
    meteo_dataset = "gfs_analysis_0p50_north_atlantic"
    lon           = -93.0
    lat           = 29.5
    zoom          = 7

    [[model]]
    name = "sfincs_gulf_500m"

    [[model]]
    name = "sfincs_gulf_0002"

A track ensemble for Hurricane Maria, using a track file and all SFINCS,
HurryWave, and BEWARE models in a super region and a region:

.. code-block:: toml

    long_name                      = "Hurricane Maria ensemble"
    cycle                          = "20170919_00z"
    runtime                        = 72
    meteo_track                    = "maria"
    run_ensemble                   = true
    track_ensemble_nr_realizations = 10
    observations_path              = "hurricane_maria"
    lon                            = -66.5
    lat                            = 18.2
    zoom                           = 10

    [[model]]
    super_region = "north_atlantic"
    type         = ["hurrywave", "sfincs", "beware"]

    [[model]]
    region = "puerto_rico"
    type   = ["sfincs"]

General settings
^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 30 50 10 10
   :header-rows: 1

   * - Parameter
     - Description
     - Default
     - Unit

   * - runtime
     - Simulation duration from the cycle time. Required.
     -
     - hours

   * - cycle
     - Cycle time as a string (e.g. ``"20200826_00z"``). If omitted, and no
       cycle is given when running CoSMoS, the current time is used (see
       :ref:`Running CoSMoS <running>`).
     -
     -

   * - long_name
     - Display name shown in the web viewer.
     - scenario name
     -

   * - description
     - Textual description of the scenario, shown in the web viewer.
     - scenario name
     -

Web viewer settings
^^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 30 50 10 10
   :header-rows: 1

   * - Parameter
     - Description
     - Default
     - Unit

   * - lon, lat
     - Initial map centre in the web viewer.
     - from configuration file
     - degrees

   * - zoom
     - Initial map zoom level in the web viewer.
     - from configuration file
     -

   * - observations_path
     - Name of the sub-folder in ``observations`` with manually provided
       observation files (see :ref:`Observation stations <stations>`).
     - None
     -

Meteorological forcing
^^^^^^^^^^^^^^^^^^^^^^

These settings apply to all models in the scenario. See
:ref:`Meteorological forcing <meteo>` for details.

.. list-table::
   :widths: 30 50 10 10
   :header-rows: 1

   * - Parameter
     - Description
     - Default
     - Unit

   * - meteo_dataset
     - Name of a gridded dataset in ``meteo_database.toml``.
     - None
     -

   * - meteo_track
     - Name, without extension, of a ``.cyc`` track file in the ``tracks``
       folder of the meteo database.
     - None
     -

   * - cyclone_track_forecast_source
     - Use forecast tracks from this source. Currently ``"jtwc"``.
     - None
     -

   * - cyclone_track_forecast_area_file
     - GeoJSON file in ``configuration/areas`` with a polygon, used to select
       the JTWC track.
     - None
     -

   * - meteo_wind
     - Apply wind forcing.
     - true
     -

   * - meteo_atmospheric_pressure
     - Apply atmospheric pressure forcing.
     - true
     -

   * - meteo_precipitation
     - Apply precipitation forcing.
     - true
     -

Track ensemble
^^^^^^^^^^^^^^

See :ref:`Track ensemble <meteo_ensemble>` for details.

.. list-table::
   :widths: 30 50 10 10
   :header-rows: 1

   * - Parameter
     - Description
     - Default
     - Unit

   * - run_ensemble
     - Run a track ensemble.
     - false
     -

   * - track_ensemble_nr_realizations
     - Number of synthetic tracks.
     - from configuration file
     -

   * - ensemble_models
     - Model types to run as an ensemble.
     - from configuration file
     -

Tsunami
^^^^^^^

For tsunami events (``event_mode = "tsunami"`` in the
:ref:`configuration file <configuration>`), the initial water level is computed
from an earthquake source.

.. list-table::
   :widths: 30 50 10 10
   :header-rows: 1

   * - Parameter
     - Description
     - Default
     - Unit

   * - finite_fault_file
     - Earthquake finite fault file, as an absolute path or a file name in the
       ``tsunami`` folder of the scenario.
     - None
     -

.. _scenario_models:

Selecting models
^^^^^^^^^^^^^^^^

Models are added with ``[[model]]`` sections. Each section either selects one
model by name, or all models of the given types in a region or super region.

.. list-table::
   :widths: 25 65 10
   :header-rows: 1

   * - Parameter
     - Description
     - Type

   * - name
     - Name of one model (the folder name in the model database).
     - string

   * - region
     - Select all models in this region (the ``<region>`` folder in the model
       database). Requires ``type``.
     - string

   * - super_region
     - Select all models in the regions of this super region (see
       :ref:`Regions and super regions <super_regions>`). Requires ``type``.
     - string

   * - type
     - Model types to select: ``sfincs``, ``hurrywave``, ``delft3dfm``,
       ``xbeach``, ``beware``.
     - list

   * - meteo_dataset, meteo_track
     - Use different meteorological forcing for the models in this section.
     - string

A model can be selected by more than one section; it is then included once.
Make sure that the parent models of nested models (``flow_nested``,
``wave_nested`` in ``model.toml``) are also part of the scenario, otherwise
:ref:`validation <running>` stops the run.

.. _scenario_stations:

Adding stations
^^^^^^^^^^^^^^^

Observation stations are normally set per model in ``model.toml``. With a
``[[station]]`` section, a station file is added to models for this scenario
only:

.. code-block:: toml

    [[station]]
    name       = "usgs_fev_waterlevels_hurricane_michael.toml"
    model_type = ["sfincs"]

.. list-table::
   :widths: 25 65 10
   :header-rows: 1

   * - Parameter
     - Description
     - Type

   * - name
     - Station file in ``configuration/stations``.
     - string

   * - model_type
     - Add the stations to all models of these types.
     - list

   * - model_name
     - Add the stations to these models.
     - list

See :ref:`Observation stations <stations>` for the station file format.

.. _scenario_clusters:

Model clusters
^^^^^^^^^^^^^^

For large model databases, it is often not necessary to run all detailed
models in every cycle. A cluster groups nested models and only runs the models
where the highest water levels are expected. When all parent models have
finished, CoSMoS estimates the peak total water level at the boundary of each
model in the cluster:

    total water level = water level + ``hm0fac`` × wave height − ``mhhw``

Only models where this level exceeds ``boundary_twl_treshold`` (set in
``model.toml``) plus ``boundary_twl_margin`` are run, and at most ``topn``
of them, starting with the highest. Only nested models (with ``flow_nested``
or ``wave_nested``) can be part of a cluster.

.. code-block:: toml

    [[cluster]]
    name         = "gulf_coast_flood_models"
    super_region = "gulf"
    type         = ["sfincs"]
    topn         = 5

.. list-table::
   :widths: 25 55 10 10
   :header-rows: 1

   * - Parameter
     - Description
     - Default
     - Unit

   * - name
     - Cluster name. Required.
     -
     -

   * - type
     - Model types in the cluster.
     - all
     -

   * - region
     - List of regions whose models are in the cluster.
     - all
     -

   * - super_region
     - Super region whose models are in the cluster.
     -
     -

   * - topn
     - Maximum number of models to run.
     - 10
     -

   * - hm0fac
     - Factor applied to the wave height in the total water level estimate.
     - 0.2
     -

   * - boundary_twl_margin
     - Margin added to ``boundary_twl_treshold``.
     - 0.0
     - m

   * - use_threshold
     - ``"y"`` to only run models that exceed the threshold; any other value
       runs the ``topn`` highest models regardless of the threshold.
     - "y"
     -