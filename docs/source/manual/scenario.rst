.. _scenario:

Setting up a scenario
------------

A scenario file is a simple toml-structured text file that defines which models you want to run, for which hindcast or forecast period, and with which data sources.

Below, two examples of scenario files are given. The first is a determininistic simulation of hurricane Laura, the second an ensemble run for hurricane Maria.

.. include:: examples/scenario.toml
       :literal: 

.. include:: examples/scenario2.toml
       :literal: 

The scenario file must always be named *scenario.toml*. CoSMoS assigns the scenario *name* based on the folder name 
(see also :ref:`Folder structure <folder_structure>`).

The following settings can be included in the scenario file:

.. list-table::
   :widths: 30 70 30 30
   :header-rows: 1

   * - general settings
     - description
     - default setting
     - unit

   * - long_name
     - Long name as displayed in the webviewer.
     - name
     - 

   * - cycle
     - Cycle start time.
     -
     -

   * - runtime
     - Cycle run time.
     -
     -

   * - description
     - Long description of the scenario.
     - name
     -

   * - runinterval
     - If ran in forecast mode: interval between forecast predictions.
     -
     -

   * - track_ensemble_nr_realizations
     - If ran in ensemble mode: number of cyclone tracks to be generated.
     - 0
     -

   * - **webviewer settings**
     - **description**
     - **default setting**
     - **unit**

   * - lon, lat
     - Longitude and latitude of area of interest (used in webviewer).
     - 0, 0
     - degree

   * - zoom
     - Zoom level for webviewer.
     - 10
     -

   * - observations_path
     - Optional path to local observations of waves and water levels.
     - None
     -

   * - **General model settings**
     - **Can be overwritten by model-specific settings.**
     - **default setting**
     - **unit**

   * - meteo_dataset
     - Meteo dataset to use from meteo_database\\meteo_subsets.xml (see :ref:`Meteo <meteo>`).
     - None
     -

   * - meteo_spiderweb
     - Meteo spiderweb to use from meteo_database\\spiderwebs (see :ref:`Meteo <meteo>`).
     - None
     -

   * - meteo_track
     - Meteo track file (.cyc) to use from meteo_database\\tracks (see :ref:`Meteo <meteo>`).
     - None
     -

   * - wind
     - Wind forcing.
     - True
     -

   * - atmospheric pressure
     - Atmospheric pressure.
     - True
     -

   * - precipitation
     - Precipitation.
     - True
     -

   * - make_flood_map
     - Make flood maps. 
     - False
     -

   * - make_wave_map
     - Make wave maps.
     - False
     -

   * - **[[model]]**
     - **Model-specific settings** (overwrite general model settings)
     - **default setting**
     - **unit**

   * - name
     - Model name as specified in the model folder.
     -
     -

   * - region
     - Instead of model name: region for which all models are run (with same settings). When using the keyword *region* to add models, you must specify the model *type* as indicated in the example scenario file.
     - 
     - 

   * - super_region
     - Instead of model name: super region for which all models are run (with same settings) (see :ref:`Super regions <super_regions>`). When using the keyword *super_region* to add models, you must specify the model *type* as indicated in the example scenario file.
     -
     -

   * - type
     - Model type (optional): delft3dfm, sfincs, beware, hurrywave
     -
     -

   * - **[[cluster]]**
     - **Settings to selectively run models depending on other model output.**
     - **default setting**
     - **unit**

   * - name
     - Name of model cluster.
     -
     -

   * - super_region
     - Super region of models to cluster.
     -
     -

   * - type
     - Which type of models to cluster.
     -
     -

   * - run_condition
     - How to select mmodels within cluster to run conditionally. Option: "topn"
     - "topn"
     -
     
   * - topn
     - Top x number of models to run per cluster
     - 10
     -

   * - hm0fac
     - Factor of Hm0 to add to TWL component. 
     - 0.2
     -

   * - boundary_twl_margin
     - Boundary TWL margin for clustering models.
     - 0.0
     -





