.. _configuration:

Setting up your configuration file
-----------------------------------

The CoSMoS configuration file (``config.toml``) is located in the ``configuration`` folder of your run directory.
It specifies paths, executables, web server settings, and runtime behaviour.

Example configuration file:

.. include:: examples/config.toml
       :literal:

The sections below describe all available settings.

[conda]
^^^^^^^

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - keyword
     - description
     - default

   * - path
     - Path to your conda/miniforge installation.
     - None

   * - env
     - Name of the conda environment.
     - None

[model_database]
^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - keyword
     - description
     - default

   * - path
     - Path to the model database folder.
     - None

[meteo_database]
^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - keyword
     - description
     - default

   * - path
     - Path to the meteorological database folder.
     - None

[executables]
^^^^^^^^^^^^^

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - keyword
     - description
     - default

   * - sfincs_path
     - Path to the SFINCS executable folder.
     - None

   * - sfincs_docker_image
     - Docker image name for SFINCS (used when ``sfincs_docker = true``).
     - None

   * - hurrywave_path
     - Path to the HurryWave executable folder.
     - None

   * - hurrywave_docker_image
     - Docker image name for HurryWave (used when ``hurrywave_docker = true``).
     - None

   * - delft3dfm_path
     - Path to the Delft3D FM executable folder.
     - None

   * - xbeach_path
     - Path to the XBeach executable folder.
     - None

   * - beware_path
     - Path to the BEWARE executable folder.
     - None

[webserver]
^^^^^^^^^^^

Settings for uploading the web viewer to a remote server.

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - keyword
     - description
     - default

   * - hostname
     - Web server hostname (SFTP).
     - None

   * - path
     - Remote path on the web server.
     - None

   * - username
     - SFTP username.
     - None

   * - password
     - SFTP password.
     - None

[webviewer]
^^^^^^^^^^^

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - keyword
     - description
     - default

   * - name
     - Name of the web viewer.
     - None

   * - version
     - Web viewer template from ``configuration/webviewer_templates``.
     - None

   * - lon
     - Initial longitude for the web viewer map.
     - 0.0

   * - lat
     - Initial latitude for the web viewer map.
     - 0.0

   * - zoom
     - Initial zoom level for the web viewer map.
     - 1

   * - lon_lim
     - Longitude limits for wind and meteo maps (list of two values).
     - None

   * - lat_lim
     - Latitude limits for wind and meteo maps (list of two values).
     - None

   * - storm_classification
     - Classification system for track points. Options: ``"saffirsimpson"``, ``"pagasa"``.
     - "saffirsimpson"

[cloud_config]
^^^^^^^^^^^^^^

Settings for cloud execution via AWS S3 and Argo Workflows.

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - keyword
     - description
     - default

   * - host
     - Argo Workflows API endpoint URL.
     - None

   * - access_key
     - AWS S3 access key.
     - None

   * - secret_key
     - AWS S3 secret key.
     - None

   * - region
     - AWS region for the Kubernetes cluster.
     - "eu-west-1"

   * - namespace
     - Kubernetes namespace for Argo.
     - "argo"

   * - token
     - Argo authentication token.
     - None

[track_ensemble]
^^^^^^^^^^^^^^^^

Error statistics for tropical cyclone track ensemble generation (based on NHC 2018--2021).

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - keyword
     - description
     - default

   * - mean_abs_cte24
     - Mean absolute cross-track error at 24 h (nautical miles).
     - 19.04

   * - sc_cte
     - Auto-regression coefficient for cross-track error.
     - 1.33

   * - mean_abs_ate24
     - Mean absolute along-track error at 24 h (nautical miles).
     - 26.22

   * - sc_ate
     - Auto-regression coefficient for along-track error.
     - 1.34

   * - mean_abs_ve24
     - Mean absolute wind speed error at 24 h (knots).
     - 6.99

   * - sc_ve
     - Auto-regression coefficient for wind speed error.
     - 1.00

   * - bias_ve
     - Wind speed bias per hour.
     - 0.0

   * - nr_realizations
     - Number of ensemble realizations to generate.
     - 10

[run]
^^^^^

Runtime settings controlling the forecast loop.

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - keyword
     - description
     - default

   * - mode
     - Run mode. ``"single_shot"`` runs once (hindcast); ``"continuous"`` repeats at the configured interval (forecast).
     - "single_shot"

   * - interval
     - Cycle interval in hours (forecast mode only).
     - 6

   * - delay
     - Hours to wait after cycle time before starting the run.
     - 0

   * - run_mode
     - Execution method. ``"serial"`` (local), ``"parallel"`` (multiple local PCs), or ``"cloud"`` (AWS/Argo).
     - "serial"

   * - event_mode
     - Event type. ``"meteo"`` (weather-driven) or ``"tsunami"`` (earthquake-driven).
     - "meteo"

   * - run_models
     - Run model simulations.
     - true

   * - just_initialize
     - Only initialize scenario (do not run models).
     - false

   * - download_meteo
     - Download meteorological data from remote servers.
     - true

   * - collect_meteo_up_to_cycle
     - Collect meteo data only up to the current cycle time.
     - false

   * - catch_up
     - Catch up on missed cycles.
     - false

   * - clean_up
     - Clean up old files after each cycle.
     - false

   * - clean_up_mode
     - Cleanup strategy. Options: ``"forecast"``, ``"risk_map"``, ``"continuous"``, ``"continuous_hindcast"``.
     - "forecast"

   * - prune_after_hours
     - Remove cycle folders older than this many hours.
     - 72

   * - make_flood_maps
     - Generate flood map tiles.
     - true

   * - make_wave_maps
     - Generate wave map tiles.
     - true

   * - make_water_level_maps
     - Generate water level map tiles.
     - true

   * - make_storm_surge_maps
     - Generate storm surge map tiles.
     - true

   * - make_meteo_maps
     - Generate meteorological map tiles.
     - true

   * - make_sedero_maps
     - Generate sedimentation/erosion map tiles.
     - true

   * - make_webviewer
     - Build the web viewer after model completion.
     - true

   * - upload
     - Upload web viewer to the remote server.
     - true

   * - dthis
     - Output interval for history files (seconds).
     - 600.0

   * - dtmap
     - Output interval for map files (seconds).
     - 21600.0

   * - dtmax
     - Output interval for maximum value snapshots (seconds).
     - 21600.0

   * - dtwnd
     - Wind forcing time step (seconds).
     - 1800

   * - spw_wind_field
     - Spiderweb wind field type. Options: ``"parametric"``, ``"background"``.
     - "parametric"

   * - use_spw_precip
     - Use precipitation from spiderweb file for overland flood models.
     - false

   * - clear_zs_ini
     - Limit initial water level in SFINCS models (to remove excess from previous events).
     - false

   * - bathtub
     - Enable bathtub mode for SFINCS flood map models.
     - false

   * - bathtub_fachs
     - Bathtub mode wave height factor.
     - 0.4

   * - sfincs_docker
     - Run SFINCS in Docker instead of native executable.
     - false

   * - hurrywave_docker
     - Run HurryWave in Docker instead of native executable.
     - false

   * - only_run_ensemble
     - Only run ensemble models (skip deterministic).
     - false

   * - ensemble_models
     - Model types to include in ensemble runs.
     - ["sfincs", "hurrywave", "delft3d", "xbeach", "beware"]

   * - post_processing_script
     - Path to a custom post-processing script run after each model loop.
     - None

The ``[run]`` settings can be overwritten programmatically when initializing CoSMoS (see :ref:`Running CoSMoS <running>`).
