.. _models:

Adding models to the database
------------

The CoSMoS model database contains all model input files. 
CoSMoS automatically nests the models and collects the required meteorological data. Therefore, the model folders contain only the grid and input files for the individual models.
A separate xml file describes, among other things, in which model it is nested and which meteo sources and observation stations are to be used:

.. include:: examples/model.toml
       :literal: 

Within CoSMoS, the name of your model is equal to the folder name in which the *model.toml* file is located 
(see also :ref:`Folder structure <folder_structure>`).

The following settings can be included in the model file:

.. list-table::
   :widths: 30 70
   :header-rows: 0

   * - longname
     - Model long name

   * - runid
     - Model id used in CoSMoS

   * - type
     - Model type (options: beware, delft3dfm, hurrywave, sfincs, xbeach)

   * - coordsys
     - Coordinate system

   * - coordsystype
     - projected or geographic

   * - priority
     - Optional to define order in which models are run.

   * - wavenested
     - Name of model in which current model is nested (waves)    

   * - flownested
     - Name of model in which current model is nested (flow)   

   * - wavespinup
     - Spinup time (hours) (waves)    

   * - flowspinup
     - Spinup time (hours) (flow)   

   * - vertical_reference_level_name
     - Name of vertical reference level

   * - vertical_reference_level_difference_with_msl
     - Difference of vertical reference level with MSL (m)    

   * - station
     - Station xml file (located in cosmos//stations) added as observation points in model.

   * - make_wave_map
     - Yes or no to make wave maps  

   * - make_flood_map
     - Yes or no to make flood maps

   * - make_sedero_map
     - Yes or no to make sedimentation/erosion maps


