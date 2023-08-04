# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:02:04 2021

@author: ormondt
"""

import os
import pandas as pd
import numpy as np
import datetime
import boto3

from cht.sfincs.sfincs import SFINCS
import cht.misc.fileops as fo
from cht.tide.tide_predict import predict
from cht.misc.misc_tools import dict2yaml

from .cosmos import cosmos
from .cosmos_model import Model
from .cosmos_tiling import make_flood_map_tiles
import cosmos.cosmos_meteo as meteo

from cht.nesting.nest1 import nest1


class CoSMoS_SFINCS(Model):
    
    def read_model_specific(self):
        
        # Read in the SFINCS model
        input_file  = os.path.join(self.path, "input", "sfincs.inp")
        self.domain = SFINCS(input_file)

        # Copy some attributes to the model domain (needed for nesting)
        self.domain.crs   = self.crs
        self.domain.type  = self.type
        self.domain.name  = self.name
        self.domain.runid = self.runid
        
        
    def pre_process(self):
                       
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
#            self.domain.write_wavemaker_forcing_points()

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
            meteo_path = os.path.join(cosmos.config.main_path, "meteo", "spiderwebs")
            src = os.path.join(meteo_path, self.meteo_spiderweb)
            fo.copy_file(os.path.join(meteo_path, self.meteo_spiderweb), self.job_path)
            
            self.domain.input.baro    = 1
            self.domain.input.utmzone = self.crs.utm_zone
            self.domain.input.amufile = None
            self.domain.input.amvfile = None
            self.domain.input.ampfile = None
            self.domain.input.amprfile = None

        if self.ensemble:
            # Use spiderweb from ensemble
            self.domain.input.spwfile = "sfincs.spw"
            if self.crs.is_projected:
                self.domain.input.utmzone = self.crs.utm_zone

        # Now write input file (sfincs.inp)
        self.domain.write_input_file()

        # Copy the correct to run_job.py
        pth = os.path.dirname(__file__)
        fo.copy_file(os.path.join(pth, "cosmos_run_sfincs.py"), os.path.join(self.job_path, "run_job.py"))

        # Write config file to be used in run_job.py
        config = {}
        config["name"] = self.name
        config["scenario"] = cosmos.scenario_name
        config["cycle"]    = cosmos.cycle_string
        config["ensemble"] = self.ensemble
        config["run_mode"] = cosmos.config.cycle.run_mode
        if self.flow_nested:
            config["flow_nested_type"] = self.flow_nested.type
            config["flow_nested_path"] = self.flow_nested.cycle_output_path
        if self.wave_nested:
            config["wave_nested_type"] = self.wave_nested.type
            config["wave_nested_path"] = self.wave_nested.cycle_output_path
        if self.bw_nested: 
            config["bw_nested_type"]   = self.bw_nested.type
            config["bw_nested_path"]   = self.bw_nested.cycle_output_path
        if self.ensemble:
            config["spw_path"] = cosmos.scenario.cycle_track_ensemble_spw_path
        config["boundary_water_level_correction"] = self.boundary_water_level_correction
        config["vertical_reference_level_difference_with_msl"] = self.vertical_reference_level_difference_with_msl        
        if cosmos.config.cycle.make_flood_maps and self.make_flood_map:
            config["flood_map"] = {}
            if self.ensemble:
                name = "flood_map_90"
            else:
                name = "flood_map"    
            config["flood_map"]["name"] = name
            config["flood_map"]["png_path"]   = os.path.join(cosmos.config.webviewer.data_path)
            config["flood_map"]["index_path"] = os.path.join(self.path, "tiling", "indices")
            config["flood_map"]["topo_path"]  = os.path.join(self.path, "tiling", "topobathy")
            config["flood_map"]["start_time"] = cosmos.cycle
            config["flood_map"]["stop_time"]  = cosmos.stop_time
            config["flood_map"]["color_map"]  = cosmos.config.map_contours[cosmos.config.webviewer.flood_map_color_map]
            config["flood_map"]["color_map"]  = cosmos.config.map_contours[cosmos.config.webviewer.flood_map_color_map]
        if cosmos.config.cycle.run_mode == "cloud":
            config["access_key"] = cosmos.config.cloud_config.access_key
            config["secret_key"] = cosmos.config.cloud_config.secret_key
        
        dict2yaml(os.path.join(self.job_path, "config.yml"), config)

        if self.ensemble:
            # Write ensemble members to file
            with open(os.path.join(self.job_path, "ensemble_members.txt"), "w") as f:
                for member in cosmos.scenario.ensemble_names:
                    f.write(member + "\n")

        # Make run batch file (only for windows)
        batch_file = os.path.join(self.job_path, "run_sfincs.bat")
        fid = open(batch_file, "w")
        fid.write("@ echo off\n")
        exe_path = os.path.join(cosmos.config.executables.sfincs_path, "sfincs.exe")
        fid.write(exe_path + "\n")
        fid.close()

        # Finally set the path back to the one in cosmos\models\etc.
        self.domain.path = pth

    def move(self):
        
        job_path     = self.job_path
        output_path  = self.cycle_output_path
        input_path   = self.cycle_input_path  
        restart_path = self.restart_flow_path

        fo.move_file(os.path.join(job_path, "sfincs_map.nc"), output_path)
        fo.move_file(os.path.join(job_path, "sfincs_his.nc"), output_path)
        fo.move_file(os.path.join(job_path, "*.txt"), output_path)

        # Restart file used in simulation        
        fo.move_file(os.path.join(self.job_path, "sfincs.rst"), input_path)

        # Restart files created during simulation
        fo.move_file(os.path.join(self.job_path, "*.rst"), restart_path)

        # Input (all the rest)
        fo.move_file(os.path.join(self.job_path, "*.*"), input_path)
        
    def post_process(self):
#        import cht.misc.prob_maps as pm

        # Extract water levels

#        input_path  = self.cycle_input_path
        output_path = self.cycle_output_path
        post_path   = self.cycle_post_path

#        return    
        # if not self.domain.input.tref:
        #     # This model has been run before. The model instance has not data on tref, obs points etc.
        #     self.domain.read_input_file(os.path.join(input_path, "sfincs.inp"))
        #     self.domain.read_observation_points()
        
        # if self.ensemble:
        #     # Should really do this in the job itself            
        #     # Make probabilistic flood maps
        #     # file_list = []
        #     # file_list= fo.list_files(os.path.join(output_path, "sfincs_map_*"))
        #     # prcs= np.concatenate((np.arange(0, 0.9, 0.05), np.arange(0.9, 1, 0.01)))
        #     # vars= ["hm0", "tp"]
        #     # output_file_name = os.path.join(output_path, "hurrywave_map_ensemble.nc")
        #     # #pm.prob_floodmaps(file_list=file_list, variables=vars, prcs=prcs, delete = False, output_file_name=output_file_name)

        #     # Make probabilistic water level timeseries
        #     file_list = []
        #     for member in cosmos.scenario.ensemble_names:
        #         file_list.append(os.path.join(output_path, member, "sfincs_his.nc"))
        #     prcs= [0.05, 0.5, 0.95]
        #     vars= ["point_zs"]
        #     output_file_name = os.path.join(output_path, "sfincs_his_ensemble.nc")
        #     pm.prob_floodmaps(file_list=file_list, variables=vars, prcs=prcs, delete = False, output_file_name=output_file_name)

        if self.station:

            # Read in data for all stations
            data = {}
            if self.ensemble:
                prcs= [0.10, 0.50, 0.90]
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



        # if self.station:

        #     cosmos.log("Extracting time series from model " + self.name)    

        #     if cosmos.scenario.track_ensemble and self.ensemble:
        #         # Make probabilistic water level timeseries
        #         file_list= fo.list_files(os.path.join(output_path, "sfincs_his_*"))
        #         prcs=  [0.05, 0.5, 0.95]
        #         vars= ["point_zs"]
        #         output_file_name = os.path.join(output_path, "sfincs_his_ensemble.nc")
        #         pm.prob_floodmaps(file_list=file_list, variables=vars, prcs=prcs, delete = False, output_file_name=output_file_name)

        #     if self.domain.input.outputformat=="bin":
        #         nc_file = os.path.join(output_path, "zst.txt")
        #     else:    
        #         nc_file = os.path.join(output_path, "sfincs_his.nc")

        #     name_list=[]
        #     for station in self.station:
        #         name_list.append(station.name)
        #     v = self.domain.read_timeseries_output(name_list=name_list, file_name=nc_file)
            
        #     # Water levels in the csv files have the same datum as the model !!!            
        #     for station in self.station:
        #         df = pd.DataFrame(index=v.index)
        #         df.index.name='date_time' 
        #         df['wl']= v[station.name]                          
        #         df['wl'] = df['wl'] + station.water_level_correction

        #         if cosmos.scenario.track_ensemble and self.ensemble:
        #            nc_file = os.path.join(output_path, "sfincs_his_ensemble.nc")
        #            for ii,vv in enumerate(prcs):
        #                tmp = self.domain.read_timeseries_output(name_list = name_list, file_name=nc_file, parameter = "point_zs_" + str(round(vv*100)))
        #                df["wl_" + str(round(vv*100))]=tmp[station.name]
        #                df["wl_" + str(round(vv*100))]= df["wl_" + str(round(vv*100))]+ station.water_level_correction

        #         file_name = os.path.join(post_path,
        #                                  "waterlevel." + station.name + ".csv")
        #         df.to_csv(file_name,
        #                   date_format='%Y-%m-%dT%H:%M:%S',
        #                   float_format='%.3f')        

        return

        # # Make flood map tiles
        # if cosmos.config.cycle.make_flood_maps and self.make_flood_map:

        #     if self.ensemble:
        #         # Make probabilistic flood maps
        #         file_list= fo.list_files(os.path.join(output_path, "sfincs_map_*"))
        #         prcs= [0.05, 0.5, 0.95]#np.concatenate((np.arange(0, 0.9, 0.05), np.arange(0.9, 1, 0.01)))            
        #         vars= ["zs", "zsmax"]
        #         output_file_name = os.path.join(output_path, "sfincs_map_ensemble.nc")
        #         pm.prob_floodmaps(file_list=file_list, variables=vars, prcs=prcs, delete = False, output_file_name=output_file_name)

        #     flood_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
        #                                   "flood_map")
            
        #     index_path = os.path.join(self.path, "tiling", "indices")
        #     topo_path = os.path.join(self.path, "tiling", "topobathy")
            
        #     if os.path.exists(index_path) and os.path.exists(topo_path):
                
        #         cosmos.log("Making flood map tiles for model " + self.long_name + " ...")                

        #         # 24 hour increments  
        #         dtinc = 24
    
        #         # Wave map for the entire simulation
        #         dt1 = datetime.timedelta(hours=1)
        #         dt  = datetime.timedelta(hours=dtinc)
        #         t0  = cosmos.cycle.replace(tzinfo=None)    
        #         t1  = cosmos.stop_time
                    
        #         pathstr = []
                
        #         # 6-hour increments
        #         requested_times = pd.date_range(start=t0 + dt,
        #                                         end=t1,
        #                                         freq=str(dtinc) + "H").to_pydatetime().tolist()
    
        #         for it, t in enumerate(requested_times):
        #             pathstr.append((t - dt).strftime("%Y%m%d_%HZ") + "_" + (t).strftime("%Y%m%d_%HZ"))
    
        #         pathstr.append("combined_" + (t0).strftime("%Y%m%d_%HZ") + "_" + (t1).strftime("%Y%m%d_%HZ"))
                            
        #         zsmax_file = os.path.join(output_path, "sfincs_map.nc")
                
        #         try:
        #             # Inundation map over dt-hour increments                    
        #             for it, t in enumerate(requested_times):
    
        #                 zsmax = self.domain.read_zsmax(zsmax_file=zsmax_file,
        #                                                time_range=[t - dt + dt1, t + dt1])
        #                 flood_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
        #                                               "flood_map",
        #                                               pathstr[it])                                            
        #                 make_flood_map_tiles(zsmax, index_path, topo_path, flood_map_path,
        #                                          water_level_correction=0.0)
    
        #             # Full simulation        
        #             flood_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
        #                                           "flood_map",
        #                                            pathstr[-1])                    
        #             zsmax = self.domain.read_zsmax(zsmax_file=zsmax_file,
        #                                            time_range=[t0 + dt1, t1 + dt1])
        #             make_flood_map_tiles(zsmax, index_path, topo_path, flood_map_path,
        #                                  water_level_correction=0.0)

        #             if cosmos.scenario.track_ensemble and self.ensemble:
        #                 zsmax_file = os.path.join(output_path, "sfincs_map_ensemble.nc")
        #                 # Full simulation        
        #                 flood_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
        #                                             "flood_map", 
        #                                             pathstr[-1] + "_95")                    
        #                 zsmax = self.domain.read_zsmax(zsmax_file=zsmax_file,
        #                                             time_range=[t0 + dt1, t1 + dt1], parameter = 'zsmax_95')
        #                 make_flood_map_tiles(zsmax, index_path, topo_path, flood_map_path,
        #                                     water_level_correction=0.0)
        #         except:
        #             print("An error occured while making flood map tiles")


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



# pre-process
# Base input
#   sfincs.inp
#   sfincs.obs
#   sfincs.amu/amv/amp/ampr 
# Nesting (move most to nest.py)
# Meteo

# post_process
#   make flood maps and csv files

# run
# if ensemble:
#   run models
#   merge his files (cht)  
#   prob flood map (cht) 
#   delete unnecessary files 
# else:
#   run model
