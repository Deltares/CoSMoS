.. _output:

CoSMoS output
------------

Scenario output
^^^^^^^^^^^^

After running a CoSMoS scenario, the output is stored in the *scenarios* folder. For each new cycle time, a new cycle folder is created. 
An example of an output folder structure is shown below for a scenario called *hurricane_irma* with a cycle that starts on 4 September 2017.

.. include:: examples/scenario_folder.txt
       :literal: 

In the *job_list* folder, you can find an overview of completed models. 
When rerunning a scenario, any models that are marked as finished in the *job_list* folder will not be executed again. 
To rerun specific models or the entire selection for a particular scenario, it is necessary to delete these finished files.

The *models* folder contains all model input and output.
The *tiles* folder contains all tiles for the webviewer.
The *restart* folder contains restart files for all models.
The *timeseries* folder contains timeseries csv files with model output for observation locations defined in the <station> file (see :ref:`Observation stations <stations>`).

.. _webviewer:

Webviewer
^^^^^^^^^^^^

CoSMoS output is presented in a webviewer which provides an interactive method of viewing the results for the different scenarios and model output. 
The webviewer can be found under webviewers/webviewer_name and is structured as follows:

.. include:: examples/webviewer_folder.txt
       :literal: 

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Webviewer file or folder
     - Description

   * - index.html
     - Open this file to view webviewer.

   * - css
     - Main plotting and layout settings

   * - data
     - Model output data

   * - data/scenarios.js
     - Settings for all scenarios (names, locations, zoom levels) included in the webviewer.

   * - data/[scenario_name]/variables.js
     - Variables to include for a certain scenario (e.g., wave heights, water levels, runup)

   * - data/[scenario_name]/stations.js
     - Water level station features (names, locations, link to observation data, link to model output data).

   * - data/[scenario_name]/wavebuoys.js
     - Wave buoy station features (names, locations, link to observation data, link to model output data).

   * - data/[scenario_name]/timeseries
     - Folder with model output and observation timeseries.

   * - data/[scenario_name]/floodmap hm0 precipitation
     - Folders with model map output data (tiles)

   * - html
     - Html codes to plot water level, wave height, and runup timeseries in webviewer.

   * - img
     - Pngs used in the webviewer.

   * - js
     - Main code to generate webviewer.



    

 
