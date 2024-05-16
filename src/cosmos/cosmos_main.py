# -*- coding: utf-8 -*-
"""
Created on Mon May 10 12:18:09 2021

@author: ormondt
"""

import os
import datetime

import cht.misc.fileops as fo


class CoSMoS:

    """This is the main CoSMoS class.

    Parameters
    ----------
    initialize : func
        Initialize cosmos based on main folder input
    run : func
        Run cosmos scenario
    stop : func
        Stop cosmos scenario
    log : func
        Make log of cosmos scenario
    make_webviewer : func
        Just make webviewer for cosmos scenario
    post_process : func
        Just post-process cosmos results

    See Also
    -------
    cosmos.cosmos_main_loop.MainLoop
    cosmos.cosmos_model.Model
    cosmos.cosmos_beware.CoSMoS_BEWARE
    cosmos.cosmos_delft3dfm.CoSMoS_Delft3DFM
    cosmos.cosmos_hurrywave.CoSMoS_HurryWave
    cosmos.cosmos_sfincs.CoSMoS_SFINCS
    cosmos.cosmos_xbeach.CoSMoS_XBeach

    """
    
    def __init__(self):

        os.environ['HDF5_DISABLE_VERSION_CHECK'] = '2'
        
#        self.config          = Config()
        # self.cycle_time      = None        
        # self.cycle_stop_time = None  
        # self.storm_flag      = False
        # self.storm_keeplist  = []

    def initialize(self, main_path, **kwargs):
        """Initialize CoSMoS configuration based on configuration file and input arguments.

        Parameters
        ----------
        main_path : str
            Path of CoSMoS main folder.
        scenario_name : str
            Name of the scenario to be run.
        config_file : str, optional
            Configuration file in folder 'configurations', by default "config.toml"
        mode : str, optional
            _description_, by default "single"
        run_models : bool, optional
            Option to run models, by default True
        make_flood_maps : bool, optional
            Option to make flood maps, by default True
        make_wave_maps : bool, optional
            Option to make wave maps, by default True
        make_water_level_maps : bool, optional
            Option to make water level maps, by default True
        make_sedero_maps : bool, optional
            Option to make sedero maps, by default False
        get_meteo : bool, optional
            Option to upload results, by default True
        make_figures : bool, optional
            Option to make figures, by default True
        upload : bool, optional
            Option to upload results, by default False
        ensemble : bool, optional
            Option to run in ensemble mode, by default False
        webviewer : str, optional
            Webviewer version, by default None
        just_initialize : bool, optional
            Only initialize cosmos models, by default False
        clean_up : bool, optional
            Option to clean up job folder, by default False
        cycle : str, optional
            Cycle to start with (e.g. 20231213_00z), by default None

        See Also
        -------
        cosmos.cosmos_configuration.Configuration

        """
        from .cosmos_configuration import Configuration

        self.config          = Configuration()

        # Set main path        
        self.config.path.main = main_path

        self.config.file_name = "config.toml"
        for key, value in kwargs.items():
            if key == "config_file":
                self.config.file_name = value       
                break

        # Read in configuration
        self.config.set(**kwargs)

    def run(self, scenario_name=None, cycle=None):

        """Run a CoSMoS scenario:
    
        - Initialize cosmos_main_loop and cosmos_model_loop
        - Start cosmos_main_loop

        Parameters
        ----------
        scenario_name : str
            Name of the scenario to be run.
        cycle : str, optional
            Cycle to start with (e.g. 20231213_00z), by default None
        
        See Also
        -------
        cosmos.cosmos_main_loop.MainLoop
        cosmos.cosmos_model_loop.ModelLoop
        cosmos.cosmos_webviewer.WebViewer

        """

        # Determine which cycle is needs to be run
        # If no cycle is given, then it will be determined later on        
        self.scenario_name = scenario_name

        if cycle:
            cycle = datetime.datetime.strptime(cycle, "%Y%m%d_%HZ").replace(tzinfo=datetime.timezone.utc)        
        
        if not self.config.path.main:
            cosmos.log("Error: CoSMoS main path not set! Do this by running cosmos.initialize(main_path) or passing main_path as input argument to cosmos.run().")
            return

        from .cosmos_main_loop import MainLoop
        from .cosmos_model_loop import ModelLoop
        self.main_loop  = MainLoop()
        self.model_loop = ModelLoop()

        self.main_loop.just_initialize = self.config.cycle.just_initialize
        self.main_loop.run_models      = self.config.cycle.run_models
        # self.main_loop.clean_up        = self.config.cycle.clean_up
        
        self.main_loop.start(cycle=cycle)


    def stop(self): 
        """Stop main loop and model loop.
        """  
        self.model_loop.scheduler.cancel()
        self.main_loop.scheduler.cancel()

    def log(self, message:str):  
        """Write log message to cosmos.log

        Parameters
        ----------
        message : str
            Log message
        """
        print(message)
        log_file = os.path.join(self.config.path.main, "cosmos.log")
        tstr = "[" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + " UTC] "
        with open(log_file, 'a') as f:
            f.write(tstr + message + "\n")
            f.close()

    def make_webviewer(self, scenario_name:str):   
        """Just make webviewer

        Parameters
        ----------
        scenario_name : str
            Scenario name
        
        See Also
        -------
        cosmos.cosmos_main_loop.MainLoop
        cosmos.cosmos_model_loop.ModelLoop
        cosmos.cosmos_webviewer.WebViewer

        """
        
        if not cosmos.config.path.main:
            cosmos.log("Error: CoSMoS main path not set! Do this by running cosmos.initialize(main_path) or passing main_path as input argument to cosmos.run().")
            return
        
        self.config.cycle.just_initialize  = True
        self.config.cycle.run_models = False
        self.run(scenario_name)
                
        from .cosmos_webviewer import WebViewer
        
        wv = WebViewer(cosmos.config.webviewer.name)
        wv.make()

        # Delete job folder that was just created
        if cosmos.config.cycle.run_mode != "parallel":
            fo.rmdir(os.path.join(cosmos.config.path.jobs,
                                  cosmos.scenario_name))
        
        if cosmos.config.cycle.upload:
            wv.upload()

    def post_process(self, scenario_name:str, model=None, cycle:str=None):   
        """Just post-process model results. 

        Parameters
        ----------
        scenario_name : str
            Scenario name
        model : list or 'all', optional
            Which models to post-process, by default None
        cycle : _type_, optional
            Cycle name, by default None       
    
        See Also
        -------
        cosmos.cosmos_main_loop.MainLoop
        cosmos.cosmos_model_loop.ModelLoop

        """
                
        if not cosmos.config.path.main:
            cosmos.log("Error: CoSMoS main path not set! Do this by running cosmos.initialize(main_path) or passing main_path as input argument to cosmos.run().")
            return
        
        # Overwrite settings for just_initialize and run_models
        self.config.cycle.just_initialize  = True
        self.config.cycle.run_models = False
        self.run(scenario_name)
        
        mdls = []
        if model == "all":
            for mdl in cosmos.scenario.model:
                mdls.append(mdl)
        else:    
            for model2 in model:
                for mdl in cosmos.scenario.model:
                    if mdl.name == model2:
                        mdls.append(mdl)
                
        for mdl in mdls:
            fo.mkdir(mdl.cycle_path)
            fo.mkdir(mdl.cycle_input_path)
            fo.mkdir(mdl.cycle_output_path)
            fo.mkdir(mdl.cycle_figures_path)
            fo.mkdir(mdl.cycle_post_path)
            fo.mkdir(mdl.restart_flow_path)
            fo.mkdir(mdl.restart_wave_path)
            mdl.post_process()

        # Delete job folder that was just created
        if cosmos.config.cycle.run_mode != "parallel":
            fo.rmdir(os.path.join(cosmos.config.path.jobs,
                                  cosmos.scenario_name))

# class Config:
#     def __init__(self):        
#         self.main_path = None
#         self.run_mode  = "serial"
                        
cosmos = CoSMoS()
