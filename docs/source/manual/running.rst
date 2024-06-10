.. _running:

Running CoSMoS
------------

With *run_cosmos.py*, CoSMoS can be initialized and run:

.. include:: examples/run_cosmos.py
       :literal: 

This *run_cosmos.py* script requires a *scenario_name* as input (here: *hurricane_laura*). The corresponding scenario file should be located in the folder:
*scenarios/hurricane_laura/scenario.toml*.

Input settings to the *initialize* function of CoSMoS will overwrite :ref:`*cycle* input settings defined in the configuration file <configuration>`.  
All input settings are described in :py:class:`cosmos.cosmos_main.CoSMoS`.

There are two options to execute model runs using CoSMoS:

1. Run all models locally on your PC (**run_mode = "serial"**).
2. Run models on multiple local PCs (**run_mode = "parallel"**). 
   On the main PC (where CoSMoS and the CoastalHazardsToolkit are installed) you need to run the script *run_cosmos.py*. 
   The following script must be executed on other PCs that have access to the same CoSMoS run folder:

   .. include:: examples/run_parallel.py
          :literal: 

   This script *run_parallel.py* will try to run models in the *jobs* folder that contain the text file *ready.txt*. 
   You can run the script for a specific scenario, or assign *None* to the scenario.
   In this case, it will try to run any model in the *jobs* folder that contains a *ready.txt* file.

The *run_mode* setting is defined in :ref:`*config.toml* <configuration>`.
Alternatively, you can overwrite settings in the configuration file when initializing CoSMoS (see *run_cosmos.py*).

