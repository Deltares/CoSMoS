Code architecture
=================

This page describes how the CoSMoS code is organized. It is meant for
developers who want to change or extend CoSMoS. For what happens during a run
(the Main Loop and the Model Loop), see :ref:`How CoSMoS works <workflow>`.

Figure 1 shows the main classes and methods, and which loop calls them.

.. figure:: manual/pngs/detailed_workflow.*
   :width: 100%
   :alt: Classes and methods of CoSMoS

   Figure 1: Classes and methods of CoSMoS. Row colours indicate whether a
   method is called from the Main Loop (blue) or the Model Loop (yellow).

Overview
--------

The code is organized in three layers:

1. **Orchestration** — the ``cosmos`` object and the Main Loop and Model Loop
   that drive the forecast cycle.
2. **Model wrappers** — one class per model type that prepares, starts, and
   post-processes the models, plus a job script per model type that runs the
   simulation.
3. **Supporting modules** — meteorological data, cyclone track ensembles,
   observation stations, map tiles, the web viewer, and cloud execution.

Almost every module imports the ``cosmos`` object (``from .cosmos import
cosmos``), which holds the configuration and the state of the current run
(``cosmos.config``, ``cosmos.scenario``, ``cosmos.cycle``, ...).

The core classes can be imported from the top-level package::

    from cosmos import cosmos, MainLoop, ModelLoop, Configuration, Scenario

The model wrappers are not imported at the top level, because they depend on
optional model packages. Import them from their module::

    from cosmos.sfincs import CoSMoS_SFINCS

Orchestration
-------------

.. list-table::
   :widths: 30 70
   :header-rows: 0

   * - :py:class:`~cosmos.cosmos.CoSMoS`
     - The central object (``cosmos``). Provides ``initialize()``,
       ``validate()``, ``run()``, ``post_process()``, and
       ``make_webviewer()``.

   * - :py:class:`~cosmos.main_loop.MainLoop`
     - Runs once per cycle: reads the scenario, sets the cycle times,
       downloads and collects meteo data, generates the track ensemble,
       starts the Model Loop, and finishes the cycle (clean-up, web viewer).

   * - :py:class:`~cosmos.model_loop.ModelLoop`
     - Repeats every second until all models have finished: pre-processes
       and submits models that are ready, and moves and post-processes
       finished models.

   * - :py:class:`~cosmos.configuration.Configuration`
     - Reads the configuration file and holds all settings.

   * - :py:class:`~cosmos.scenario.Scenario`
     - Reads the scenario file and creates the models and clusters.

   * - :py:class:`~cosmos.cluster.Cluster`
     - Selects which models in a cluster are run.

   * - :py:class:`~cosmos.stations.Stations`
     - Reads the observation station files.

Model wrappers and job scripts
------------------------------

Each model type has two parts:

- A **wrapper class** that inherits from :py:class:`~cosmos.model.Model`. It
  runs in the CoSMoS process and has access to the ``cosmos`` object. It
  implements ``read_model_specific()``, ``pre_process()``, ``move()``, and
  ``post_process()``.
- A **job script** (e.g. :py:mod:`cosmos.run_sfincs`) that is copied to the
  job folder as ``run_job_2.py`` and runs independently, possibly on another
  machine or in a container. It only has access to the job folder and a
  ``config.yml`` written by the wrapper. It carries out nesting step 2, runs
  the simulation, and makes the map tiles; for ensembles it also prepares and
  merges the ensemble members.

When adding functionality to a model, decide whether it belongs in the
wrapper (needs the ``cosmos`` object) or in the job script (must run where the
model runs).

.. list-table::
   :widths: 30 25 45
   :header-rows: 1

   * - Wrapper class
     - Job script
     - Model

   * - :py:class:`~cosmos.model.Model`
     -
     - Base class: reads ``model.toml``, nesting, stations, meteo forcing
       files, job submission, restart files.

   * - :py:class:`~cosmos.sfincs.CoSMoS_SFINCS`
     - ``run_sfincs.py``
     - SFINCS (via ``hydromt_sfincs``)

   * - :py:class:`~cosmos.hurrywave.CoSMoS_HurryWave`
     - ``run_hurrywave.py``
     - HurryWave (via ``hydromt_hurrywave``)

   * - :py:class:`~cosmos.delft3dfm.CoSMoS_Delft3DFM`
     - ``run_delft3dfm.py``
     - Delft3D FM

   * - :py:class:`~cosmos.xbeach.CoSMoS_XBeach`
     - ``run_xbeach.py``
     - XBeach

   * - :py:class:`~cosmos.beware.CoSMoS_BEWARE`
     - ``run_beware.py``
     - BEWARE

Supporting modules
------------------

.. list-table::
   :widths: 30 70
   :header-rows: 0

   * - :py:mod:`cosmos.meteo`
     - Downloads and collects gridded meteo data and cyclone tracks.

   * - :py:mod:`cosmos.track_ensemble`
     - Generates cyclone track ensembles.

   * - :py:mod:`cosmos.tsunami`
     - Computes the initial water level for tsunami events.

   * - :py:class:`~cosmos.webviewer.WebViewer`
     - Builds and publishes the web viewer.

   * - :py:mod:`cosmos.tiling`, :py:mod:`cosmos.merge_tiles`
     - Makes and merges map tiles.

   * - :py:class:`~cosmos.cloud.Cloud`, :py:mod:`cosmos.argo`
     - AWS S3 transfer and Argo Workflows job submission (cloud mode).

   * - :py:mod:`cosmos.validation`
     - Checks a scenario before it is run.

   * - :py:mod:`cosmos.custom_processing`
     - Runs the user's pre- and post-processing scripts.

   * - :py:mod:`cosmos.clean_up`
     - Removes old files after a cycle.

Module layout
-------------

::

    cosmos/
    ├── __init__.py          # Public classes
    ├── __main__.py          # Command line interface (python -m cosmos)
    ├── cosmos.py            # The cosmos object
    ├── main_loop.py         # Main Loop
    ├── model_loop.py        # Model Loop
    ├── configuration.py     # Configuration file
    ├── scenario.py          # Scenario file
    ├── cluster.py           # Model clusters
    ├── stations.py          # Observation stations
    ├── validation.py        # Scenario validation
    ├── custom_processing.py # User pre/post-processing scripts
    │
    ├── model.py             # Base model class
    ├── sfincs.py            # SFINCS wrapper
    ├── hurrywave.py         # HurryWave wrapper
    ├── delft3dfm.py         # Delft3D FM wrapper
    ├── xbeach.py            # XBeach wrapper
    ├── beware.py            # BEWARE wrapper
    │
    ├── run_sfincs.py        # SFINCS job script
    ├── run_hurrywave.py     # HurryWave job script
    ├── run_delft3dfm.py     # Delft3D FM job script
    ├── run_xbeach.py        # XBeach job script
    ├── run_beware.py        # BEWARE job script
    ├── run_parallel.py      # Worker script for parallel mode
    │
    ├── meteo.py             # Meteo data and cyclone tracks
    ├── track_ensemble.py    # Track ensembles
    ├── tsunami.py           # Tsunami source
    ├── webviewer.py         # Web viewer
    ├── tiling.py            # Map tiles
    ├── merge_tiles.py       # Tile merging (cloud)
    ├── color_maps.py        # Colour scales
    ├── cloud.py             # S3 operations
    ├── argo.py              # Argo Workflows client
    └── clean_up.py          # Clean-up