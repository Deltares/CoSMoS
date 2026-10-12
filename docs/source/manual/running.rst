.. _running:

Running CoSMoS
--------------

Using a Python script
^^^^^^^^^^^^^^^^^^^^^

The most common way to run CoSMoS is with a short Python script:

.. include:: examples/run_cosmos.py
       :literal:

The script does three things:

1. :py:meth:`cosmos.initialize() <cosmos.cosmos.CoSMoS.initialize>` reads the
   :ref:`configuration file <configuration>` from the run folder.
2. Optionally, settings from the ``[run]`` section of the configuration file
   are overwritten by setting ``cosmos.config.run.<keyword>`` *after*
   ``cosmos.initialize()`` and *before* ``cosmos.run()``.
3. :py:meth:`cosmos.run() <cosmos.cosmos.CoSMoS.run>` runs the scenario.

``cosmos.run()`` requires a *scenario_name* (here: *example_forecast_2026*).
The corresponding scenario file should be located in
``scenarios/<scenario_name>/scenario.toml``.

The cycle is given as a string in the format ``yyyymmdd_hhz`` (e.g.
``"20261001_00z"``). If no ``cycle`` argument is provided, CoSMoS checks the
scenario file for a ``cycle`` keyword. If that is also absent, the current time
is used, rounded down to the cycle interval (forecast mode).

Hindcast and forecast
"""""""""""""""""""""

Whether CoSMoS runs one cycle or keeps running is set with ``mode`` in the
``[run]`` section of the :ref:`configuration file <configuration>`:

- ``mode = "single_shot"`` (default) — run one cycle and stop.
- ``mode = "continuous"`` — after each cycle, start the next one at the
  configured ``interval``. Use the ``last_cycle`` argument to stop after a
  given cycle::

      cosmos.run("my_scenario", cycle="20261001_00z", last_cycle="20261003_00z")

When a cycle is run again, models that already finished in that cycle are
skipped (see :ref:`Model output <output>`).

Using the command line
^^^^^^^^^^^^^^^^^^^^^^

CoSMoS can also be run directly from the command line, from within the
``cosmos`` conda environment::

    python -m cosmos run <scenario> [options]

The following commands are available:

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Command
     - Description

   * - ``python -m cosmos run <scenario>``
     - Run a scenario.

   * - ``python -m cosmos validate <scenario>``
     - Validate a scenario without running (see below).

   * - ``python -m cosmos post-process <scenario>``
     - Post-process model results.

   * - ``python -m cosmos webviewer <scenario>``
     - Build the web viewer.

Options:

.. list-table::
   :widths: 20 25 55
   :header-rows: 1

   * - Option
     - Commands
     - Description

   * - ``--path``
     - all
     - Path to the CoSMoS run folder. If not provided, the ``COSMOS_PATH``
       environment variable is used.

   * - ``--config``
     - all
     - Configuration file name (default: ``config.toml``).

   * - ``--cycle``
     - ``run``, ``post-process``, ``webviewer``
     - Cycle to run or process (e.g. ``20231213_00z``).

   * - ``--last-cycle``
     - ``run``
     - Last cycle to process (continuous mode).

   * - ``--models``
     - ``post-process``
     - Comma-separated model names to post-process, or ``all`` (default).

Examples::

    python -m cosmos run example_forecast --path=c:\work\cosmos\run_folder
    python -m cosmos run example_forecast --config=config_local.toml --cycle=20260224_00z
    python -m cosmos post-process example_forecast --models=sfincs_500m,sfincs_100m

Using an environment variable (PowerShell)::

    $env:COSMOS_PATH = "c:\work\cosmos\run_folder"
    python -m cosmos run example_forecast

In a Windows command prompt, use ``set COSMOS_PATH=c:\work\cosmos\run_folder``
instead.

Validation
^^^^^^^^^^

CoSMoS validates the scenario automatically before each run
(:py:meth:`cosmos.validate() <cosmos.cosmos.CoSMoS.validate>`). Validation
reports **errors**, which abort the run, and **warnings**, which do not.

Errors:

- The run folder or the model database does not exist.
- The scenario folder or scenario file is missing, or the file cannot be
  parsed.
- The scenario contains no ``[[model]]`` entries.
- A referenced model, super region, or station file does not exist.
- A model has no ``model.toml`` or no ``input`` folder.
- A model is nested in a parent model (``flow_nested``, ``wave_nested``,
  ``bw_nested``) that is not part of the scenario.
- The nesting contains a circular dependency.
- The meteo dataset is not in the meteo database.

Warnings:

- The meteo database path does not exist, or no meteorological forcing is
  specified.
- The spiderweb or track file is not found.
- A model has no ``crs``.
- Tiling folders are missing for a model with ``make_flood_map`` or
  ``make_wave_map`` enabled.
- A model executable path is not set or does not exist (checked in ``serial``
  run mode only).

The report also lists the models in the scenario and their nesting tree.

To validate without running::

    python -m cosmos validate my_scenario --path=c:\work\cosmos\run_folder

Or from a Python script::

    from cosmos import cosmos

    cosmos.initialize("path/to/run_folder")
    cosmos.validate("my_scenario")

To skip validation (not recommended)::

    cosmos.run("my_scenario", validate=False)

Execution modes
^^^^^^^^^^^^^^^

There are three options to execute model runs, configured via ``run_mode`` in
:ref:`config.toml <configuration>`:

1. **serial** — run all models one after another on your PC
   (``run_mode = "serial"``).

2. **parallel** — run several models at the same time
   (``run_mode = "parallel"``).

   On Windows, models are distributed over multiple PCs. On the main PC, run
   ``run_cosmos.py`` as usual. On each worker PC that has access to the same
   run folder, run (:py:class:`~cosmos.run_parallel.CosmosRunParallel`).

   For every model that is ready to run, CoSMoS writes a small text file with
   the location of the model to ``jobs/<scenario>``. The worker script monitors this folder, 
   claims a job, copies the model to ``local_path``, runs it there, and copies
   the results back. A worker runs one model at a time. You can run the script
   for a specific scenario or set ``scenario = None`` to pick up jobs from any
   scenario.

   On Linux, no worker script is needed: the jobs are started in the
   background on the machine that runs CoSMoS.

3. **cloud** — run models on a Kubernetes cluster via Argo Workflows
   (``run_mode = "cloud"``). Input and output are transferred via AWS S3.