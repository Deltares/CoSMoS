.. _stations:

Observation stations
------------

To compare model results (water levels and wave conditions) with observations, station locations and observation data can be added to the CoSMoS database. 
Station locations can be referenced in the *model.toml* files, while observation data can be referenced in the *scenario.toml* file. 

Station locations
^^^^^^^^^^^^
To add observation points in models, stations must be referenced in a station file located in *configuration/stations*. 
An example of a station file is given below:

 .. include:: examples/ndbc_buoy.xml
       :literal: 

In the :ref:`*model.toml* <models>` file you can refer to one or more station files using the keyword *station*. 
The following attributes can be described in the station file:

.. list-table::
   :widths: 30 70
   :header-rows: 0

   * - name
     - Name of the observation station.

   * - longname
     - Long name of the observation station.

   * - longitude, latitude
     - Coordinates of the observation station.

   * - type
     - Type: wave_buoy or tide_gauge

   * - coops_id
     - Optional: NOAA CO-OPS tide gauge id.

   * - ndbc_id
     - Optional: NDBC wave buoy id.

   * - water_level_correction
     - Optional: Water level correction.

   * - mllw
     - Mean lower low water level (m).

The default *cosmos_run_folder* contains xml files with locations of the NDBC wave buoys and the NOAA CO-OPS water level stations. 
Other observation locations can be added manually. 

Observation data
^^^^^^^^^^^^
Observation data for the station locations defined in the *stations* folder are either automatically extracted by CoSMoS 
or can be manually added to the observations folder. 
For the NOAA CO-OPS water level stations, water levels are automatically extracted from the NOAA CO-OPS server.
For the NDBC wave buoys, the wave buoy data must be manually extracted from the NDBC website (https://www.ndbc.noaa.gov/),
where you can find historical wave buoy data. The following script converts the NDBC text files to csv files that can be used by CoSMoS:

 .. include:: examples/ndbc2csv.py
       :literal: 

Note: this script requires the Coastalhazardstoolkit.

The csv-files must be stored under: 
*observations//[observations_path]//waves//waves.[stationid].observed.csv*

Similarly, other water level or wave data can be added to the observation folder, using the format given below. Note that water level data must be stored using the following format:
*observations//[observations_path]//waterlevels//waterlevel.[stationid].observed.csv*

 .. include:: examples/waves.42060.observed.csv.js
       :literal: 

 .. include:: examples/waterlevel.42060.observed.csv.js
       :literal: 

In the :ref:`scenario file <scenario>`, you must refer to the *observations_path* to include these observations in the webviewer.

