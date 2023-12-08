# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:02:04 2021

@author: ormondt
"""

import os
import pandas as pd
import numpy as np
import shutil
import datetime

from cht.sfincs.sfincs import SFINCS
import cht.misc.fileops as fo
from cht.tide.tide_predict import predict
from cht.misc.deltares_ini import IniStruct
from cht.misc.misc_tools import dict2yaml

from .cosmos import cosmos
from .cosmos_model import Model
from .cosmos_tiling import make_flood_map_tiles
import cosmos.cosmos_meteo as meteo

#import xmlkit as xml

import cht.nesting.nesting as nesting


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
        self.domain.input.dtmapout = 21600.0
        self.domain.input.dtmaxout = 21600.0
        self.domain.input.outputformat = "net"
        self.domain.input.bzsfile  = "sfincs.bzs"
        self.domain.input.storecumprcp = 1
        
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
                nesting.nest1(self.domain, nested_model.domain)

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

            # Get boundary conditions from overall model (Nesting 2)

            # Correct boundary water levels. Assuming that output from overall
            # model is in MSL !!!
            zcor = self.boundary_water_level_correction - self.vertical_reference_level_difference_with_msl
            
            self.domain.input.bzsfile = "sfincs.bzs"
            # Get boundary conditions from overall model (Nesting 2)
            if self.ensemble:
                # Loop through ensemble members
                for iens in range(cosmos.scenario.track_ensemble_nr_realizations):
                    name = cosmos.scenario.ensemble_names[iens]
                    nesting.nest2(self.flow_nested.domain,
                          self.domain,
                          output_path=os.path.join(self.flow_nested.cycle_output_path, name),
                          output_file= 'sfincs_his.nc',
                          boundary_water_level_correction=zcor,
                          option="flow",
                          bc_file=os.path.join(self.job_path, name, self.domain.input.bzsfile))
            else:
                # Deterministic    
                nesting.nest2(self.flow_nested.domain,
                        self.domain,
                        output_path=self.flow_nested.cycle_output_path,
                        # output_file='sfincs_his.nc',
                        boundary_water_level_correction=zcor,
                        option="flow",
                        bc_file= os.path.join(self.job_path,self.domain.input.bzsfile))
            
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
            
            # Get wave boundary conditions from overall model (Nesting 2)

            # Check to see in which model this model is nested 
            # In case of BEWARE:
            #    We force the wave makers with IG waves from BEWARE
            #    Data from bhi file are the IG wave heights
            #    Data from bti file are the IG wave period
            # Otherwise:
            #    We force the model wave makers with SnapWave
            #    Data from bhs file are Hm0 incident waves
           
            # We do this following bit just to make sure the file names are set.
            # The user should probably make sure that they are present in the sfincs.inp file.

            self.domain.input.snapwave_bhsfile = "snapwave.bhs"
            self.domain.input.snapwave_btpfile = "snapwave.btp"
            self.domain.input.snapwave_bwdfile = "snapwave.bwd"
            self.domain.input.snapwave_bdsfile = "snapwave.bds"
            
            # Get boundary conditions from overall model (Nesting 2)
            if self.ensemble:
                # Loop through ensemble members
                for iens in range(cosmos.scenario.track_ensemble_nr_realizations):
                    name = cosmos.scenario.ensemble_names[iens]
                    nesting.nest2(self.wave_nested.domain,
                          self.domain,
                          output_path=os.path.join(self.wave_nested.cycle_output_path, name),
                          option="wave",
                          bc_path=os.path.join(self.job_path, name))
            else:
                # Deterministic    
                nesting.nest2(self.wave_nested.domain,
                        self.domain,
                        output_path=self.wave_nested.cycle_output_path,
                        option="wave",
                        bc_path=self.job_path)

        # If SFINCS nested in Hurrywave for SNAPWAVE setup, separately run BEWARE nesting for LF waves
        if self.bw_nested:

            self.domain.input.wfpfile = "sfincs.wfp"
            self.domain.input.whifile = "sfincs.whi"
            self.domain.input.wtifile = "sfincs.wti"

            # Get wave maker conditions from overall model (Nesting 2)
            if self.ensemble:
                # Loop through ensemble members
                for iens in range(cosmos.scenario.track_ensemble_nr_realizations):
                    name = cosmos.scenario.ensemble_names[iens]
                    nesting.nest2(self.bw_nested.domain,
                          self.domain,
                          output_path=os.path.join(self.bw_nested.cycle_output_path, name),
                          option="wave",
                          bc_path=os.path.join(self.job_path, name))
            else:
                # Deterministic    
                nesting.nest2(self.bw_nested.domain,
                      self.domain,
                      output_path=self.bw_nested.cycle_output_path,
                      option="wave",
                      bc_path=self.job_path)

            self.domain.write_wavemaker_forcing_points()

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

        if self.meteo_spiderweb:
            
            # Spiderweb file given, copy to job folder
            self.domain.input.spwfile = self.meteo_spiderweb
            meteo_path = os.path.join(cosmos.config.meteo_database.path, "spiderwebs")
            src = os.path.join(meteo_path, self.meteo_spiderweb)
            fo.copy_file(os.path.join(meteo_path, self.meteo_spiderweb), self.job_path)

            # elif cosmos.scenario.track_ensemble:
            #     self.domain.input.spwfile = "sfincs.spw"   
            #     fo.copy_file(cosmos.scenario.best_track_file, os.path.join(self.job_path, "sfincs.spw"))
            
        if self.ensemble:
            # Copy all spiderwebs to jobs folder
            self.domain.input.spwfile = "sfincs.spw"
            for iens in range(cosmos.scenario.track_ensemble_nr_realizations):
                name = cosmos.scenario.ensemble_names[iens]
                fname0 = os.path.join(cosmos.scenario.cycle_track_ensemble_spw_path,
                                      "ensemble" + name + ".spw")
                fname1 = os.path.join(self.job_path, name, "sfincs.spw")
                fo.copy_file(fname0, fname1)
        
        if not self.ensemble and self.meteo_track:
            # Copy all spiderwebs to jobs folder
            self.domain.input.spwfile = "sfincs.spw"
            name = cosmos.scenario.best_track
            fname0 = os.path.join(cosmos.scenario.cycle_track_ensemble_spw_path,
                                    "ensemble" + name + ".spw")
            fname1 = os.path.join(self.job_path, "sfincs.spw")
            fo.copy_file(fname0, fname1)

        if self.ensemble or self.meteo_spiderweb or self.meteo_track:
            self.domain.input.baro    = 1
            self.domain.input.utmzone = self.crs.utm_zone
            if self.meteo_spiderweb or self.meteo_track:
                self.domain.input.amufile = None
                self.domain.input.amvfile = None
                self.domain.input.ampfile = None
                self.domain.input.amprfile = None
#            self.domain.input.variables.amufile = None
#            self.domain.input.variables.amvfile = None

        # Now write input file (sfincs.inp)
        self.domain.write_input_file()

        # Make run batch file
        batch_file = os.path.join(self.job_path, "run.bat")
        fid = open(batch_file, "w")
        fid.write("@ echo off\n")
        fid.write("DATE /T > running.txt\n")
        exe_path = os.path.join(cosmos.config.executables.sfincs_path, "sfincs.exe")
        fid.write(exe_path + "\n")
        fid.write("move running.txt finished.txt\n")
        fid.close()

        # Set the path back to the one in cosmos\models\etc.
        self.domain.path = pth

    def move(self):
        """Move SFINCS model input, output, and restart files.
        """   
        job_path     = self.job_path
        output_path  = self.cycle_output_path
        input_path   = self.cycle_input_path  
        restart_path = self.restart_flow_path
        
        # Output        
        if self.ensemble:
            # Merging should happen in the job, so there should not be a difference between ensemble and deterministic
            for member_name in cosmos.scenario.ensemble_names:                
                pth0 = os.path.join(job_path, member_name)
                pth1 = os.path.join(output_path, member_name)
                fo.mkdir(pth1)
                fo.move_file(os.path.join(pth0, "sfincs_map.nc"), pth1)
                fo.move_file(os.path.join(pth0, "sfincs_his.nc"), pth1)
        else:
            fo.move_file(os.path.join(job_path, "sfincs_map.nc"), output_path)
            fo.move_file(os.path.join(job_path, "sfincs_his.nc"), output_path)
            fo.move_file(os.path.join(job_path, "*.txt"), output_path)
        
        
        fo.move_file(os.path.join(job_path, "sfincs.rst"), input_path)

        # Restart files 
        fo.move_file(os.path.join(job_path, "*.rst"), restart_path)
        # Restart files 
        if self.ensemble:
            # Copy restart file from first member (they should be identical for all members)
            member_name = cosmos.scenario.ensemble_names[0]
            pth0 = os.path.join(job_path, member_name)
            fo.move_file(os.path.join(job_path, member_name, "*.rst"), restart_path)
        else:
            fo.move_file(os.path.join(job_path, "*.rst"), restart_path)

        # Input
        fo.move_file(os.path.join(job_path, "*.*"), input_path)
        
    def post_process(self):
        """Post-process SFINCS output: generate (probabilistic) water level timeseries and flood maps.        
        """
        import cht.misc.prob_maps as pm
        import cht.misc.misc_tools

        # Extract water levels

        input_path  = self.cycle_input_path
        output_path = self.cycle_output_path
        # post_path   = self.cycle_post_path
        post_path =  os.path.join(cosmos.config.path.webviewer, 
                            cosmos.config.webviewer.name,
                            "data",
                            cosmos.scenario.name)
        
        if self.ensemble:
            # Make probabilistic water level timeseries
            file_list = []
            for member in cosmos.scenario.ensemble_names:
                file_list.append(os.path.join(output_path, member, "sfincs_his.nc"))
            prcs= [5, 50, 95]
            vars= ["point_zs"]
            output_file_name = os.path.join(output_path, "sfincs_his_ensemble.nc")
            pm.prob_floodmaps(file_list=file_list, variables=vars, prcs=prcs, delete = False, output_file_name=output_file_name)


        if self.station:

            # Read in data for all stations
            data = {}
            if self.ensemble:
                prcs= [5, 50, 95]
                for i,v in enumerate(prcs):
                    data["wl_" + str(round(v))] = self.domain.read_timeseries_output(path=output_path,
                                                          file_name= "sfincs_his_ensemble.nc",
                                                          parameter= "point_zs_" + str(round(v)))
            else:    
                data["wl"] = self.domain.read_timeseries_output(path=output_path,  parameter="point_zs")

            # Loop through stations 
            for station in self.station:                
                if station.upload:
                    if self.ensemble:
                        indx = data["wl_" + str(round(prcs[0]))].index
                        df = pd.DataFrame(index=indx)
                        df.index.name='date_time'
                        for i,v in enumerate(prcs):
                            df["wl_" + str(round(v))] = data["wl_" + str(round(v))][station.name]
                            df["wl_" + str(round(v))] += self.vertical_reference_level_difference_with_msl

                    else:    
                        df = pd.DataFrame(index=data["wl"].index)
                        df.index.name='date_time'
                        df["wl"]=data["wl"][station.name]
                        df["wl"] += self.vertical_reference_level_difference_with_msl                            

                    # Write csv file for station
                    fo.mkdir(os.path.join(post_path, 'timeseries'))
                    csv_file = os.path.join(post_path,
                                            "timeseries",
                                                "waterlevel." + self.name + "." + station.name + ".csv.js")
                    
                    s = df.to_csv(date_format='%Y-%m-%dT%H:%M:%S',
                                    float_format='%.3f',
                                    header=False) 
                    cht.misc.misc_tools.write_csv_js(csv_file, s, "var csv = `date_time,wl")

        # Make flood map tiles
        if cosmos.config.cycle.make_flood_maps and self.make_flood_map:
                  
            if self.ensemble:
                # Make probabilistic flood maps
                file_list = []
                for member in cosmos.scenario.ensemble_names:
                    file_list.append(os.path.join(output_path, member, "sfincs_map.nc"))
                prcs= [5, 50, 95]                
                vars= ["zs", "zsmax"]
                output_file_name = os.path.join(output_path, "sfincs_map_ensemble.nc")
                pm.prob_floodmaps(file_list=file_list, variables=vars, prcs=prcs, delete = False, output_file_name=output_file_name)
            
            index_path = os.path.join(self.path, "tiling", "indices")
            topo_path = os.path.join(self.path, "tiling", "topobathy")
            
            if os.path.exists(index_path) and os.path.exists(topo_path):
                
                cosmos.log("Making flood map tiles for model " + self.long_name + " ...")                

                # 24 hour increments  
                dtinc = 24
    
                # Wave map for the entire simulation
                dt1 = datetime.timedelta(hours=1)
                dt  = datetime.timedelta(hours=dtinc)
                t0  = cosmos.cycle.replace(tzinfo=None)    
                t1  = cosmos.stop_time
                    
                pathstr = []
                
                # 6-hour increments
                requested_times = pd.date_range(start=t0 + dt,
                                                end=t1,
                                                freq=str(dtinc) + "H").to_pydatetime().tolist()
    
                for it, t in enumerate(requested_times):
                    pathstr.append((t - dt).strftime("%Y%m%d_%HZ") + "_" + (t).strftime("%Y%m%d_%HZ"))
    
                pathstr.append("combined_" + (t0).strftime("%Y%m%d_%HZ") + "_" + (t1).strftime("%Y%m%d_%HZ"))
                            
                zsmax_file = os.path.join(output_path, "sfincs_map.nc")
                
                try:
                    # Inundation map over dt-hour increments     
                    if not self.ensemble:  
                        # if os.path.exists(os.path.join(post_path, "flood_map")):
                        #     shutil.rmtree(os.path.join(post_path, "flood_map"))

                        for it, t in enumerate(requested_times):
        
                            zsmax = self.domain.read_zsmax(zsmax_file=zsmax_file,
                                                        time_range=[t - dt + dt1, t + dt1])
                            flood_map_path = os.path.join(post_path,
                                                        "flood_map",
                                                        pathstr[it])                                            
                            make_flood_map_tiles(zsmax, index_path, topo_path, flood_map_path,
                                                    water_level_correction=0.0)
        
                        # Full simulation        
                        flood_map_path = os.path.join(post_path,
                                                    "flood_map",
                                                    pathstr[-1])                    
                        zsmax = self.domain.read_zsmax(zsmax_file=zsmax_file,
                                                    time_range=[t0 + dt1, t1 + dt1])
                        make_flood_map_tiles(zsmax, index_path, topo_path, flood_map_path,
                                            water_level_correction=0.0)

                    elif self.ensemble:
                        # if os.path.exists(os.path.join(post_path, "flood_map_95")):
                        #     shutil.rmtree(os.path.join(post_path, "flood_map_95"))

                        zsmax_file = os.path.join(output_path, "sfincs_map_ensemble.nc")
                        # Full simulation        
                        flood_map_path = os.path.join(post_path,
                                                    "flood_map_95", 
                                                    pathstr[-1])                    
                        zsmax = self.domain.read_zsmax(zsmax_file=zsmax_file,
                                                    time_range=[t0 + dt1, t1 + dt1], parameter = 'zsmax_95')
                        make_flood_map_tiles(zsmax, index_path, topo_path, flood_map_path,
                                            water_level_correction=0.0)
                except:
                    print("An error occured while making flood map tiles")


#         # Make flood map tiles
# #        if cosmos.config.make_flood_maps and self.make_flood_map and self.domain.input.outputformat=="bin":
#         if cosmos.config.make_flood_maps and self.make_flood_map:

#             flood_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
#                                           "flood_map")
            
#             index_path = os.path.join(self.path, "tiling", "indices")
#             topo_path = os.path.join(self.path, "tiling", "topobathy")
            
#             if os.path.exists(index_path) and os.path.exists(topo_path):

#                 if self.domain.input.outputformat[0:3]=="bin":                
#                     zsmax_file = os.path.join(output_path, "zsmax.dat")
#                     zsmax = self.domain.read_zsmax(zsmax_file=zsmax_file)
#                 else:
#                     zsmax_file = os.path.join(output_path, "sfincs_map.nc")
#                     zsmax = self.domain.read_zsmax(zsmax_file=zsmax_file)
                    
#                 cosmos.log("Making flood map tiles for model " + self.name)    
#                 make_flood_map_tiles(zsmax, index_path, topo_path, flood_map_path,
#                                          water_level_correction=0.0)
#                 cosmos.log("Flood map tiles done.")    
