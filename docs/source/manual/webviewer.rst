.. _webviewer:

Web viewer
----------

CoSMoS output is presented in an interactive web viewer for viewing results
across scenarios and models. The web viewer is located in
``webviewers/<webviewer_name>`` and is automatically populated with post-processed
model results. To view results, open ``index.html`` in a web browser.

Web viewer folder structure:

.. include:: examples/webviewer_folder.txt
       :literal:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - File or folder
     - Description

   * - index.html
     - Open this file to view the web viewer.

   * - css
     - Plotting and layout settings.

   * - data
     - Model output data.

   * - data/scenarios.js
     - Settings for all scenarios (names, locations, zoom levels).

   * - data/[scenario_name]/variables.js
     - Variables to display (e.g. wave heights, water levels, runup).

   * - data/[scenario_name]/stations.js
     - Water level station features (names, locations, links to data).

   * - data/[scenario_name]/wavebuoys.js
     - Wave buoy station features (names, locations, links to data).

   * - data/[scenario_name]/timeseries
     - Model output and observation time series files.

   * - data/[scenario_name]/floodmap, hm0, precipitation
     - Map tile folders for spatial output layers.

   * - html
     - HTML templates for time series plots.

   * - img
     - Static images (logos, markers, infographics).

   * - js
     - JavaScript code that drives the web viewer.

The web viewer name and template version are configured in the
:ref:`configuration file <configuration>` under ``[webviewer]``. Web viewer
templates are stored in ``configuration/webviewer_templates``.

If ``upload = true`` is set in the configuration, CoSMoS automatically uploads
the web viewer to the configured web server after each cycle.
