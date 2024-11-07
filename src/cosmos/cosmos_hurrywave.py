# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:02:04 2021

@author: ormondt
"""

import os
import pandas as pd
import platform

from .cosmos_main import cosmos
from .cosmos_model import Model
# from cht_utils.misc_tools import dict2yaml

from cht_hurrywave import HurryWave
import cht_utils.fileops as fo
from cht_nesting import nest1

class CoSMoS_HurryWave(Model):
    """Cosmos class for HurryWave model.

    HurryWave is a computationally efficient third generation spectral wave model, with physics similar to 
    those of SWAN and WAVEWATCH III.

    This cosmos class reads HurryWave model data, pre-processes, moves and post-processes HurryWave models.

    Parameters
    ----------
    Model : class
        Generic cosmos model attributes

    See Also
    ----------
    cosmos.cosmos_scenario.Scenario
    cosmos.cosmos_model_loop.ModelLoop
    cosmos.cosmos_model.Model
    """  

    def read_model_specific(self):
        """Read HurryWave specific model attributes.

        See Also
        ----------
        cht_hurrywave.hurrywave
        """ 
        # Read in the HurryWave model
        
        # Now read in the domain data
        self.domain = HurryWave(path=os.path.join(self.path, "input"), load=True)

        # Copy some attributes to the model domain (needed for nesting)
        self.domain.crs   = self.crs
        self.domain.type  = self.type
        self.domain.name  = self.name
        self.domain.runid = self.runid        
        
    def pre_process(self):
        """Preprocess HurryWave model.

        - Extract and write wave conditions.
        - Write input file. 
        - Write meteo forcing.
        - Add observation points for nested models and observation stations.
        - Optional: make ensemble of models.

        See Also
        ----------
        cht_nesting.nest2
        """
        # Set path temporarily to job path
        pth = self.domain.path
        self.domain.path = self.job_path
        
        # Start and stop times
        self.domain.input.variables.tref     = cosmos.scenario.ref_date
        self.domain.input.variables.tstart   = self.wave_start_time
        self.domain.input.variables.tstop    = self.wave_stop_time
        self.domain.input.variables.tspinup  = self.wave_spinup_time*3600
#        nsecs = (self.wave_stop_time - self.wave_start_time).total_seconds()
#        self.domain.input.dtmaxout = nsecs
        self.domain.input.variables.dtmaxout = 21600.0
        self.domain.input.variables.dtmapout = 21600.0
        self.domain.input.variables.outputformat = "net"


        # Boundary conditions        
        if self.wave_nested:
            self.domain.input.variables.bspfile = "hurrywave.bsp"
            self.domain.boundary_conditions.forcing = "spectra"
                    
        # Meteo forcing
        if self.meteo_wind:
            self.write_meteo_input_files("hurrywave", self.domain.input.variables.tref)
            self.domain.input.variables.amufile = "hurrywave.amu"
            self.domain.input.variables.amvfile = "hurrywave.amv"
                
        if self.meteo_spiderweb or self.meteo_track and not self.ensemble:   
            self.domain.input.variables.spwfile = "hurrywave.spw"
            # Spiderweb file given, copy to job folder
            if cosmos.scenario.run_ensemble:
                spwfile = os.path.join(cosmos.scenario.cycle_track_ensemble_spw_path, "ensemble00000.spw")
            elif self.meteo_spiderweb:
                spwfile = os.path.join(cosmos.scenario.cycle_track_spw_path, self.meteo_spiderweb)
            elif self.meteo_track:
                spwfile = os.path.join(cosmos.scenario.cycle_track_spw_path, self.meteo_track.split('.')[0] + ".spw")        
            fo.copy_file(spwfile, os.path.join(self.job_path, "hurrywave.spw"))            

        if self.ensemble:
            # Copy all spiderwebs to jobs folder
            self.domain.input.variables.spwfile = "hurrywave.spw"
        
        # Make observation points
        if self.station:
            for station in self.station:
                if not self.domain.input.variables.obsfile:
                    self.domain.input.variables.obsfile = "hurrywave.obs"
                self.domain.observation_points_regular.add_point(station.x,
                                                                 station.y,
                                                                 station.name)
                
        # Add observation points for nested models (Nesting 1)
        if self.nested_wave_models:
            
            for nested_model in self.nested_wave_models:

                specout = False
                if nested_model.type=="xbeach":
                    specout = True
                    nest1(self.domain, nested_model.domain, option="sp2")
                elif nested_model.type=="sfincs":
                    # No sp2 output
                    nested_model.domain.input.bwvfile = "snapwave.bnd"
                    nested_model.domain.read_wave_boundary_points()
                    nest1(self.domain, nested_model.domain)
                    nested_model.domain.input.bwvfile = None
                elif nested_model.type=="beware":
                    specout = False
                    nest1(self.domain, nested_model.domain)
                else:
                    specout = True
                    nest1(self.domain, nested_model.domain)
                    
            if specout:        
                if not self.domain.input.variables.ospfile:
                    self.domain.input.variables.ospfile = "hurrywave.osp"
                self.domain.observation_points_sp2.write()                             
                if self.domain.input.variables.dtsp2out == 0.0:
                    self.domain.input.variables.dtsp2out = 3600.0

        if len(self.domain.observation_points_regular.gdf)>0:
            if not self.domain.input.variables.obsfile:
                self.domain.input.variables.obsfile = "hurrywave.obs"            
            self.domain.observation_points_regular.write()

        # Make restart file
        trstsec = self.domain.input.variables.tstop.replace(tzinfo=None) - self.domain.input.variables.tref            
        if self.meteo_dataset:
            if self.meteo_dataset.last_analysis_time:
                trstsec = self.meteo_dataset.last_analysis_time.replace(tzinfo=None) - self.domain.input.variables.tref
        self.domain.input.variables.trstout  = trstsec.total_seconds()
        self.domain.input.variables.dtrstout = 0.0
        
        # Get restart file from previous cycle
        if self.wave_restart_file:
            src = os.path.join(self.restart_wave_path,
                               self.wave_restart_file)
            dst = os.path.join(self.job_path,
                               "hurrywave.rst")
            fo.copy_file(src, dst)
            self.domain.input.variables.rstfile = "hurrywave.rst"
            self.domain.input.variables.tspinup = 0.0

        # Now write input file (sfincs.inp)
        self.domain.input.write()

        # Set the path back to the one in cosmos\models\etc.
        self.domain.path = pth

        ### And now prepare the job files ###

        # Copy the correct run script to run_job.py
        pth = os.path.dirname(__file__)
        fo.copy_file(os.path.join(pth, "cosmos_run_hurrywave.py"), os.path.join(self.job_path, "run_job_2.py"))

        # Write config.yml file to be used in job
        self.write_config_yml()

        if self.ensemble:
            # Write ensemble members to file
            with open(os.path.join(self.job_path, "ensemble_members.txt"), "w") as f:
                for member in cosmos.scenario.ensemble_names:
                    f.write(member + "\n")

        if cosmos.config.run.run_mode != "cloud":
            # Make run batch file (only for windows and linux).
            if platform.system() == "Windows":
                batch_file = os.path.join(self.job_path, "run_hurrywave.bat")
                fid = open(batch_file, "w")
                fid.write("@ echo off\n")
                exe_path = os.path.join(cosmos.config.executables.hurrywave_path, "hurrywave.exe")
                fid.write(exe_path + "\n")
                fid.close()
            elif platform.system() == "Linux":
                batch_file = os.path.join(self.job_path, "run_hurrywave.sh")
                fid = open(batch_file, "w")
                exe_path = os.path.join(cosmos.config.executables.hurrywave_path, "hurrywave")
                fid.write(exe_path + "\n")
                fid.close()
 
        if cosmos.config.run.run_mode == "cloud":
            # Set workflow names
            if self.ensemble:
                self.workflow_name = "hurrywave-ensemble-workflow"
            else:
                self.workflow_name = "hurrywave-deterministic-workflow"


    def move(self):             
        job_path    = self.job_path
        output_path  = self.cycle_output_path
        input_path   = self.cycle_input_path  
        restart_path = self.restart_wave_path        

        # Output        
        fo.move_file(os.path.join(job_path, "hurrywave_map.nc"), output_path)
        fo.move_file(os.path.join(job_path, "hurrywave_his.nc"), output_path)
        fo.move_file(os.path.join(job_path, "hurrywave_sp2.nc"), output_path)
        fo.move_file(os.path.join(job_path, "*.txt"), output_path)

        # Restart file used in simulation        
        fo.move_file(os.path.join(job_path, "hurrywave.rst"), input_path)
        # Restart files created during simulation
        fo.move_file(os.path.join(self.job_path, "hurrywave.*.rst"), restart_path)
        # Input
        fo.move_file(os.path.join(job_path, "*.*"), input_path)


    def post_process(self):
        # Extract wave time series
        # input_path  = self.cycle_input_path
        output_path = self.cycle_output_path
        post_path   = self.cycle_post_path            
        # if not self.domain.input.variables.tref:
        #     # This model has been run before. The model instance has not data on tref, obs points etc.
        #     self.domain.read_input_file(os.path.join(input_path, "hurrywave.inp"))
        #     self.domain.read_observation_points()
        if self.station:
            # Read in data for all stations
            data = {}
            if self.ensemble:
                prcs= [0.05, 0.5, 0.95]
                for i,v in enumerate(prcs):
                    data["hm0_" + str(round(v*100))] = self.domain.read_timeseries_output(path=output_path,
                                                          file_name= "hurrywave_his.nc",
                                                          parameter= "hm0_" + str(round(v*100)))
                    data["tp_" + str(round(v*100))] = self.domain.read_timeseries_output(path=output_path,
                                                          file_name= "hurrywave_his.nc",
                                                          parameter= "tp_" + str(round(v*100)))
            else:    
                data["hm0"] = self.domain.read_timeseries_output(path=output_path,  parameter="hm0")
                data["tp"] = self.domain.read_timeseries_output(path=output_path,  parameter="tp")

            # Loop through stations 
            for station in self.station:                

                if self.ensemble:
                    indx = data["hm0_" + str(round(prcs[0]*100))].index
                    df = pd.DataFrame(index=indx)
                    df.index.name='date_time'
                    for i,v in enumerate(prcs):
                        df["Hm0_" + str(round(v*100))] = data["hm0_" + str(round(v*100))][station.name]
                        df["Tp_" + str(round(v*100))]  = data["tp_" + str(round(v*100))][station.name]

                else:    
                    df = pd.DataFrame(index=data["hm0"].index)
                    df.index.name='date_time'
                    df["Hm0"]=data["hm0"][station.name]
                    df["Tp"]=data["tp"][station.name]

                # Write csv file for station
                file_name = os.path.join(post_path,
                                            "waves." + station.name + ".csv")
                df.to_csv(file_name,
                            date_format='%Y-%m-%dT%H:%M:%S',
                            float_format='%.3f')        
