.. _configuration:

Setting up your configuration file
------------

The CoSMoS configuration file specifies the model database path, the model executable paths, and the webserver, webviewer, and cycle settings:

.. include:: examples/config.toml
       :literal: 

The following webviewer and cycle settings can be included in the configuration file. The cycle configurations can be overwritten when :ref:`initialing CoSMoS <running>`.

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - webviewer settings
     - Description

   * - name
     - Choose your own webviewer name.

   * - version
     - A webviewer template from the folder *configuration/webviewer_templates*.

   * - **cycle settings**
     - **Description**

   * - mode
     - Run mode. Options: single_shot ??

   * - interval
     - Cycle time interval (hours)

   * - clean_up
     - Clean up folders after each cycle.

   * - make_flood_maps
     - Make flood map tiles for webviewer.

   * - make_wave_maps
     - Make wave map tiles for webviewer.

   * - upload
     - Upload results to webviewer.

   * - get_meteo
     - Download meteo from webserver.





