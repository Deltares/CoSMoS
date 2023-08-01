.. _meteo:

Meteo collection
------------
CoSMoS automatically downloads, collects and writes meteorological data for each model based on user-defined settings in the :ref:`scenario file <scenario>`. 
The path to your meteo database must be specified in the :ref:`*config.toml* <configuration>` file. An example of a meteo folder structure is given below:

.. include:: examples/meteo_folder.txt
       :literal: 

This example meteo folders shows the three main types of meteo data:

- **Regularly gridded meteo data** (keyword: *meteo_dataset* in scenario file). The *gfs_forecast_0p25_north_atlantic* and *gfs_anl_0p50_north_atlantic* folders are examples of regularly gridded meteo data.
- **Spiderweb grid meteo data** (keyword: *meteo_spiderweb* in scenario file). The *irma.spw* file in the folder *spiderwebs* is an example of spiderweb forcing.
- **Ensemble of tracks** (keyword: *meteo_track* in scenario file). The *irma.cyc* file in the folder *tracks* is an example of cyclone file. 

Metadata for the *meteo_datasets*, *spiderweb*, and *track* files are contained in the *meteo_subsets.xml* file:

.. include:: examples/meteo_subsets.xml
       :literal:

The following attributes can be included in the meteo subsets:

.. list-table::
   :widths: 30 70 30 30
   :header-rows: 0

   * - name
     - Name of the meteo dataset
     - default setting
     - unit

   * - source
     - Source of meteo dataset. Options: gfs_anl_0p50, gfs_forecast_0p25, coamps_analysis, coamps_tc_hindcast, coamps_tc_forecast, alternative
     -
     - 

   * - x_range, y_range
     - Optional: X and Y range for which meteo data needs to be downloaded / collected (in EPSG 4326).
     - None
     - Degree

   * - xystride
     - Optional: ??
     - 1
     - 



Regularly gridded meteo data
^^^^^^^^^^^^

Regularly gridded meteorological datasets contain *netcdf* files with the following information:

.. list-table::
   :widths: 30 70 30 30
   :header-rows: 1

   * - parameter
     - description
     - dimensions
     - unit

   * - lat
     - Latitude
     - lat
     - degree

   * - lon
     - Longitude
     - lon
     - degree

   * - wind_u
     - Wind speed in x direction
     - [lon, lat]
     - ??
    

   * - wind_v
     - Wind speed in y direction
     - [lon, lat]
     - ??

   * - barometric_pressure
     - Barometric pressure
     - [lon, lat]
     - ??

   * - precipitation
     - Precipitation
     - [lon, lat]
     - ??

The netcdf files must be named as follows:

<dataset_name>.<yyyymmdd_hhmm>.nc. 

For forecasts, the netcdf files are contained in a folder with the cycle time name (see meteo folder structure above).   

CoSMoS gets the meteo data in two steps:

- Download
    If the keyword *get_meteo* is set to True (see :py:class:`cosmos.cosmos.CoSMoS`), meteo data are downloaded from a webserver. The following datasets can be downloaded automatically:
    
   .. list-table::
      :widths: 30 70
      :header-rows: 1
      
      * - dataset
        - description

      * - gfs_anl_0p50
        - Global Forecast System (GFS) analysis

      * - gfs_forecast_0p25
        - Global Forecast System (GFS) forecast

      * - coamps_analysis
        - Coupled Ocean/Atmosphere Mesoscale Prediction System (COAMPS) analysis

      * - coamps_tc_hindcast
        - Coupled Ocean/Atmosphere Mesoscale Prediction System (COAMPS) tropical cyclone hindcast

      * - coamps_tc_forecast
        - Coupled Ocean/Atmosphere Mesoscale Prediction System (COAMPS) tropical cyclone hindcast

- Collect
    CoSMoS loops through the *meteo_subset.xml* data and finds subsets that match the *meteo_dataset* specified in the scenario file. 
    For each *meteo_subset*, CoSMoS collects the data from the netcdf files that are located in the specific meteo folder. 
    The individual CoSMoS model classes (see :ref:`Model classes <modelclasses>`) then write the meteo input files.

Spiderweb forcing
^^^^^^^^^^^^

For cyclone forecasting, spiderweb grids are commonly used. 
Spiderwebs are circular grids, for which each time in the time series of space varying wind and pressure (and potentially precipitation) 
the position of the cyclone eye must be given. For more information, see also the `Tropical Cyclone Toolbox <https://publicwiki.deltares.nl/display/DDB/Tropical+Cyclone>`_ and the `Delft3D-FLOW manual <https://oss.deltares.nl/web/delft3d/manuals>`_.  

When using a single spiderweb as forcing, use the keyword: *<meteo_spiderweb>* in the scenario file, 
indicating the name of the spiderweb (without extension) that is located in the *spiderwebs* folder of your meteo database.

Track ensemble
^^^^^^^^^^^^
To include track uncertainties in cyclone forecasting, CoSMoS can also generate an ensemble of tracks. 
In this way, we can obtain a probabilistic estimate of nearshore water levels, waves, and inundation. 
The cyclone tracks are generated based on De Maria et al. (2009), taking into account along-track (AT), cross-track (CT), and maximum wind speed (VE) errors.
For more information, see the `Advanced Tropical Cyclone Toolbox <https://publicwiki.deltares.nl/display/DDB/Advanced+Tropical+Cyclone>`_.

- To run a scenario in ensemble mode, set the keyword *ensemble* to True (see :ref:`Running CoSMoS <running>` and :py:class:`cosmos.cosmos.CoSMoS`).
- The keyword *track_ensemble_nr_realizations* in the scenario file specifies the number of tracks that need to be generated. CoSMoS starts running in ensemble mode if this keyword is defined.
- There are two options for meteo ensemble forcing:

  - The keyword *meteo_dataset* is defined in the scenario file: a cyclone track is estimated from regularly gridded wind field data. This track is then used to generate an ensemble of tracks.
  - The keyword *meteo_track* is defined in the scneario file: a track ensemble is generated based on this best track file.

CoSMoS determines which models to run in ensemble mode based on the cone of the generated tracks. All models that lie within this cone are run for the track ensemble.

