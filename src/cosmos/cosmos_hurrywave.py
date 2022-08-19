# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:02:04 2021

@author: ormondt
"""

import os
import pandas as pd
import datetime

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
        input_file  = os.path.join(self.path, "input", "hurrywave.inp")
        self.domain = HurryWave(input_file)

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
        self.domain.input.tstart   = self.wave_start_time
        self.domain.input.tstop    = self.wave_stop_time
#        nsecs = (self.wave_stop_time - self.wave_start_time).total_seconds()
#        self.domain.input.dtmaxout = nsecs
        self.domain.input.dtmaxout = 21600.0
        self.domain.input.dtmapout = 21600.0
        self.domain.input.outputformat = "net"

        # Boundary conditions        
        if self.wave_nested:

            # Get boundary conditions from overall model (Nesting 2)
            nesting.nest2(self.wave_nested.domain,
                          self.domain,
                          output_path=self.wave_nested.cycle_output_path)

            self.domain.input.bspfile = "hurrywave.bsp"
            self.domain.write_boundary_conditions()
                    
        # Meteo forcing
        self.meteo_atmospheric_pressure = False
        self.meteo_precipitation = False
        if self.meteo_wind:

            meteo.write_meteo_input_files(self,
                                          "hurrywave",
                                          self.domain.input.tref)

            self.domain.input.amufile = "hurrywave.amu"
            self.domain.input.amvfile = "hurrywave.amv"
    
            # if self.meteo_spiderweb:
            #     self.domain.input.spwfile = self.meteo_spiderweb
            #     self.domain.input.baro    = 1
            #     src = os.path.join("d:\\cosmos\\externalforcing\\meteo\\",
            #                        "spiderwebs",
            #                        self.meteo_spiderweb)
            #     fo.copy_file(src, self.job_path)

        if self.meteo_spiderweb:
            
            # Spiderweb file given, copy to job folder

            self.domain.input.spwfile = self.meteo_spiderweb
            meteo_path = os.path.join(cosmos.config.main_path, "meteo", "spiderwebs")
            src = os.path.join(meteo_path, self.meteo_spiderweb)
            fo.copy_file(src, self.job_path)

        # Make observation points
        if self.station:

            for station in self.station:
                if not self.domain.input.obsfile:
                    self.domain.input.obsfile = "hurrywave.obs"
                self.domain.add_observation_point(station.x,
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
                if not self.domain.input.ospfile:
                    self.domain.input.ospfile = "hurrywave.osp"
                self.domain.write_observation_points_sp2()                            
                if self.domain.input.dtsp2out == 0.0:
                    self.domain.input.dtsp2out = 3600.0

        if self.domain.observation_point:
            if not self.domain.input.obsfile:
                self.domain.input.obsfile = "hurrywave.obs"            
            self.domain.write_observation_points()

        # Make restart file
        trstsec = self.domain.input.tstop.replace(tzinfo=None) - self.domain.input.tref            
        if self.meteo_subset:
            if self.meteo_subset.last_analysis_time:
                trstsec = self.meteo_subset.last_analysis_time.replace(tzinfo=None) - self.domain.input.tref
        self.domain.input.trstout  = trstsec.total_seconds()
        self.domain.input.dtrstout = 0.0
        
        # Get restart file from previous cycle
        if self.wave_restart_file:
            src = os.path.join(self.restart_wave_path,
                               self.wave_restart_file)
            dst = os.path.join(self.job_path,
                               "hurrywave.rst")
            fo.copy_file(src, dst)
            self.domain.input.rstfile = "hurrywave.rst"
            self.domain.input.tspinup = 0.0

        # Now write input file (sfincs.inp)
        self.domain.write_input_file()

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

    def post_process(self):
        
        # Extract water levels

        input_path  = self.cycle_input_path
        output_path = self.cycle_output_path
        post_path   = self.cycle_post_path
            
#        zstfile = os.path.join(output_path, "zst.txt")
        
        if not self.domain.input.tref:
            # This model has been run before. The model instance has not data on tref, obs points etc.
            self.domain.read_input_file(os.path.join(input_path, "hurrywave.inp"))
            self.domain.read_observation_points()
        
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
#                vv=v[station.name]
#                vv.index.name='date_time'
#                vv.name='hm0'
                file_name = os.path.join(post_path,
                                         "waves." + station.name + ".csv")
                df.to_csv(file_name,
                          date_format='%Y-%m-%dT%H:%M:%S',
                          float_format='%.3f')        

            # v = self.domain.read_timeseries_output(path=output_path,
            #                                        parameter="tp")
            # for station in self.station:                
            #     vv=v[station.name]
            #     df.index.name='date_time'
            #     vv.name='hm0'
            #     file_name = os.path.join(post_path,
            #                              "tp." + station.name + ".csv")
            #     vv.to_csv(file_name,
            #               date_format='%Y-%m-%dT%H:%M:%S',
            #               float_format='%.3f')        

        # Make wave map tiles
        if cosmos.config.make_wave_maps and self.make_wave_map and not cosmos.config.webviewer:

            index_path = os.path.join(self.path, "tiling", "indices")
            
            if os.path.exists(index_path):
                
                if self.domain.input.outputformat[0:2] == "bin":
                    file_name = os.path.join(output_path, "hm0max.dat")
                elif self.domain.input.outputformat[0:2] == "asc":
                    file_name = os.path.join(output_path, "hm0max.txt")
                else:
                    file_name = os.path.join(output_path, "hurrywave_map.nc")

                # Wave map for the entire simulation
                dt1 = datetime.timedelta(hours=1)
                dt6 = datetime.timedelta(hours=6)
                dt7 = datetime.timedelta(hours=7)
                t0 = cosmos.cycle_time.replace(tzinfo=None)    
                t1 = cosmos.stop_time
                tr = [t0 + dt7, t1 + dt1]
                tstr = "combined_" + (t0).strftime("%Y%m%d_%HZ") + "_" + (t1).strftime("%Y%m%d_%HZ")
                ttlstr = "Combined 48-hour forecast"

                hm0_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                            "hm0",
                                            tstr)

                hm0max = self.domain.read_hm0max(hm0max_file=file_name,
                                                  time_range=tr)
    
                make_wave_map_tiles(hm0max, index_path, hm0_map_path,"Hm0")

                # Wave map over 6-hour increments
                
                # Loop through time
                t0 = cosmos.cycle_time.replace(tzinfo=None)    
                requested_times = pd.date_range(start=t0 + dt6,
                                          end=t1,
                                          freq='6H').to_pydatetime().tolist()
                
                cosmos.log("Making wave map tiles ...")    
                for it, t in enumerate(requested_times):
                    tr = [t - dt1, t + dt1]
                    hm0max = self.domain.read_hm0max(hm0max_file=file_name,
                                                      time_range=tr)
                    
                    tstr = (t - dt6).strftime("%Y%m%d_%HZ") + "_" + (t).strftime("%Y%m%d_%HZ")
                    ttlstr = (t - dt6).strftime("%Y-%m-%d %H:%M") + " - " + (t).strftime("%Y-%m-%d %H:%M") + " UTC"
                    hm0_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                                "hm0",
                                                tstr)
                    
                    make_wave_map_tiles(hm0max, index_path, hm0_map_path,"Hm0")

                cosmos.log("Wave map tiles done.")    


