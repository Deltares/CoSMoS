.. _models:

Adding models to the database
------------


Model database
^^^^^^^^^^^^
The CoSMoS model database contains all model input files. The path to your model database must be specified in the :ref:`*config.toml* <configuration>` file. 
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
     - Model long name (shown in webviewer)
     - name
     -

   * - runid
     - Model id used in CoSMoS.
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
     - List of station toml files (located in cosmos//stations) added as observation points in model.
     -
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

   * - mhhw
     - Mean Higher High Water to estimate total water level for clustering of models.
     - 0
     - m


Model-specific input
^^^^^^^^^^^^

There are currently five types of models that can be included in CoSMoS. 
The specific input for these models is described below.

BEWARE
"""""""""""""""

BEWARE is a meta-model based on XBeach for predicting nearshore wave heights and total water levels at reef-lined coasts.

The BEWARE executable folder, whose location is specified in the :ref:`*config.toml* <configuration>` file, must contain the following files:

- XBeach_BEWARE_database.nc: the database of XBeach runup and wave condition predictions.
- run_bw.bas: file to run *run_beware.py*.
- run_beware.py: script to run BEWARE. To be able to run *run_beware.py*, you must have installed the Coastal Hazards Toolkit in an environment called cosmos. 

The BEWARE input folder in your model database must contain the following information:

- *beware.inp*: BEWARE input file
- *r2matchfile* as specified in *beware.inp*: a *.mat* that describes the matching probabilities for each input profile.
- *profsfile* as specified in *beware.inp*: a profile describing the characteristics of the BEWARE input profiles. The profsfile must contain the following information:

  - profid: ID of profile.
  - x_off: Offshore x-coordinate (for nesting in wave model).
  - y_off: Offshore y-coordinate (for nesting in wave model).
  - x_coast: X-coordinate of intersection with the coastline (for plotting total water levels).
  - y_coast: Y-coordinate of intersection with the coastline (for plotting total water levels).
  - x_flow: Nearshore x-coordinate for nesting in flow model (to include surge in total water level estimation).
  - y_flow: Nearshore y-coordinate for nesting in flow model (to include surge in total water level estimation).
  - beachslope: Beach slope of transect for total water level prediction.

- *runup.x* and *runup.y*: files describing the x and y coordinates (in the coordinate system as specified in the *model.toml* file) for different runup levels (here between 0 and 15 m). The format is as follows:
 
.. code-block:: text

	    <runup_level1> <runup_level1> <runup_level3>  
	
	    <profid> <x runup_level1> <x runup_level1> <x runup_level3>  

      e.g.
      0 2 4
      29 163960.98 163961.75 164154.9
      35 163961.98 163962.75 164156.9

Delft3D-FM
"""""""""""""""

`Delft3D-FM <https://www.deltares.nl/en/software-and-data/products/delft3d-flexible-mesh-suite>`_ can be run as separate flow model, or as coupled flow-wave model. 
The Delft3D-FM *input* folder must contain the following folders and files:

- *flow* folder containing flow model input. The *.mdu* file name must be equal to the *runid* keyword specified in the *model.toml* file.
- *wave* folder containing wave model input. The *.mdw* file must be called *wave.mdw*. The grid for which you want to generate output timeseries must be called *wave.grd*. You can also add a nested model called *nest.grd*.
The following settings in the *.mdw* are adjusted by CoSMoS:

  - ReferenceDate         = REFDATEKEY
  - LocationFile          = OBSFILEKEY
- *dimr_config.xml* file that describes the working directories for the flow and wave models. The <time> (starttime of the simulation) is set by CoSMoS by replacing the keyword *TIMEKEY*.

The *misc* folder must contain a text file with the same name as the model name, containing the coordinates of the model outline.

HurryWave
"""""""""""""""
HurryWave is a computationally efficient third generation spectral wave model, with physics similar to those of SWAN and WAVEWATCH III.

HurryWave model input files are located in the *input* folder of your HurryWave model directory. 
In the *tiling* folder, *indices* and *topobathy* folders must be included to generate wave maps.

The *misc* folder must contain a text file with the same name as the model name, containing the coordinates of the model outline.

SFINCS
"""""""""""""""

`SFINCS <https://sfincs.readthedocs.io/en/latest/>`_ model input files are located in the *input* folder of your SFINCS model directory. 
In the *tiling* folder, *indices* and *topobathy* folders must be included to generate flood maps.

The *misc* folder must contain a text file with the same name as the model name, containing the coordinates of the model outline.

XBeach
"""""""""""""""

`XBeach <https://xbeach.readthedocs.io/en/latest/>`_ model input files are located in the *input* folder of your XBeach model directory. 
In the *tiling* folder, an *indices* folder must be included to generate pre and post-storm bed level maps.

The *misc* folder must contain a text file with the same name as the model name, containing the coordinates of the model outline.
