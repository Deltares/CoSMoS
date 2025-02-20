.. currentmodule:: cosmos

API reference
=====

Main classes
^^^^^^^^^^^^
.. autosummary:: 
   :toctree: _generated/  
   
   cosmos.cosmos_main.CoSMoS
   cosmos.cosmos_main_loop.MainLoop
   cosmos.cosmos_model_loop.ModelLoop

Additional classes
^^^^^^^^^^^^
Classes for pre-processing, running, and post-processing.

.. autosummary:: 
   :toctree: _generated/  

   cosmos.cosmos_model.Model
   cosmos.cosmos_scenario.Scenario
   cosmos.cosmos_configuration.Configuration
   cosmos.cosmos_stations.Stations
   cosmos.cosmos_webviewer.WebViewer
..   cosmos.cosmos_cluster.Cluster

Model-specific classes
^^^^^^^^^^^^
.. autosummary:: 
   :toctree: _generated/  

   cosmos.cosmos_delft3dfm.CoSMoS_Delft3DFM
   cosmos.cosmos_hurrywave.CoSMoS_HurryWave
   cosmos.cosmos_sfincs.CoSMoS_SFINCS
   cosmos.cosmos_xbeach.CoSMoS_XBeach
..   cosmos.cosmos_beware.CoSMoS_BEWARE

CoSMoS functions
^^^^^^^^^^^^
.. autosummary:: 
   :toctree: _generated/  
   
   cosmos.cosmos_main.CoSMoS.initialize
   cosmos.cosmos_main.CoSMoS.run
   cosmos.cosmos_main.CoSMoS.stop
   cosmos.cosmos_main.CoSMoS.log
   cosmos.cosmos_main.CoSMoS.make_webviewer
   cosmos.cosmos_main.CoSMoS.post_process

MainLoop and ModelLoop functions
^^^^^^^^^^^^
.. autosummary:: 
   :toctree: _generated/  
   
   cosmos.cosmos_main_loop.MainLoop.run
   cosmos.cosmos_main_loop.MainLoop.start
   cosmos.cosmos_model_loop.ModelLoop.run
   cosmos.cosmos_model_loop.ModelLoop.start
   cosmos.cosmos_model_loop.ModelLoop.stop

Model functions
^^^^^^^^^^^^
.. autosummary:: 
   :toctree: _generated/  
   
   cosmos.cosmos_model.Model.read_generic
   cosmos.cosmos_model.Model.set_paths
   cosmos.cosmos_model.Model.get_nested_models
   cosmos.cosmos_model.Model.get_all_nested_models
   cosmos.cosmos_model.Model.add_stations
   cosmos.cosmos_model.Model.get_peak_boundary_conditions
   cosmos.cosmos_sfincs.CoSMoS_SFINCS.read_model_specific
   cosmos.cosmos_sfincs.CoSMoS_SFINCS.pre_process
   cosmos.cosmos_sfincs.CoSMoS_SFINCS.move
   cosmos.cosmos_sfincs.CoSMoS_SFINCS.post_process
   cosmos.cosmos_delft3dfm.CoSMoS_Delft3DFM.read_model_specific
   cosmos.cosmos_delft3dfm.CoSMoS_Delft3DFM.pre_process
   cosmos.cosmos_delft3dfm.CoSMoS_Delft3DFM.move
   cosmos.cosmos_delft3dfm.CoSMoS_Delft3DFM.post_process
   cosmos.cosmos_hurrywave.CoSMoS_HurryWave.read_model_specific
   cosmos.cosmos_hurrywave.CoSMoS_HurryWave.pre_process
   cosmos.cosmos_hurrywave.CoSMoS_HurryWave.move
   cosmos.cosmos_hurrywave.CoSMoS_HurryWave.post_process
   cosmos.cosmos_xbeach.CoSMoS_XBeach.read_model_specific
   cosmos.cosmos_xbeach.CoSMoS_XBeach.pre_process
   cosmos.cosmos_xbeach.CoSMoS_XBeach.move
   cosmos.cosmos_xbeach.CoSMoS_XBeach.post_process
..   cosmos.cosmos_beware.CoSMoS_BEWARE.read_model_specific
   cosmos.cosmos_beware.CoSMoS_BEWARE.pre_process
   cosmos.cosmos_beware.CoSMoS_BEWARE.move
   cosmos.cosmos_beware.CoSMoS_BEWARE.post_process

