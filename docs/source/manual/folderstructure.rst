.. _folder_structure:

Folder structure
----------------

CoSMoS works with three folders, which can be in different locations:

- the **run folder**, with the configuration, scenarios, and results;
- the **model database**, with the input of all models
  (see :ref:`Model database <models>`);
- the **meteo database**, with meteorological data and cyclone tracks
  (see :ref:`Meteorological forcing <meteo>`).

The paths to the model database and the meteo database are set in the
:ref:`configuration file <configuration>`. The databases can be shared by
several run folders.

Run folder
^^^^^^^^^^

.. code-block:: text

    run_folder
    ├── configuration
    │   ├── config.toml
    │   ├── color_maps
    │   │   └── map_contours.toml
    │   ├── stations
    │   │   └── <station_file>.toml
    │   ├── super_regions
    │   │   └── <super_region>.toml
    │   └── areas
    │       └── <area>.geojson
    ├── scenarios
    │   └── <scenario_name>
    │       ├── scenario.toml
    │       ├── <cycle>
    │       └── restart
    ├── observations
    │   └── <observations_path>
    ├── webviewers
    │   └── <webviewer_name>
    ├── jobs
    └── run_cosmos.py

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - File or folder
     - Description

   * - ``configuration/config.toml``
     - Main configuration file (see :ref:`Configuration file <configuration>`).
       Other names can be used for additional configuration files.

   * - ``configuration/color_maps``
     - Colour scales of the map layers in the web viewer
       (``map_contours.toml``). Required; copy it from the template run
       folder.

   * - ``configuration/stations``
     - Station files with observation station locations (see
       :ref:`Observation stations <stations>`).

   * - ``configuration/super_regions``
     - Super region files (see :ref:`Regions and super regions <super_regions>`).

   * - ``configuration/areas``
     - Optional. GeoJSON polygons used to select JTWC forecast tracks (see
       :ref:`Tropical cyclones <meteo_cyclones>`).

   * - ``scenarios``
     - One folder per scenario, with the scenario file, the results of each
       cycle, and the restart files (see
       :ref:`Scenario configuration <scenario>` and
       :ref:`Model output <output>`).

   * - ``observations``
     - Optional. Manually provided observation files, in one sub-folder per
       event (see :ref:`Observation stations <stations>`).

   * - ``webviewers``
     - One folder per web viewer (see :ref:`Web viewer <webviewer>`).

   * - ``jobs``
     - Only used in ``parallel`` run mode on Windows: CoSMoS places a small
       file here for each model that is ready to run, which the worker PCs
       pick up (see :ref:`Running CoSMoS <running>`).

   * - ``run_cosmos.py``
     - Script to run CoSMoS (see :ref:`Running CoSMoS <running>`). It can
       also be stored elsewhere.

CoSMoS creates ``scenarios/<scenario_name>/<cycle>``, ``restart``,
``webviewers``, and ``jobs`` itself. While a cycle runs, CoSMoS writes its log
to ``cosmos.log`` in the run folder; when the cycle is finished, the log is
moved to the cycle folder.

The ``configuration`` folder can also be placed one level above the run
folder, so that several run folders share one configuration.

A template run folder is included in the CoSMoS repository, in
``cosmos_run_folder``.

Model database
^^^^^^^^^^^^^^

.. code-block:: text

    model_database
    └── <region>
        └── <model_type>
            └── <model_name>
                ├── model.toml
                ├── model.geojson
                ├── input
                ├── tiling
                └── stations

See :ref:`Model database <models>` for a description of each file and folder.

Meteo database
^^^^^^^^^^^^^^

.. code-block:: text

    meteo_database
    ├── meteo_database.toml
    ├── <dataset_name>
    │   └── <cycle>
    │       └── <dataset_name>.<yyyymmdd_hhmm>.nc
    └── tracks
        └── <track_name>.cyc

See :ref:`Meteorological forcing <meteo>` for a description of each file and
folder.