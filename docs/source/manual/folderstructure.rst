.. _folder_structure:

Folder structure
----------------

The CoSMoS run folder is organized as follows:

.. include:: examples/cosmos_folder.txt
       :literal:

- ``configuration/config.toml`` — main configuration file with paths to
  executables, databases, and runtime settings
  (see :ref:`Configuration <configuration>`).
- ``configuration/stations`` — station TOML files defining observation station
  locations (see :ref:`Observation stations <stations>`).
- ``configuration/super_regions`` — super region files for grouping models
  (see :ref:`Super regions <super_regions>`).
- ``configuration/webviewer_templates`` — web viewer templates
  (see :ref:`Web viewer <webviewer>`).
- ``jobs`` — working directory where models are executed.
- ``scenarios`` — scenario input files and model results
  (see :ref:`Setting up a scenario <scenario>`).
- ``webviewers`` — generated web viewers with post-processed results
  (see :ref:`Web viewer <webviewer>`).
- ``model_database`` — model input files and descriptions
  (see :ref:`Model database <models>`).
- ``meteo_database`` — meteorological data sources and files
  (see :ref:`Meteo <meteo>`).
- ``run_cosmos.py`` — example script for running CoSMoS
  (see :ref:`Running a scenario <running>`).
