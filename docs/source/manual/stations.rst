.. _stations:

Observation stations
------------

To compare model results (water levels and wave conditions) with observations, station locations and observation data can be added to the CoSMoS database. 
Station locations can be referenced in the model xml files, while observation data can be referenced in the scenario xml file. 


Station locations
^^^^^^^^^^^^
To add observation points to a specific model, station locations files can be used. 
An example of a station file is given below:

 .. include:: examples/ndbc_buoy.xml
       :literal: 

The station location files must be added to the *stations* folder. In the model xml file (see :ref:`Models <models>`) you can refer to one 
or more station files using the keyword <station>.

The default cosmos_run_folder contains xml files with locations of the NDBC wave buoys and the NOAA CO-OPS water level stations. 
Other observation locations can also be added manually. 

Observation data
^^^^^^^^^^^^
Observation data for the station locations defined in the *stations* folder are either automatically extracted by CoSMoS 
or can be manually added to the observations folder. 
For the NOAA-COOPS water level stations, water levels are automatically extracted from the NOAA-COOPS server.
For the NDBC wave buoys, the wave buoy data must be manually extracted from the NDBC website (https://www.ndbc.noaa.gov/),
where you can find historical wave buoy data. The following script converts the NDBC text files to csv files that can be used by CoSMoS:

 .. include:: examples/ndbc2csv.py
       :literal: 

Note: this script requires the Coastalhazardstoolkit.

The csv-files must be stored under: 
*observations//[observations_path]//waves//waves.[stationid].observed.csv*

Similarly, other water level or wave data can be added to the observation folder, using the format given below. Note that water level data must be stored using the following format:
*observations//[observations_path]//waterlevels//waterlevels.[stationid].observed.csv*

 .. include:: examples/waves.42060.observed.csv.js
       :literal: 

In the scenario file, you must refer to the [observations_path] (see :ref:`Scenario <scenario>`) to include these observations in the webviewer.

