# -*- coding: utf-8 -*-
"""
Created on Mon May 10 12:18:09 2021

@author: ormondt
"""

import os
import datetime

import cht.misc.fileops as fo


class CoSMoS:

    """
    This is the CoSMoS class.

    :param kind: Optional "kind" of ingredients.
    :type kind: list[str] or None
    :return: The ingredients list.
    :rtype: list[str]

    """
    
    def __init__(self):        
        os.environ['HDF5_DISABLE_VERSION_CHECK'] = '2'

    def initialize(self, main_path, **kwargs):

        from .cosmos_configuration import Configuration

        self.config          = Configuration()

        # Set main path        
        self.config.path.main = main_path

        self.config.file_name = "default.toml"
        for key, value in kwargs.items():
            if key == "config_file":
                self.config.file_name = value       
                break

        # Read in configuration
        self.config.set(**kwargs)
        
        

    def run(self, *args):

        """
        Runs a CoSMoS scenario.
    
        :param scenario_name: name of the scenario to be run.
        :param main_path: overrides *main_path* specified in ``cosmos.initialize()``.
        :type scenario_name: str
        :type main_path: str
    
        """

        # Determine which cycle is needs to be run
        # If no cycle is given, then it will be determined later on        
        cycle = None
        self.scenario_name = args[0]
        if len(args)>1:
            cycle = args[1]

        if cycle:
            cycle = datetime.datetime.strptime(cycle, "%Y%m%d_%HZ").replace(tzinfo=datetime.timezone.utc)        
        else:
            cycle = None

        
        if not self.config.path.main:
            cosmos.log("Error: CoSMoS main path not set! Do this by running cosmos.initialize(main_path) or passing main_path as input argument to cosmos.run().")
            return

        from .cosmos_main_loop import MainLoop
        from .cosmos_model_loop import ModelLoop
        self.main_loop  = MainLoop()
        self.model_loop = ModelLoop()

        # self.main_loop.just_initialize = self.config.cycle.just_initialize
        # self.main_loop.run_models      = self.config.cycle.run_models
        # self.main_loop.clean_up        = self.config.cycle.clean_up
        
        self.main_loop.start(cycle=cycle)

    def stop(self):   
        self.model_loop.scheduler.cancel()
        self.main_loop.scheduler.cancel()

    def log(self, message):
        print(message)
        log_file = os.path.join(self.config.path.main, "cosmos.log")
        tstr = "[" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + " UTC] "
        with open(log_file, 'a') as f:
            f.write(tstr + message + "\n")
            f.close()

    def make_webviewer(self, sc_name, wv_name, upload=False, cycle=None,config_file="default.xml"):   

        if not cosmos.config.main_path:
            cosmos.log("Error: CoSMoS main path not set! Do this by running cosmos.initialize(main_path) or passing main_path as input argument to cosmos.run().")
            return
        
        self.run(sc_name,config_file=config_file, just_initialize=True, cycle=cycle)
                
        from .cosmos_webviewer import WebViewer
        
        wv = WebViewer(wv_name)
        wv.make()

        # Delete job folder that was just created
        if cosmos.config.run_mode != "parallel":
            fo.rmdir(os.path.join(cosmos.config.job_path,
                                  cosmos.config.scenario_name))
        
        if upload:
            wv.upload()

    def post_process(self, sc_name, model=None, cycle=None):   

        if not cosmos.config.main_path:
            cosmos.log("Error: CoSMoS main path not set! Do this by running cosmos.initialize(main_path) or passing main_path as input argument to cosmos.run().")
            return
        
        self.run(sc_name,just_initialize=True, cycle=cycle)
        
        mdls = []
        if model == "all":
            for mdl in cosmos.scenario.model:
                mdls.append(mdl)
        else:    
            for mdl in cosmos.scenario.model:
                if mdl.name == model:
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
        if cosmos.config.run_mode != "parallel":
            fo.rmdir(os.path.join(cosmos.config.job_path,
                                  cosmos.config.scenario_name))

# class Config:
#     def __init__(self):        
#         self.main_path = None
#         self.run_mode  = "serial"
                        
cosmos = CoSMoS()
