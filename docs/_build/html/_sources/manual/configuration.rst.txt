.. _configuration:

Setting up your configuration file
------------

The CoSMoS configuration file specifies the model database path, the model executable paths, and the webserver, webviewer, and cycle settings:

.. include:: examples/config.toml
       :literal: 

The following webviewer and cycle settings can be included in the configuration file. The cycle configurations can be overwritten when :ref:`initialing CoSMoS <running>`.

.. list-table::
   :widths: 30 70 30
   :header-rows: 1

   * - webviewer settings
     - description
     - default setting

   * - name
     - Choose your own webviewer name.
     - None

   * - version
     - A webviewer template from the folder *configuration/webviewer_templates*.
     - None

   * - **cycle settings**
     - **description**
     - **default setting**

   * - mode
     - Run mode. Options: single_shot ??
     - "single_shot"

   * - interval
     - Cycle time interval (hours)
     - 6

   * - clean_up
     - Clean up folders after each cycle.
     - False

   * - make_flood_maps
     - Make flood map tiles for webviewer.
     - True

   * - make_wave_maps
     - Make wave map tiles for webviewer.
     - True

   * - upload
     - Upload results to webviewer.
     - True

   * - get_meteo
     - Download meteo from webserver.
     - True

   * - run_mode
     - ??
     - "serial"




