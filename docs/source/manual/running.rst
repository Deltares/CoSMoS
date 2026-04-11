.. _running:

Running CoSMoS
--------------

Using a Python script
^^^^^^^^^^^^^^^^^^^^^

The most common way to run CoSMoS is with a short Python script:

.. include:: examples/run_cosmos.py
       :literal:

This script requires a *scenario_name* (here: *philippines_nov2013_ifs*). The
corresponding scenario file should be located in:
``scenarios/<scenario_name>/scenario.toml``.

If no ``cycle`` argument is provided, CoSMoS checks the scenario file for a
``cycle`` keyword. If that is also absent, the current time is used (forecast
mode).

Input settings to ``cosmos.initialize()`` will overwrite
:ref:`cycle settings defined in the configuration file <configuration>`.

Using the command line
^^^^^^^^^^^^^^^^^^^^^^

CoSMoS can also be run directly from the command line::

    python -m cosmos run <scenario> [options]

Options:

.. list-table::
   :widths: 25 75
   :header-rows: 0

   * - ``--path``
     - Path to the CoSMoS run folder. If not provided, the ``COSMOS_PATH``
       environment variable is used.

   * - ``--config``
     - Configuration file name (default: ``config.toml``).

   * - ``--cycle``
     - Starting cycle (e.g. ``20231213_00z``).

   * - ``--last-cycle``
     - Last cycle to process.

Examples::

    python -m cosmos run tyndall_forecast --path=c:\work\cosmos\run_folder
    python -m cosmos run tyndall_forecast --config=config_local.toml --cycle=20260224_00z

Using an environment variable::

    set COSMOS_PATH=c:\work\cosmos\run_folder
    python -m cosmos run tyndall_forecast

Additional commands are available:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Command
     - Description

   * - ``python -m cosmos run <scenario>``
     - Run a scenario.

   * - ``python -m cosmos validate <scenario>``
     - Validate a scenario without running (see below).

   * - ``python -m cosmos post-process <scenario>``
     - Post-process model results only.

   * - ``python -m cosmos webviewer <scenario>``
     - Build the web viewer without running models.

Validation
^^^^^^^^^^

CoSMoS validates the scenario automatically before each run. Validation checks:

- Configuration paths (model database, meteo database).
- Scenario file exists and is parseable.
- All referenced models exist in the model database.
- All referenced super regions and station files exist.
- Nesting chains are valid (no circular dependencies, parent models exist).
- Meteo dataset, spiderweb, or track file exists.
- Model executables exist (when running locally).

If validation fails, the run is aborted with a detailed error report.

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

1. **serial** — run all models locally on your PC (``run_mode = "serial"``).

2. **parallel** — run models on multiple local PCs (``run_mode = "parallel"``).
   On the main PC, run ``run_cosmos.py`` as usual. On worker PCs that have
   access to the same run folder, run the following script:

   .. include:: examples/run_parallel.py
          :literal:

   This script monitors the *jobs* folder for models containing a *ready.txt*
   file. You can run it for a specific scenario or set ``scenario = None`` to
   pick up any available job.

3. **cloud** — run models on a Kubernetes cluster via Argo Workflows
   (``run_mode = "cloud"``). Input and output are transferred via AWS S3.
