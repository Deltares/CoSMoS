.. _scenario:

Setting up a scenario
------------

A scenario file is a simple toml-structured text file that defines which models you want to run, for which hindcast or forecast period, with which data sources.

An example of a scenario file is given below:

.. include:: examples/scenario.toml
       :literal: 

The scenario file must always be named *scenario.toml*. CoSMoS assigns the scenario *name* based on the folder name 
(see also :ref:`Folder structure <folder_structure>`).

The following settings can be included in the scenario file:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - General settings
     - Description

   * - longname
     - Long name as displayed in the webviewer.

   * - cycle
     - Cycle start time.

   * - runtime
     - Cycle run time.

   * - description
     - Long description of the scenario.

   * - runinterval
     - If ran in forecast mode: interval between forecast predictions.

   * - track_ensemble
     - If ran in ensemble mode: meteo folder with .cyc file.

   * - track_ensemble_nr_realizations
     - If ran in ensemble mode: number of cyclone tracks to be generated.

   * - **Webviewer settings**
     - **Description**

   * - lon, lat
     - Longitude and latitude of area of interest (used in webviewer).

   * - zoom
     - Zoom level for webviewer.

   * - observations_path
     - Optional path to local observations of waves and water levels.

   * - **General model settings**
     - **Can be overwritten by model-specific settings.**

   * - meteo_dataset
     - Meteo dataset to use from meteo\\meteo_subsets.xml (see :ref:`Meteo <meteo>`).

   * - meteo_spiderweb
     - Meteo spiderweb to use from meteo\\spiderwebs (see :ref:`Meteo <meteo>`).

   * - wind
     - Yes or no for wind forcing.

   * - atmospheric pressure
     - Yes or no for atmospheric pressure.

   * - precipitation
     - Yes or no for precipitation.

   * - ensemble
     - Yes or no to run model in ensemble mode.

   * - make_flood_map
     - Yes or no to make flood maps. 

   * - make_wave_map
     - Yes or no to make wave maps.

   * - **[[model]]**
     - **Model-specific settings** (overwrite general model settings)

   * - name
     - Model name as specified in the model folder.

   * - region
     - Instead of model name: region for which all models are run (with same settings).

   * - super_region
     - Instead of model name: super region for which all models are run (with same settings) (see :ref:`Super regions <super_regions>`).

   * - type
     - Model type (optional): delft3dfm, sfincs, beware, hurrywave

   * - **[[cluster]]**
     - **Settings to selectively run models depending on other model output.**

   * - name
     - Name of model cluster.

   * - super_region
     - Super region of models to cluster.

   * - type
     - Which type of models to cluster.

   * - run_condition
     - ?

   * - topn
     - ?

   * - hm0fac
     - ?

   * - boundary_twl_margin
     - ?





