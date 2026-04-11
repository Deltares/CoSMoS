.. _scenario:

Scenario configuration
----------------------

A scenario file defines which models to run, the simulation period, and the
meteorological forcing to apply. It is a TOML-formatted text file located at
``scenarios/<scenario_name>/scenario.toml``. The scenario name is derived from
the folder name (see :ref:`Folder structure <folder_structure>`).

Below are two examples: a deterministic simulation of Hurricane Laura and an
ensemble run for Hurricane Maria.

.. include:: examples/scenario.toml
       :literal:

.. include:: examples/scenario2.toml
       :literal:

General settings
^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 25 55 10 10
   :header-rows: 1

   * - Parameter
     - Description
     - Default
     - Unit

   * - long_name
     - Display name shown in the web viewer.
     - name
     -

   * - description
     - Textual description of the scenario.
     - name
     -

   * - cycle
     - Starting cycle time (e.g. ``"20231213_00z"``). If omitted, CoSMoS
       determines the cycle automatically.
     -
     -

   * - runtime
     - Simulation duration.
     -
     - hours

   * - runinterval
     - Interval between forecast cycles (forecast mode only).
     -
     - hours

   * - track_ensemble_nr_realizations
     - Number of synthetic cyclone tracks for ensemble mode. Setting this
       value enables ensemble mode.
     - 0
     -

Web viewer settings
^^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 25 55 10 10
   :header-rows: 1

   * - Parameter
     - Description
     - Default
     - Unit

   * - lon, lat
     - Initial map centre coordinates for the web viewer.
     - 0, 0
     - degrees

   * - zoom
     - Initial map zoom level.
     - 10
     -

   * - observations_path
     - Path to local observation data (water levels and waves).
     - None
     -

Meteorological forcing
^^^^^^^^^^^^^^^^^^^^^^

These settings apply to all models in the scenario unless overridden per model.
See :ref:`Meteorological forcing <meteo>` for details.

.. list-table::
   :widths: 25 55 10 10
   :header-rows: 1

   * - Parameter
     - Description
     - Default
     - Unit

   * - meteo_dataset
     - Gridded dataset name from ``meteo_database.toml``.
     - None
     -

   * - meteo_spiderweb
     - Spiderweb file name (without extension) from ``spiderwebs`` folder.
     - None
     -

   * - meteo_track
     - Cyclone track file (``.cyc``) from ``tracks`` folder.
     - None
     -

   * - wind
     - Enable wind forcing.
     - true
     -

   * - atmospheric_pressure
     - Enable atmospheric pressure forcing.
     - true
     -

   * - precipitation
     - Enable precipitation forcing.
     - true
     -

   * - make_flood_map
     - Generate flood map tiles for all applicable models.
     - false
     -

   * - make_wave_map
     - Generate wave map tiles for all applicable models.
     - false
     -

Model selection
^^^^^^^^^^^^^^^

Models are added to the scenario using ``[[model]]`` sections. Each section
can specify an individual model by name, or select multiple models by region
or super region.

.. list-table::
   :widths: 25 55 10 10
   :header-rows: 1

   * - Parameter
     - Description
     - Default
     - Unit

   * - name
     - Name of an individual model (must match a folder in the model database).
     -
     -

   * - region
     - Select all models in a given region. Requires ``type`` to be specified.
     -
     -

   * - super_region
     - Select all models in a super region (see
       :ref:`Regions and super regions <super_regions>`). Requires ``type``.
     -
     -

   * - type
     - Model type filter: ``sfincs``, ``hurrywave``, ``delft3dfm``, ``xbeach``,
       ``beware``.
     -
     -

Per-model ``meteo_dataset``, ``meteo_spiderweb``, and ``meteo_track`` settings
can be specified within a ``[[model]]`` section to override the scenario-level
defaults.

Model clustering
^^^^^^^^^^^^^^^^

Clusters allow selective execution of models based on boundary water level
conditions. They are defined using ``[[cluster]]`` sections.

.. list-table::
   :widths: 25 55 10 10
   :header-rows: 1

   * - Parameter
     - Description
     - Default
     - Unit

   * - name
     - Cluster identifier.
     -
     -

   * - super_region
     - Super region whose models are included in this cluster.
     -
     -

   * - type
     - Model type(s) to cluster.
     -
     -

   * - run_condition
     - Selection strategy. Currently supported: ``"topn"``.
     - topn
     -

   * - topn
     - Maximum number of models to run within the cluster.
     - 10
     -

   * - hm0fac
     - Wave height factor added to the total water level estimate.
     - 0.2
     -

   * - boundary_twl_margin
     - Margin applied to the boundary total water level threshold.
     - 0.0
     - m
