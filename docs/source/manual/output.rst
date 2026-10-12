.. _output:

Model output
------------

CoSMoS writes two kinds of output:

- **Scenario folder** — all model input and output, per cycle, in
  ``scenarios/<scenario_name>`` in the run folder. This is described on this
  page.
- **Web viewer** — map tiles and time series for the web viewer, in
  ``webviewers/<webviewer_name>/data/<scenario_name>/<cycle>`` (see
  :ref:`Web viewer <webviewer>`). Map tiles are written there directly by the
  model jobs.

Scenario folder
^^^^^^^^^^^^^^^

For each cycle, CoSMoS creates a cycle folder in the scenario folder, named
after the cycle time (``yyyymmdd_hhz``). Example for a scenario called
*hurricane_irma* with a cycle starting on 4 September 2017:

.. code-block:: text

    scenarios
    └── hurricane_irma
        ├── scenario.toml
        ├── 20170904_00z
        │   ├── cosmos.log
        │   ├── cycle_info.yml
        │   ├── job_list
        │   │   └── <model_name>.finished
        │   ├── models
        │   │   └── <model_name>
        │   │       ├── input
        │   │       ├── output
        │   │       └── timeseries
        │   ├── track
        │   └── track_ensemble
        └── restart
            └── <model_name>
                ├── flow
                └── wave

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - File or folder
     - Description

   * - ``cosmos.log``
     - Log file of the cycle. During the run it is written to the run folder;
       it is moved here when the cycle is finished.

   * - ``cycle_info.yml``
     - Summary of the scenario, the cycle, and the models in it. Passed to
       custom pre- and post-processing scripts (see
       :ref:`Configuration file <configuration>`).

   * - ``job_list``
     - A ``<model_name>.finished`` file for each model that has finished.

   * - ``models/<model_name>``
     - Folder in which the model runs. When the simulation has finished,
       CoSMoS sorts the files into ``input`` (model input files) and
       ``output`` (model output files, e.g. ``sfincs_map.nc`` and
       ``sfincs_his.nc``). ``timeseries`` contains the time series at the
       observation stations, as CSV files (e.g. ``wl.<station>.csv`` or
       ``waves.<station>.csv``).

   * - ``track``
     - The cyclone track (``storm.cyc``) and spiderweb (``storm.spw``) used in
       this cycle (see :ref:`Tropical cyclones <meteo_cyclones>`).

   * - ``track_ensemble``
     - The ensemble tracks, their spiderwebs, and the cone around the tracks
       (see :ref:`Track ensemble <meteo_ensemble>`).

   * - ``restart``
     - Restart files for each model, in ``flow`` and ``wave`` sub-folders.
       This folder sits next to the cycle folders, so that the next cycle can
       start from a restart file instead of a spin-up.

Ensemble runs are stored in their own model folder, with ``_ensemble`` added
to the model name. Tide-only runs (see ``include_tide_only`` in
:ref:`Model database <models>`) get ``_tide_only`` added to the model name.

Rerunning a cycle
^^^^^^^^^^^^^^^^^

When a cycle is run again, CoSMoS skips the models that have a ``.finished``
file in ``job_list``. To run a model again, delete its ``.finished`` file.
To run the whole cycle again, delete the ``job_list`` folder or the whole
cycle folder.

Results of earlier cycles
^^^^^^^^^^^^^^^^^^^^^^^^^

The time series in the web viewer start 48 hours before the current cycle.
CoSMoS takes the first part from the ``timeseries`` folders of earlier cycles,
so keep the cycle folders of at least the last two days when running in
forecast mode.

Old cycle folders and restart files are removed automatically when
``clean_up`` is enabled in the configuration file (see ``clean_up_mode`` and
``prune_after_hours`` in :ref:`Configuration file <configuration>`).