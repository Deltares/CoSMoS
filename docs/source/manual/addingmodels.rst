.. _models:

Adding models to the database
------------

The CoSMoS model database contains all model input files. 
CoSMoS automatically nests the models and collects the required meteorological data. Therefore, the model folders contain only the grid and input files for the individual models.
A separate toml file describes, among other things, in which model it is nested and which meteo sources and observation stations are to be used:

.. include:: examples/model.toml
       :literal: 

Within CoSMoS, the name of your model is equal to the folder name in which the *model.toml* file is located 
(see also :ref:`Folder structure <folder_structure>`).

The following settings can be included in the model file:

.. list-table::
   :widths: 30 70 30 30
   :header-rows: 1

   * - parameter
     - description
     - default
     - unit

   * - longname
     - Model long name
     - name
     -

   * - runid
     - Model id used in CoSMoS
     - None
     -

   * - type
     - Model type (options: beware, delft3dfm, hurrywave, sfincs, xbeach)
     -
     -

   * - crs
     - Coordinate system
     -
     -

   * - flow
     - Run flow model.
     - False
     -

   * - wave
     - Run wave model.
     - False
     -

   * - priority
     - Optional to define order in which models are run.
     - 10
     -

   * - flow_nested
     - Name of model in which current model is nested (flow)   
     - None
     -

   * - wave_nested
     - Name of model in which current model is nested (waves) 
     - None
     -

   * - bw_nested
     - Name of model in which current model is nested (BEWARE) 
     - None
     -  
  
   * - flow_spinup_time 
     - Spinup time (flow)   
     - 0
     - hours

   * - wave_spinup_time 
     - Spinup time (waves)  
     - 0  
     - hours

   * - vertical_reference_level_name
     - Name of vertical reference level
     - 'MSL'
     -

   * - vertical_reference_level_difference_with_msl
     - Difference of vertical reference level with MSL
     - 0
     - m

   * - boundary_water_level_correction 
     - Water level correction at boundary
     - 0
     - m

   * - station
     - Station xml file (located in cosmos//stations) added as observation points in model.
     -
     -

   * - meteo_dataset
     - Meteo dataset to use from meteo\\meteo_subsets.xml (see :ref:`Meteo <meteo>`).
     - None
     -

   * - meteo_spiderweb
     - Meteo spiderweb to use from meteo\\spiderwebs (see :ref:`Meteo <meteo>`).
     - None
     -

   * - meteo_wind
     - Add wind forcing.
     - True
     -

   * - meteo_atmospheric_pressure
     - Add atmospheric pressure forcing.
     - True
     -

   * - meteo_precipitation
     - Add precipitation.
     - True
     -

   * - polygon
     - ??
     - None   
     -      

   * - make_wave_map
     - Make wave maps 
     - False 
     -

   * - make_flood_map
     - Make flood maps
     - False
     -

   * - make_sedero_map
     - Make sedimentation/erosion maps
     - False
     -

   * - sa_correction
     - Solar annual correction for tidal constituents. 
     - None
     -

   * - ssa_correction
     - Solar semiannual correction for tidal constituents.
     - None
     -

   * - mhhw
     - Mean Higher High Water to estimate total water level
     - 0
     - m

   * - cluster
     - ?? Name of cluster that model belongs to.
     - None
     -

   * - boundary_twl_threshold
     - Total water level threshold to cluster models.
     - 999
     - m

   * - zb_deshoal
     - ?? Depth to which nearshore wave heights are deshoaled.
     - None
     -

   * - ensemble
     - Run in ensemble mode.
     - False
     -


