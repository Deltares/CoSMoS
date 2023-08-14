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
        
        self.config          = Config()
        self.cycle_time      = None        
        self.cycle_stop_time = None  
        self.storm_flag      = False
        self.storm_keeplist  = []
        
    def initialize(self, main_path):        

        """
        Set the path of the CoSMoS main folder.
    
        :param main_path: Path of CoSMoS main folder.
        :type main_path: str
        """
        
        self.config.main_path = main_path
        
        os.environ['HDF5_DISABLE_VERSION_CHECK'] = '2'

    def run(self,
            scenario_name,
            main_path=None,
            config_file="default.xml",
            mode="single",
#            forecast=False,
            run_models=True,
            make_flood_maps=True,
            make_wave_maps=True,
            get_meteo=True,
            make_figures=True,
            upload=False,
            ensemble=False,
            webviewer=None,
            just_initialize=False,
            clean_up=False,
            cycle=None):

        """
        Runs a CoSMoS scenario.
    
        :param scenario_name: name of the scenario to be run.
        :param main_path: overrides *main_path* specified in ``cosmos.initialize()``.
        :type scenario_name: str
        :type main_path: str
    
        """
           
        if main_path:
            self.config.main_path   = main_path            
        self.config.scenario_name   = scenario_name
        self.config.cycle_mode      = mode
        self.config.make_flood_maps = make_flood_maps
        self.config.make_wave_maps  = make_wave_maps
        self.config.upload          = upload
        self.config.webviewer       = webviewer
#        self.config.forecast        = forecast
        self.config.config_file     = config_file
        self.config.get_meteo       = get_meteo
        if cycle:
            self.config.cycle = datetime.datetime.strptime(cycle, "%Y%m%d_%HZ").replace(tzinfo=datetime.timezone.utc)        
        else:
            self.config.cycle = None

        # Make folder to store log files
        # And set some other paths
        self.config.job_path      = os.path.join(self.config.main_path, "jobs")
        self.config.stations_path = os.path.join(self.config.main_path, "stations")
        
        if not self.config.main_path:
            cosmos.log("Error: CoSMoS main path not set! Do this by running cosmos.initialize(main_path) or passing main_path as input argument to cosmos.run().")
            return

#        cosmos.config.make_figures    = make_figures
#        cosmos.config.run_ensemble    = ensemble

        from .cosmos_main_loop import MainLoop
        from .cosmos_model_loop import ModelLoop
        self.main_loop  = MainLoop()
        self.model_loop = ModelLoop()

        self.main_loop.just_initialize = just_initialize
        self.main_loop.run_models      = run_models
        self.main_loop.clean_up        = clean_up
        
        self.main_loop.start()

    def stop(self):   
        self.model_loop.scheduler.cancel()
        self.main_loop.scheduler.cancel()

    def log(self, message):
        print(message)
        log_file = os.path.join(self.config.main_path,"cosmos.log")
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
        
        if upload and os.path.isabs(cosmos.config.ftp_path):
            wv.copy_to_webviewer()
        elif upload:
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

class Config:
    def __init__(self):        
        self.main_path = None
        self.run_mode  = "serial"
                        
cosmos = CoSMoS()
