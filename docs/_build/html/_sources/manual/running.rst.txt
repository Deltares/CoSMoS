.. _running:

Running CoSMoS
------------

The script below gives an example of how CoSMoS can be initialized.

.. include:: examples/run_cosmos.py
       :literal: 

This *run_cosmos.py* script requires a *scenario_name* as input (here: *hurricane_laura*). The corresponding scenario file should be located in the folder:
*scenarios/hurricane_laura/scenario.toml*.

Input settings to the *initialize* function of CoSMoS will overwrite :ref:`*cycle* input settings defined in the configuration file <configuration>`. 
All input settings are described in :py:class:`cosmos.cosmos_main.CoSMoS`.



