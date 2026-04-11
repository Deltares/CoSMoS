Code Architecture
=================

This page describes how the CoSMoS codebase is organized and how the main
components interact during a forecast cycle.

Overview
--------

CoSMoS is structured around three layers:

1. **Orchestration** — the main loop and model loop that drive the forecast cycle.
2. **Model wrappers** — model-specific classes that handle pre-processing, execution, and post-processing for each supported model.
3. **Supporting services** — meteorological data handling, observation stations, map tiling, web viewer generation, and cloud infrastructure.

All classes are importable from the top-level ``cosmos`` package::

    from cosmos import cosmos, MainLoop, Configuration, CoSMoS_SFINCS

Orchestration
-------------

The forecast cycle is controlled by three classes:

.. list-table::
   :widths: 25 75
   :header-rows: 0

   * - :py:class:`~cosmos.CoSMoS`
     - The central singleton (``cosmos``). Manages initialization, configuration,
       and provides ``run()``, ``post_process()``, and ``make_webviewer()`` entry
       points.

   * - :py:class:`~cosmos.MainLoop`
     - Runs once per forecast cycle. Reads the scenario, downloads meteorological
       data, determines cycle times, generates track ensembles (if applicable),
       and starts the model loop.

   * - :py:class:`~cosmos.ModelLoop`
     - Iterates every second while models are running. Pre-processes waiting
       models, submits jobs, monitors for completion, moves output, runs
       post-processing, and builds the web viewer when all models finish.

A typical forecast cycle proceeds as follows::

    cosmos.initialize(main_path, config_file="config.toml")
    cosmos.run("scenario_name")

    # Internally:
    # MainLoop.start()
    #   → read scenario, download meteo, set cycle times
    #   → ModelLoop.start()
    #       → pre-process → submit → wait → move → post-process
    #       → (repeat for all models)
    #   → build web viewer
    #   → clean up

Configuration and scenario
--------------------------

.. list-table::
   :widths: 25 75
   :header-rows: 0

   * - :py:class:`~cosmos.Configuration`
     - Reads ``config.toml`` and stores all settings: paths, executables,
       web server credentials, cloud config, and runtime parameters.

   * - :py:class:`~cosmos.Scenario`
     - Reads ``scenario.toml`` and initializes the collection of models,
       clusters, timing parameters, and nesting relationships.

   * - :py:class:`~cosmos.Cluster`
     - Groups models and applies conditional run logic (top-N by water level,
       threshold-based, or ensemble threshold).

   * - :py:class:`~cosmos.Stations`
     - Reads observation station definitions (tide gauges, wave buoys) from
       TOML files for model validation.

Model wrappers
--------------

Each supported model has a wrapper class that inherits from :py:class:`~cosmos.Model`
and implements four methods: ``read_model_specific()``, ``pre_process()``,
``move()``, and ``post_process()``.

.. list-table::
   :widths: 25 75
   :header-rows: 0

   * - :py:class:`~cosmos.Model`
     - Base class with shared functionality: reading ``model.toml``, nesting
       setup, station assignment, meteo file writing, job submission, and
       restart file management.

   * - :py:class:`~cosmos.CoSMoS_SFINCS`
     - SFINCS flood model (via ``hydromt_sfincs.SfincsModel``).

   * - :py:class:`~cosmos.CoSMoS_HurryWave`
     - HurryWave spectral wave model (via ``hydromt_hurrywave.HurrywaveModel``).

   * - :py:class:`~cosmos.CoSMoS_Delft3DFM`
     - Delft3D Flexible Mesh hydrodynamic model.

   * - :py:class:`~cosmos.CoSMoS_XBeach`
     - XBeach nearshore morphodynamic model.

   * - :py:class:`~cosmos.CoSMoS_BEWARE`
     - BEWARE reef-coast wave runup meta-model.

Each wrapper also has a standalone job runner script (e.g. ``run_sfincs.py``)
that is copied to the job folder and executed independently. These scripts
handle nesting (step 2), simulation execution, ensemble merging, map tile
generation, and cleanup.

Supporting services
-------------------

.. list-table::
   :widths: 25 75
   :header-rows: 0

   * - :py:class:`~cosmos.WebViewer`
     - Builds the interactive web viewer with time-series plots, map tile
       layers, and GeoJSON overlays.

   * - :py:class:`~cosmos.Cloud`
     - AWS S3 upload/download and Argo Workflows job submission for
       cloud-based execution.

   * - ``meteo``
     - Downloads and collects meteorological forcing data (gridded wind,
       pressure, precipitation) and tropical cyclone tracks.

   * - ``tiling`` / ``merge_tiles``
     - Generates and merges PNG map tiles (flood maps, wave heights, water
       levels, storm surge) for the web viewer.

   * - ``track_ensemble``
     - Generates synthetic tropical cyclone track ensembles for probabilistic
       storm surge prediction.

   * - ``tsunami``
     - Computes initial water surface deformation from earthquake fault
       parameters.

Module layout
-------------

::

    cosmos/
    ├── __init__.py          # Public API re-exports
    ├── cosmos.py            # CoSMoS singleton class
    ├── main_loop.py         # Forecast cycle loop
    ├── model_loop.py        # Model execution loop
    ├── model.py             # Base Model class
    ├── configuration.py     # Configuration reader
    ├── scenario.py          # Scenario reader
    ├── cluster.py           # Conditional model execution
    ├── stations.py          # Observation station management
    │
    ├── sfincs.py            # SFINCS wrapper
    ├── hurrywave.py         # HurryWave wrapper
    ├── delft3dfm.py         # Delft3D FM wrapper
    ├── xbeach.py            # XBeach wrapper
    ├── beware.py            # BEWARE wrapper
    │
    ├── run_sfincs.py        # SFINCS standalone job runner
    ├── run_hurrywave.py     # HurryWave standalone job runner
    ├── run_delft3dfm.py     # Delft3D FM standalone job runner
    ├── run_xbeach.py        # XBeach standalone job runner
    ├── run_beware.py        # BEWARE standalone job runner
    │
    ├── meteo.py             # Meteorological data handling
    ├── track_ensemble.py    # Cyclone track ensemble generation
    ├── tsunami.py           # Tsunami source generation
    ├── cloud.py             # S3 / Argo cloud operations
    ├── argo.py              # Argo Workflows client
    ├── webviewer.py         # Web viewer builder
    ├── tiling.py            # Map tile generation
    ├── merge_tiles.py       # Tile merging (cloud)
    ├── color_maps.py        # Contour / color definitions
    └── clean_up.py          # Cleanup routines
