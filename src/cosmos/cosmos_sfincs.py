# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:02:04 2021

@author: ormondt
"""

import os
import pandas as pd
import numpy as np

from cht.sfincs.sfincs import SFINCS
import cht.misc.fileops as fo
from cht.tide.tide_predict import predict
from cht.nesting.nest1 import nest1

from .cosmos_main import cosmos
from .cosmos_model import Model
import cosmos.cosmos_meteo as meteo

class CoSMoS_SFINCS(Model):
    """Cosmos class for SFINCS model.

    SFINCS (Super-Fast Inundation of CoastS) is a reduced-complexity model capable of simulating compound flooding 
    with a high computational efficiency balanced with an adequate accuracy (see also https://sfincs.readthedocs.io/en/latest/).

    This cosmos class reads SFINCS  model data, pre-processes, moves and post-processes SFINCS models.

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
        """Read SFINCS specific model attributes.

        See Also
        ----------
        cht.sfincs.sfincs
        """         
        # Read in the SFINCS model                        
        input_file  = os.path.join(self.path, "input", "sfincs.inp")
        self.domain = SFINCS(input_file)
        # Copy some attributes to the model domain (needed for nesting)
        self.domain.crs   = self.crs
        self.domain.type  = self.type
        self.domain.name  = self.name
        self.domain.runid = self.runid
                        
    def pre_process(self):
        """Preprocess SFINCS model.

        - Extract and write water level and wave conditions.
        - Write input file. 
        - Write meteo forcing.
        - Add observation points for nested models and observation stations.
        - Optional: make ensemble of models.

        See Also
        ----------
        cht.nesting.nest2
        """
        # Set path temporarily to job path
        pth = self.domain.path
        self.domain.path = self.job_path
        
        # Start and stop times
        self.domain.input.tref     = cosmos.scenario.ref_date
        self.domain.input.tstart   = self.flow_start_time
        self.domain.input.tstop    = self.flow_stop_time
        self.domain.input.tspinup  = self.flow_spinup_time*3600
        self.domain.input.dtmapout = 21600.0 # should this not be configurable?
        self.domain.input.dtmaxout = 21600.0 # should this not be configurable?
        self.domain.input.dtout    = None
        self.domain.input.outputformat = "net"
        self.domain.input.bzsfile  = "sfincs.bzs"
        self.domain.input.storecumprcp = 1

        # Temporary fix for SFINCS bug 
        if hasattr(self.domain.input, "krfile"):
            self.domain.input.ksfile = self.domain.input.krfile
        
        if self.flow_nested:
            self.domain.input.pavbnd = -999.0

        # Make observation points
        if self.station:
            self.domain.input.obsfile  = "sfincs.obs"
            for station in self.station:
                self.domain.add_observation_point(station.x,
                                                  station.y,
                                                  station.name)
                
        # Add observation points for nested models (Nesting 1)
        if self.nested_flow_models:
            if not self.domain.input.obsfile:
                self.domain.input.obsfile = "sfincs.obs"
            
            for nested_model in self.nested_flow_models:
                nest1(self.domain, nested_model.domain)

        # Add other observation stations 
        if self.nested_flow_models or len(self.station)>0:
            if not self.domain.input.obsfile:
                self.domain.input.obsfile = "sfincs.obs"
            self.domain.write_observation_points()

        # Make restart file
        trstsec = self.domain.input.tstop.replace(tzinfo=None) - self.domain.input.tref            
        if self.meteo_subset:
            if self.meteo_subset.last_analysis_time:
                trstsec = self.meteo_subset.last_analysis_time.replace(tzinfo=None) - self.domain.input.tref
        self.domain.input.trstout = trstsec.total_seconds()
        self.domain.input.dtrst   = 0.0
        
        # Get restart file from previous cycle
        if self.flow_restart_file:
            src = os.path.join(self.restart_flow_path,
                               self.flow_restart_file)
            dst = os.path.join(self.job_path,
                               "sfincs.rst")
            fo.copy_file(src, dst)
            self.domain.input.rstfile = "sfincs.rst"
            self.domain.input.tspinup = 0.0

        # Boundary conditions        
        if self.flow_nested:
            # The actual nesting occurs in the run_job.py file 
            self.domain.input.bzsfile = "sfincs.bzs"
            
        elif self.domain.input.bcafile:            
            # Get boundary conditions from astronomic components (should really do this in sfincs.py) 
            times = pd.date_range(start=self.flow_start_time,
                                  end=self.flow_stop_time,
                                  freq='600s')            
            # Make boundary conditions based on bca file
            for point in self.domain.flow_boundary_point:
                if self.tide:
                    v = predict(point.astro, times)
                else:    
                    v = np.zeros(len(times))
                point.data = pd.Series(v, index=times)                    
            self.domain.write_flow_boundary_conditions()

        if self.wave_nested:
            # The actual nesting occurs in the run_job.py file
            self.domain.input.snapwave_bhsfile = "snapwave.bhs"
            self.domain.input.snapwave_btpfile = "snapwave.btp"
            self.domain.input.snapwave_bwdfile = "snapwave.bwd"
            self.domain.input.snapwave_bdsfile = "snapwave.bds"

        # If SFINCS nested in Hurrywave for SNAPWAVE setup, separately run BEWARE nesting for LF waves
        if self.bw_nested:
            # The actual nesting occurs in the run_job.py file 
            self.domain.input.wfpfile = "sfincs.wfp"
            self.domain.input.whifile = "sfincs.whi"
            self.domain.input.wtifile = "sfincs.wti"

        # Meteo forcing
        if self.meteo_wind or self.meteo_atmospheric_pressure or self.meteo_precipitation:
            meteo.write_meteo_input_files(self,
                                          "sfincs",
                                          self.domain.input.tref)
            if self.meteo_wind:                
                self.domain.input.amufile = "sfincs.amu"
                self.domain.input.amvfile = "sfincs.amv"
            if self.meteo_atmospheric_pressure:
                self.domain.input.ampfile = "sfincs.amp"
                self.domain.input.baro    = 1                            
            if self.meteo_precipitation:                
                self.domain.input.amprfile = "sfincs.ampr"
            else:
                self.domain.input.scsfile = None

        if self.meteo_spiderweb or self.meteo_track and not self.ensemble:   
            self.domain.input.spwfile = "sfincs.spw"         
            # Spiderweb file given, copy to job folder
            if cosmos.scenario.run_ensemble:
                spwfile = os.path.join(cosmos.scenario.cycle_track_ensemble_spw_path, "ensemble00000.spw")
            elif self.meteo_spiderweb:
                spwfile = os.path.join(cosmos.scenario.cycle_track_spw_path, self.meteo_spiderweb)
            elif self.meteo_track:
                spwfile = os.path.join(cosmos.scenario.cycle_track_spw_path, self.meteo_track.split('.')[0] + ".spw")
            fo.copy_file(spwfile, os.path.join(self.job_path, "sfincs.spw"))            
            self.domain.input.baro    = 1
            if self.crs.is_projected:
                self.domain.input.utmzone = self.crs.utm_zone
        
        if self.ensemble:
            # Use spiderweb from ensemble
            self.domain.input.spwfile = "sfincs.spw"
            if self.crs.is_projected:
                self.domain.input.utmzone = self.crs.utm_zone

        # Now write input file (sfincs.inp)
        self.domain.write_input_file()
        # Finally set the path back to the one in cosmos\models\etc.
        self.domain.path = pth

        # And now prepare the job files

        # Copy the correct run script to run_job.py
        pth = os.path.dirname(__file__)
        fo.copy_file(os.path.join(pth, "cosmos_run_sfincs.py"), os.path.join(self.job_path, "run_job_2.py"))

        # Write config.yml file to be used in job
        self.write_config_yml()

        if self.ensemble:
            # Write ensemble members to file
            with open(os.path.join(self.job_path, "ensemble_members.txt"), "w") as f:
                for member in cosmos.scenario.ensemble_names:
                    f.write(member + "\n")

        if cosmos.config.run.run_mode != "cloud":
            # Make run batch file (only for windows)
            batch_file = os.path.join(self.job_path, "run_sfincs.bat")
            fid = open(batch_file, "w")
            fid.write("@ echo off\n")
            exe_path = os.path.join(cosmos.config.executables.sfincs_path, "sfincs.exe")
            fid.write(exe_path + ">sfincs.log\n")
            fid.close()
 
        if cosmos.config.run.run_mode == "cloud":
            # Set workflow names
            if self.ensemble:
                self.workflow_name = "sfincs-ensemble-workflow"
            else:
                self.workflow_name = "sfincs-deterministic-workflow"


    def move(self):        
        job_path     = self.job_path
        output_path  = self.cycle_output_path
        input_path   = self.cycle_input_path  
        restart_path = self.restart_flow_path
        # Output
        fo.move_file(os.path.join(job_path, "sfincs_map.nc"), output_path)
        fo.move_file(os.path.join(job_path, "sfincs_his.nc"), output_path)
        # Restart file used in simulation        
        fo.move_file(os.path.join(self.job_path, "sfincs.rst"), input_path)
        # Restart files created during simulation
        fo.move_file(os.path.join(self.job_path, "*.rst"), restart_path)
        # Input (all the rest)
        fo.move_file(os.path.join(self.job_path, "*.*"), input_path)
        
    def post_process(self):
        # Extract water levels
        output_path = self.cycle_output_path
        post_path   = self.cycle_post_path
        if self.station:
            # Read in data for all stations
            data = {}
            if self.ensemble:
                prcs= [0.05, 0.50, 0.95]
                for i,v in enumerate(prcs):
                    data["wl_" + str(round(v*100))] = self.domain.read_timeseries_output(path=output_path,
                                                          file_name= "sfincs_his.nc",
                                                          parameter= "point_zs_" + str(round(v*100)))
            else:    
                data["wl"] = self.domain.read_timeseries_output(path=output_path,  parameter="point_zs")
            # Loop through stations 
            for station in self.station:                
                if self.ensemble:
                    indx = data["wl_" + str(round(prcs[0]*100))].index
                    df = pd.DataFrame(index=indx)
                    df.index.name='date_time'
                    for i,v in enumerate(prcs):
                        df["wl_" + str(round(v*100))] = data["wl_" + str(round(v*100))][station.name]
                else:    
                    df = pd.DataFrame(index=data["wl"].index)
                    df.index.name='date_time'
                    df["wl"]=data["wl"][station.name]
                # Write csv file for station
                file_name = os.path.join(post_path,
                                            "wl." + station.name + ".csv")
                df.to_csv(file_name,
                            date_format='%Y-%m-%dT%H:%M:%S',
                            float_format='%.3f')        
