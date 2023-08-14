# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:02:04 2021

@author: ormondt
"""

import os
import pandas as pd
import datetime
import shutil

from .cosmos_main import cosmos
from .cosmos_model import Model
from .cosmos_tiling import make_wave_map_tiles
import cosmos.cosmos_meteo as meteo

from cht.hurrywave.hurrywave import HurryWave
import cht.misc.fileops as fo
import cht.nesting.nesting as nesting

class CoSMoS_HurryWave(Model):
    
    def read_model_specific(self):
        
        # Read in the HurryWave model
        
        # Now read in the domain data
        self.domain = HurryWave(path=os.path.join(self.path, "input"), load=True)

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
        self.domain.input.variables.tref     = cosmos.scenario.ref_date
        self.domain.input.variables.tstart   = self.wave_start_time
        self.domain.input.variables.tstop    = self.wave_stop_time
#        nsecs = (self.wave_stop_time - self.wave_start_time).total_seconds()
#        self.domain.input.dtmaxout = nsecs
        self.domain.input.variables.dtmaxout = 21600.0
        self.domain.input.variables.dtmapout = 21600.0
        self.domain.input.variables.outputformat = "net"

        # Boundary conditions        
        if self.wave_nested:

            # Get boundary conditions from overall model (Nesting 2)
            nesting.nest2(self.wave_nested.domain,
                          self.domain,
                          output_path=self.wave_nested.cycle_output_path)

            self.domain.input.variables.bspfile = "hurrywave.bsp"
            self.domain.boundary_conditions.write()
                    
        # Meteo forcing
        self.meteo_atmospheric_pressure = False
        self.meteo_precipitation = False
        if self.meteo_wind:

            meteo.write_meteo_input_files(self,
                                          "hurrywave",
                                          self.domain.input.variables.tref)

            self.domain.input.variables.amufile = "hurrywave.amu"
            self.domain.input.variables.amvfile = "hurrywave.amv"
    
        if self.meteo_spiderweb or cosmos.scenario.track_ensemble:
            
            # Spiderweb file given, copy to job folder
            if self.meteo_spiderweb:
                self.domain.input.variables.spwfile = self.meteo_spiderweb
                meteo_path = os.path.join(cosmos.config.main_path, "meteo", "spiderwebs")
                fo.copy_file(os.path.join(meteo_path, self.meteo_spiderweb), self.job_path)
            elif cosmos.scenario.track_ensemble:
                self.domain.input.variables.spwfile = "hurrywave.spw"
                fo.copy_file(cosmos.scenario.best_track_file, os.path.join(self.job_path, "hurrywave.spw"))
            self.domain.input.variables.amufile = None
            self.domain.input.variables.amvfile = None

        # Make observation points
        if self.station:

            for station in self.station:
                if not self.domain.input.variables.obsfile:
                    self.domain.input.variables.obsfile = "hurrywave.obs"
                self.domain.observation_points_regular.add_point(station.x,
                                                                 station.y,
                                                                 station.name)
#            self.domain.write_observation_points()
                
        # Add observation points for nested models (Nesting 1)
        if self.nested_wave_models:
            
            for nested_model in self.nested_wave_models:

                specout = False
                if nested_model.type=="xbeach":
                    specout = True
                    nesting.nest1(self.domain, nested_model.domain, option="sp2")
                elif nested_model.type=="sfincs":
                    # No sp2 output
                    nested_model.domain.input.bwvfile = "snapwave.bnd"
                    nested_model.domain.read_wave_boundary_points()
                    nesting.nest1(self.domain, nested_model.domain)
                    nested_model.domain.input.bwvfile = None
                else:
                    specout = True
                    nesting.nest1(self.domain, nested_model.domain)
                    
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
        if self.meteo_subset:
            if self.meteo_subset.last_analysis_time:
                trstsec = self.meteo_subset.last_analysis_time.replace(tzinfo=None) - self.domain.input.variables.tref
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

        # Make run batch file
        batch_file = os.path.join(self.job_path, "run.bat")
        fid = open(batch_file, "w")
        fid.write("@ echo off\n")
        fid.write("DATE /T > running.txt\n")
        exe_path = os.path.join(cosmos.config.hurrywave_exe_path, "hurrywave.exe")
        fid.write(exe_path + "\n")
        fid.write("move running.txt finished.txt\n")
        # fid.write("exit\n")
        fid.close()

        # Now loop through ensemble members
        if cosmos.scenario.track_ensemble and self.ensemble:
            
            # Use main folder as best_track folder with spiderweb forcing
            # os.rename(self.job_path, self.job_path + "_besttrack")
            fo.copy_file(cosmos.scenario.best_track_file, os.path.join(self.job_path, "hurrywave.spw"))
            self.domain.input.variables.spwfile = "hurrywave.spw"
            self.domain.input.variables.amufile = None
            self.domain.input.variables.amvfile = None
            self.domain.input.write()

            for member_name in cosmos.scenario.member_names:
                
                # Job path for this ensemble member
                member_path = self.job_path + "_" + member_name
                fo.mkdir(member_path)
                self.domain.path = member_path

                # Boundary conditions 
                zcor = self.boundary_water_level_correction - self.vertical_reference_level_difference_with_msl
       
                if self.wave_nested:
                    # Get boundary conditions from overall model (Nesting 2)
                    if self.wave_nested.ensemble:
                         output_file = "hurrywave_sp2_" + member_name + '.nc'
                    else:
                        output_file = None

                    nesting.nest2(self.wave_nested.domain,
                        self.domain,
                        output_path=self.wave_nested.cycle_output_path,
                        output_file= output_file,
                        boundary_water_level_correction=zcor)

                    self.domain.input.variables.bspfile = "hurrywave.bsp"
                    self.domain.input.variables.bndfile = r"..\\" + os.path.basename(self.job_path) + r"\\hurrywave.bnd"
                    self.domain.boundary_conditions.write()
                
                # Copy spw file to member path
                meteo_path = os.path.join(cosmos.config.main_path, "meteo")
                spwfile = os.path.join(meteo_path,
                                       cosmos.scenario.track_ensemble,
                                       member_name + ".spw")
                fo.copy_file(spwfile, os.path.join(member_path, "hurrywave.spw"))
                
                # Adjust input and save to .inp file
                self.domain.input.variables.spwfile = "hurrywave.spw"  
                self.domain.input.variables.amufile = None
                self.domain.input.variables.amvfile = None
                self.domain.input.variables.depfile = r"..\\" + os.path.basename(self.job_path) + r"\\hurrywave.dep"
                self.domain.input.variables.mskfile = r"..\\" + os.path.basename(self.job_path) + r"\\hurrywave.msk"
                self.domain.input.variables.obsfile = r"..\\" + os.path.basename(self.job_path) + r"\\hurrywave.obs"
                self.domain.input.variables.ospfile = r"..\\" + os.path.basename(self.job_path) + r"\\hurrywave.osp"


                self.domain.input.write()
                fo.copy_file(os.path.join(self.job_path, 'run.bat'), member_path)

        # Set the path back to the one in cosmos\models\etc.
        self.domain.path = pth

    def move(self):
        
        # Move files from job folder to archive folder
        
        # First clear archive folder      
        
        job_path    = self.job_path

        # Delete finished.txt file
        # fo.delete_file(os.path.join(job_path, "finished.txt"))
        
        output_path  = self.cycle_output_path
        input_path   = self.cycle_input_path  
        restart_path = self.restart_wave_path
        
        # Output        
        fo.move_file(os.path.join(job_path, "hurrywave_map.nc"), output_path)
        fo.move_file(os.path.join(job_path, "hurrywave_his.nc"), output_path)
        fo.move_file(os.path.join(job_path, "hurrywave_sp2.nc"), output_path)
        fo.move_file(os.path.join(job_path, "*.txt"), output_path)

        fo.move_file(os.path.join(job_path, "hurrywave.rst"), input_path)

        # Restart files 
        fo.move_file(os.path.join(job_path, "*.rst"), restart_path)

        # Input
        fo.move_file(os.path.join(job_path, "*.*"), input_path)

        if cosmos.scenario.track_ensemble and self.ensemble:
            # And now for the ensemble members
            # Only output
            for member_name in cosmos.scenario.member_names:
                
                pth = self.job_path + "_" + member_name

                if os.path.isfile(os.path.join(pth, "hurrywave_his.nc")):
                    fo.move_file(os.path.join(pth, "hurrywave_his.nc"), os.path.join(self.cycle_output_path, 'hurrywave_his_'+ member_name +'.nc'))
                if os.path.isfile(os.path.join(pth, "hurrywave_map.nc")):
                    fo.move_file(os.path.join(pth, "hurrywave_map.nc"), os.path.join(self.cycle_output_path, 'hurrywave_map_'+ member_name +'.nc'))
                if os.path.isfile(os.path.join(pth, "hurrywave_sp2.nc")):
                    fo.move_file(os.path.join(pth, "hurrywave_sp2.nc"), os.path.join(self.cycle_output_path, 'hurrywave_sp2_'+ member_name +'.nc'))
                if os.path.isfile(os.path.join(pth, "hurrywave.rst")):
                    fo.move_file(os.path.join(pth, "hurrywave.rst"), os.path.join(self.cycle_output_path, 'hurrywave_'+ member_name +'.rst'))

                try:
                    shutil.rmtree(pth)
                except:
                    # Folder was probably open in another application
                    pass


    def post_process(self):
        import xarray as xr
        import numpy as np
        import cht.misc.prob_maps as pm
        # Extract water levels

        input_path  = self.cycle_input_path
        output_path = self.cycle_output_path
        post_path   = self.cycle_post_path
            
        if not self.domain.input.variables.tref:
            # This model has been run before. The model instance has not data on tref, obs points etc.
            self.domain.read_input_file(os.path.join(input_path, "hurrywave.inp"))
            self.domain.read_observation_points()
        
        if cosmos.scenario.track_ensemble and self.ensemble:
            
            # Make probabilistic flood maps
            file_list= fo.list_files(os.path.join(output_path, "hurrywave_map_*"))
            prcs= np.concatenate((np.arange(0, 0.9, 0.05), np.arange(0.9, 1, 0.01)))
            vars= ["hm0", "tp"]
            output_file_name = os.path.join(output_path, "hurrywave_map_ensemble.nc")
            #pm.prob_floodmaps(file_list=file_list, variables=vars, prcs=prcs, delete = False, output_file_name=output_file_name)

            # Make probabilistic wave timeseries
            file_list= fo.list_files(os.path.join(output_path, "hurrywave_his_*"))
            prcs= [0.05, 0.5, 0.95]#np.concatenate((np.arange(0, 0.9, 0.05), np.arange(0.9, 1, 0.01)))
            vars= ["point_hm0", "point_tp"]
            output_file_name = os.path.join(output_path, "hurrywave_his_ensemble.nc")
            pm.prob_floodmaps(file_list=file_list, variables=vars, prcs=prcs, delete = False, output_file_name=output_file_name)

        if self.station:

            vhm0 = self.domain.read_timeseries_output(path=output_path,
                                                      parameter="hm0")
            vtp  = self.domain.read_timeseries_output(path=output_path,
                                                      parameter="tp")
            for station in self.station:                
                
                df = pd.DataFrame(index=vhm0.index)
                # df.index=vhm0.index
                df.index.name='date_time'
                df["Hm0"]=vhm0[station.name]
                df["Tp"]=vtp[station.name]

                if cosmos.scenario.track_ensemble and self.ensemble:
                    for i,v in enumerate(prcs):
                        vhm0 = self.domain.read_timeseries_output(path=output_path,
                                            file_name= "hurrywave_his_ensemble.nc",
                                            parameter= "hm0_" + str(round(v*100)))
                        vtp  = self.domain.read_timeseries_output(path=output_path,
                                            file_name= "hurrywave_his_ensemble.nc",
                                            parameter="tp_"+ str(round(v*100)))
                        df["Hm0_" + str(round(v*100))]=vhm0[station.name]
                        df["Tp_" + str(round(v*100))]=vtp[station.name]

                file_name = os.path.join(post_path,
                                         "waves." + station.name + ".csv")
                df.to_csv(file_name,
                          date_format='%Y-%m-%dT%H:%M:%S',
                          float_format='%.3f')        


        # Make wave map tiles
        if cosmos.config.make_wave_maps:

            # 24 hour increments  
            dtinc = 24

            # Wave map for the entire simulation
            dt1 = datetime.timedelta(hours=1)
            dt  = datetime.timedelta(hours=dtinc)
            t0  = cosmos.cycle_time.replace(tzinfo=None)    
            t1  = cosmos.stop_time
            
            # Determine if wave maps can be made
            okay  = False
            index_path = os.path.join(self.path, "tiling", "indices")
            if self.make_wave_map and os.path.exists(index_path):            
                 okay = True

            if okay:

                cosmos.log("Making wave map tiles for model " + self.long_name + " ...")                

                contour_set = "Hm0"            
                pathstr = []
                
                # 6-hour increments
                requested_times = pd.date_range(start=t0 + dt,
                                                end=t1,
                                                freq=str(dtinc) + "H").to_pydatetime().tolist()
    
                for it, t in enumerate(requested_times):
                    pathstr.append((t - dt).strftime("%Y%m%d_%HZ") + "_" + (t).strftime("%Y%m%d_%HZ"))
    
                pathstr.append("combined_" + (t0).strftime("%Y%m%d_%HZ") + "_" + (t1).strftime("%Y%m%d_%HZ"))
                            
                file_name = os.path.join(self.cycle_output_path, "hurrywave_map.nc")
                
                # Wave map over dt-hour increments                    
                for it, t in enumerate(requested_times):
                    hm0max = self.domain.read_hm0max(hm0max_file=file_name,
                                                      time_range=[t - dt + dt1, t + dt1])                        
                    hm0_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                                "hm0",
                                                pathstr[it])                        
                    make_wave_map_tiles(np.transpose(hm0max), index_path, hm0_map_path, contour_set)

                # Full simulation        
                hm0_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                            "hm0",
                                            pathstr[-1])                    
                hm0max = self.domain.read_hm0max(hm0max_file=file_name,
                                                  time_range=[t0, t1 + dt1])        
                make_wave_map_tiles(np.transpose(hm0max), index_path, hm0_map_path, contour_set)
















#         # Make wave map tiles
# #        if cosmos.config.make_wave_maps and self.make_wave_map and not cosmos.config.webviewer:
#         if cosmos.config.make_wave_maps and self.make_wave_map:

#             index_path = os.path.join(self.path, "tiling", "indices")
            
#             if os.path.exists(index_path):
                
#                 if self.domain.input.outputformat[0:2] == "bin":
#                     file_name = os.path.join(output_path, "hm0max.dat")
#                 elif self.domain.input.outputformat[0:2] == "asc":
#                     file_name = os.path.join(output_path, "hm0max.txt")
#                 else:
#                     file_name = os.path.join(output_path, "hurrywave_map.nc")



                
#                 # 6-hour increments
#                 requested_times = pd.date_range(start=t0 + dt6,
#                                                 end=t1,
#                                                 freq='6H').to_pydatetime().tolist()
    
#                 for it, t in enumerate(requested_times):
#                     pathstr.append((t - dt6).strftime("%Y%m%d_%HZ") + "_" + (t).strftime("%Y%m%d_%HZ"))
#                     namestr.append((t - dt6).strftime("%Y-%m-%d %H:%M") + " - " + (t).strftime("%Y-%m-%d %H:%M") + " UTC")
    
#                 pathstr.append("combined_" + (t0).strftime("%Y%m%d_%HZ") + "_" + (t1).strftime("%Y%m%d_%HZ"))
#                 td = t1 - t0
#                 hrstr = str(int(td.days * 24 + td.seconds/3600))
#                 namestr.append("Combined " + hrstr + "-hour forecast")
                    
#                 for model in cosmos.scenario.model:
#                     if model.type=="hurrywave":
#                         index_path = os.path.join(model.path, "tiling", "indices")            
#                         if model.make_wave_map and os.path.exists(index_path):                            
                            
#                             cosmos.log("Making wave map tiles for model " + model.long_name + " ...")                
        
#                             file_name = os.path.join(model.cycle_output_path, "hurrywave_map.nc")
                            
#                             # Wave map over 6-hour increments                    
#                             for it, t in enumerate(requested_times):
#                                 hm0max = model.domain.read_hm0max(hm0max_file=file_name,
#                                                                   time_range=[t - dt1, t + dt1])                        
#                                 hm0_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
#                                                             "hm0",
#                                                             pathstr[it])                        
#                                 make_wave_map_tiles(hm0max, index_path, hm0_map_path, contour_set)
        
#                             # Full simulation        
#                             hm0_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
#                                                         "hm0",
#                                                         pathstr[-1])                    
#                             hm0max = model.domain.read_hm0max(hm0max_file=file_name,
#                                                               time_range=[t0, t1 + dt1])        
#                             make_wave_map_tiles(hm0max, index_path, hm0_map_path, contour_set)
















#                 # Wave map for the entire simulation
#                 dt1 = datetime.timedelta(hours=1)
# #                dt6 = datetime.timedelta(hours=6)
#                 dt24 = datetime.timedelta(hours=24)
# #                dt7 = datetime.timedelta(hours=7)
#                 t0 = cosmos.cycle_time.replace(tzinfo=None)    
#                 t1 = cosmos.stop_time
#                 tr = [t0 + dt7, t1 + dt1]
#                 tstr = "combined_" + (t0).strftime("%Y%m%d_%HZ") + "_" + (t1).strftime("%Y%m%d_%HZ")
#                 ttlstr = "Combined 48-hour forecast"

#                 hm0_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
#                                             "hm0",
#                                             tstr)

#                 hm0max = self.domain.read_hm0max(hm0max_file=file_name,
#                                                   time_range=tr)
    
#                 make_wave_map_tiles(hm0max, index_path, hm0_map_path,"Hm0")

#                 # Wave map over 6-hour increments
                
#                 # Loop through time
#                 t0 = cosmos.cycle_time.replace(tzinfo=None)    
#                 requested_times = pd.date_range(start=t0 + dt6,
#                                           end=t1,
#                                           freq='6H').to_pydatetime().tolist()
                
#                 cosmos.log("Making wave map tiles ...")    
#                 for it, t in enumerate(requested_times):
#                     tr = [t - dt1, t + dt1]
#                     hm0max = self.domain.read_hm0max(hm0max_file=file_name,
#                                                       time_range=tr)
                    
#                     tstr = (t - dt6).strftime("%Y%m%d_%HZ") + "_" + (t).strftime("%Y%m%d_%HZ")
#                     ttlstr = (t - dt6).strftime("%Y-%m-%d %H:%M") + " - " + (t).strftime("%Y-%m-%d %H:%M") + " UTC"
#                     hm0_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
#                                                 "hm0",
#                                                 tstr)
                    
#                     make_wave_map_tiles(hm0max, index_path, hm0_map_path,"Hm0")

#                 cosmos.log("Wave map tiles done.")    


