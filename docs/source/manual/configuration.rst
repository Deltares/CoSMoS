.. _configuration:

Configuration file
------------------

The configuration file sets the paths to the databases and model executables,
the web viewer and upload settings, and how CoSMoS runs. It is a TOML file in
the ``configuration`` folder of the run folder, usually named ``config.toml``.
Another name can be used by passing it to ``cosmos.initialize()`` or with
``--config`` on the command line (see :ref:`Running CoSMoS <running>`), for
example to keep separate configurations for local and cloud runs.

CoSMoS looks for the ``configuration`` folder in the run folder first, and
otherwise one level up. The second option lets several run folders share one
configuration.

The settings in the ``[run]`` section apply to all scenarios. They can be
overwritten in a Python script after ``cosmos.initialize()``, for example
``cosmos.config.run.download_meteo = False``.

Example
^^^^^^^

.. code-block:: toml

    [conda]
    path = "c:\\Users\\<user>\\miniforge3"
    env  = "cosmos"

    [model_database]
    path = "c:\\work\\cosmos\\model_database"

    [meteo_database]
    path = "c:\\work\\cosmos\\meteo_database"

    [executables]
    sfincs_path    = "c:\\work\\cosmos\\exe\\sfincs"
    hurrywave_path = "c:\\work\\cosmos\\exe\\hurrywave"
    delft3dfm_path = "c:\\work\\cosmos\\exe\\delft3dfm"
    xbeach_path    = "c:\\work\\cosmos\\exe\\xbeach"
    beware_path    = "c:\\work\\cosmos\\exe\\beware"

    [webviewer]
    name    = "my_viewer"
    version = "version06"
    lon     = -75.0
    lat     = 30.0
    zoom    = 5

    [run]
    mode           = "single_shot"
    run_mode       = "serial"
    download_meteo = true
    upload         = false

Only the sections and settings that differ from the defaults need to be given.
Settings that CoSMoS does not know are ignored, so check the spelling of
keywords carefully.

[conda]
^^^^^^^

The conda environment in which the model jobs are run.

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Keyword
     - Description
     - Default

   * - path
     - Path to the conda (or miniforge) installation. Required on Windows.
     - None

   * - env
     - Name of the conda environment. Required on Linux.
     - "cosmos" (Windows)

[model_database]
^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Keyword
     - Description
     - Default

   * - path
     - Path to the :ref:`model database <models>`. Required.
     - None

[meteo_database]
^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Keyword
     - Description
     - Default

   * - path
     - Path to the :ref:`meteo database <meteo>`.
     - None

[executables]
^^^^^^^^^^^^^

Only the executables of the model types that are used need to be set.

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Keyword
     - Description
     - Default

   * - sfincs_path
     - Folder with the SFINCS executable.
     - None

   * - hurrywave_path
     - Folder with the HurryWave executable.
     - None

   * - delft3dfm_path
     - Folder with the Delft3D FM installation (DIMR set).
     - None

   * - xbeach_path
     - Folder with the XBeach executable.
     - None

   * - beware_path
     - Folder with the BEWARE database and run script (see
       :ref:`Model database <models>`).
     - None

   * - sfincs_docker_image
     - Docker image for SFINCS, used when ``sfincs_docker = true`` in
       ``[run]``.
     - None

   * - hurrywave_docker_image
     - Docker image for HurryWave, used when ``hurrywave_docker = true`` in
       ``[run]``.
     - None

[webviewer]
^^^^^^^^^^^

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Keyword
     - Description
     - Default

   * - name
     - Name of the web viewer. The web viewer is written to
       ``webviewers/<name>`` in the run folder. Required.
     - None

   * - version
     - Web viewer template, from ``webviewer_templates`` in the CoSMoS
       repository (e.g. ``"version06"``). Required.
     - None

   * - lon, lat
     - Initial map centre (degrees). Can be overwritten per scenario.
     - 0.0, 0.0

   * - zoom
     - Initial zoom level. Can be overwritten per scenario.
     - 1

   * - lon_lim, lat_lim
     - Longitude and latitude limits of the wind and meteo maps (list of two
       values).
     - None

   * - storm_classification
     - Classification of cyclone track points: ``"saffirsimpson"`` or
       ``"pagasa"``.
     - "saffirsimpson"

[webserver]
^^^^^^^^^^^

Where the web viewer is copied to after each cycle, when ``upload = true``
in ``[run]`` and ``run_mode`` is ``"serial"`` or ``"parallel"``. In
``"cloud"`` run mode, the web viewer is uploaded to AWS S3 instead.

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Keyword
     - Description
     - Default

   * - path
     - Folder (for example on a network drive of the web server) to which
       the web viewer is copied.
     - None

[cloud_config]
^^^^^^^^^^^^^^

Settings for ``run_mode = "cloud"``, in which models run as Argo Workflows on
a Kubernetes cluster and data is transferred via AWS S3.

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Keyword
     - Description
     - Default

   * - host
     - Argo Workflows API endpoint URL.
     - None

   * - token
     - Argo authentication token.
     - None

   * - namespace
     - Kubernetes namespace of the Argo installation.
     - "argo"

   * - access_key
     - AWS S3 access key.
     - None

   * - secret_key
     - AWS S3 secret key.
     - None

   * - region
     - AWS region of the cluster.
     - "eu-west-1"

[track_ensemble]
^^^^^^^^^^^^^^^^

Settings for synthetic track ensembles (see
:ref:`Track ensemble <meteo_ensemble>`). The default error statistics are
based on NHC forecasts of 2018–2021.

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Keyword
     - Description
     - Default

   * - nr_realizations
     - Number of synthetic tracks. Can be overwritten per scenario with
       ``track_ensemble_nr_realizations``.
     - 10

   * - mean_abs_cte24
     - Mean absolute cross-track error at 24 h (nautical miles).
     - 19.04

   * - sc_cte
     - Auto-regression coefficient for the cross-track error.
     - 1.33

   * - mean_abs_ate24
     - Mean absolute along-track error at 24 h (nautical miles).
     - 26.22

   * - sc_ate
     - Auto-regression coefficient for the along-track error.
     - 1.34

   * - mean_abs_ve24
     - Mean absolute maximum wind speed error at 24 h (knots).
     - 6.99

   * - sc_ve
     - Auto-regression coefficient for the wind speed error (1 = no
       auto-regression).
     - 1.00

   * - bias_ve
     - Wind speed bias per hour.
     - 0.0

[run]
^^^^^

Cycles
""""""

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Keyword
     - Description
     - Default

   * - mode
     - ``"single_shot"``: run one cycle and stop (hindcast).
       ``"continuous"``: start a new cycle every ``interval`` hours
       (forecast).
     - "single_shot"

   * - interval
     - Cycle interval in hours. Also used to round the current time down to
       a cycle time when no cycle is given.
     - 6

   * - delay
     - Hours to wait after the cycle time before a cycle starts
       (continuous mode), e.g. to wait until forecast data is available.
     - 0

   * - catch_up
     - In continuous mode, skip cycles that were missed and continue with
       the most recent one.
     - false

   * - event_mode
     - ``"meteo"`` (weather-driven) or ``"tsunami"`` (earthquake-driven, see
       :ref:`Scenario configuration <scenario>`).
     - "meteo"

Model execution
"""""""""""""""

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Keyword
     - Description
     - Default

   * - run_mode
     - ``"serial"``, ``"parallel"``, or ``"cloud"`` (see
       :ref:`Execution modes <running>`).
     - "serial"

   * - sfincs_docker
     - Run SFINCS in Docker (image set in ``[executables]``).
     - false

   * - hurrywave_docker
     - Run HurryWave in Docker (image set in ``[executables]``).
     - false

   * - ensemble_models
     - Model types that are run as an ensemble. Can be overwritten per
       scenario.
     - ["sfincs", "hurrywave", "delft3d", "xbeach", "beware"]

Meteorological data
"""""""""""""""""""

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Keyword
     - Description
     - Default

   * - download_meteo
     - Download gridded meteo data before each cycle.
     - true

   * - collect_meteo_up_to_cycle
     - Only use forecast cycles up to the cycle being run (useful for
       hindcasts of forecast data).
     - false

   * - spw_wind_field
     - Spiderweb wind field: ``"parametric"`` or ``"meteo_data"`` (see
       :ref:`Tropical cyclones <meteo_cyclones>`).
     - "parametric"

   * - dtwnd
     - Time step of the meteo forcing in SFINCS and HurryWave (seconds).
     - 1800

Model output
""""""""""""

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Keyword
     - Description
     - Default

   * - dthis
     - Output interval of time series at stations (seconds, SFINCS).
     - 600

   * - dtmap
     - Output interval of map output (seconds, SFINCS and HurryWave).
     - 21600

   * - dtmax
     - Interval of maximum value output (seconds, SFINCS and HurryWave).
     - 21600

SFINCS options
""""""""""""""

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Keyword
     - Description
     - Default

   * - bathtub
     - Run SFINCS flood map models in bathtub mode.
     - false

   * - bathtub_fachs
     - Value of the SFINCS ``bathtub_fachs`` parameter in bathtub mode.
     - 0.4

   * - use_spw_precip
     - Use the rainfall from the spiderweb in SFINCS flood map models.
     - false

   * - clear_zs_ini
     - Limit the initial water level from the restart file to
       ``zs_ini_max`` (set in ``model.toml``), to remove water left from a
       previous event.
     - false

Maps and web viewer
"""""""""""""""""""

Map tiles are only made for models that have the matching setting in
``model.toml`` (see :ref:`Model database <models>`).

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Keyword
     - Description
     - Default

   * - make_flood_maps
     - Make flood map tiles.
     - true

   * - make_water_level_maps
     - Make maximum water level map tiles.
     - true

   * - make_storm_surge_maps
     - Make storm surge map tiles.
     - true

   * - make_wave_maps
     - Make wave height map tiles.
     - true

   * - make_sedero_maps
     - Make sedimentation/erosion map tiles.
     - true

   * - make_meteo_maps
     - Make precipitation map tiles and wind and meteo maps.
     - true

   * - make_webviewer
     - Build the web viewer after each cycle.
     - true

   * - upload
     - Copy or upload the web viewer after each cycle (see
       ``[webserver]``).
     - true

Clean-up
""""""""

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Keyword
     - Description
     - Default

   * - clean_up
     - Remove old files at the end of each cycle.
     - false

   * - clean_up_mode
     - What is removed:

       - ``"continuous"``: cycle folders and restart files older than
         ``prune_after_hours``, and web viewer data older than 24 hours.
       - ``"continuous_hindcast"``: model input folders, the job list, and
         restart files older than ``prune_after_hours``.
       - ``"risk_map"``: model input folders, the output of models with
         nested models, all restart files, the track folder, and the job
         list.
       - ``"forecast"``: nothing.
     - "forecast"

   * - prune_after_hours
     - Age in hours after which cycle folders and restart files are removed.
     - 72

Custom scripts
""""""""""""""

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Keyword
     - Description
     - Default

   * - pre_processing_script
     - Python file that is run at the start of each cycle, before the meteo
       data is downloaded.
     - None

   * - post_processing_script
     - Python file that is run after all models have finished, before the
       web viewer is built.
     - None

A custom script must contain a function ``main(cycle_info_file)``. CoSMoS
calls it with the path of ``cycle_info.yml``, a summary of the scenario,
cycle, and models that CoSMoS writes in the cycle folder.