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

from .cosmos_main import cosmos
from .cosmos_model import Model
from .cosmos_tiling import make_flood_map_tiles
import cosmos.cosmos_meteo as meteo

#import xmlkit as xml

from cht.nesting.nest1 import nest1
from cht.nesting.nest2 import nest2


class CoSMoS_SFINCS(Model):
    
    def read_model_specific(self):
        
        # Read in the SFINCS model
        
        # First set some defaults
#        self.flow_spinup_time = 0.0
        
#        xml_obj = xml.xml2obj(self.file_name)        
#        if hasattr(xml_obj, "flowspinup"):
#            self.flow_spinup_time = float(xml_obj.flowspinup[0].value)
                        
        # Now read in the domain data
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

            # Get boundary conditions from overall model (Nesting 2)

            # Correct boundary water levels. Assuming that output from overall
            # model is in MSL !!!
            zcor = self.boundary_water_level_correction - self.vertical_reference_level_difference_with_msl
            
            if cosmos.scenario.model:
                nest2(self.flow_nested.domain,
                    self.domain,
                    output_path=self.flow_nested.cycle_output_path,
                    output_file= 'sfincs_his.nc',
                    boundary_water_level_correction=zcor,
                    option="flow")

            if self.flow_nested.type == "beware":                
                # Make sfincs bnd file
                self.domain.write_flow_boundary_points(file_name = 'tmp' )

            if self.domain.input.corfile:
                
                # Add astronomic correction to time series (should really do this in nesting.py)
                
                # Read cor file
                corfile = os.path.join(self.domain.path, self.domain.input.corfile)
                d = IniStruct(filename=corfile)
                astro = d.section[0].data

                times = self.domain.flow_boundary_point[0].data.index
                names = []
                amp   = []
                phi   = []
                
                for icmp, cmp in enumerate(astro.index):                
                    names.append(cmp)
                    amp.append(astro[1][icmp])
                    phi.append(astro[2][icmp])
                
                df = pd.DataFrame()
                df["component"] = pd.Series(names) 
                df["amplitude"] = pd.Series(amp) 
                df["phase"]     = pd.Series(phi) 
                df = df.set_index("component")
                vv = predict(df, times)

                for pnt in self.domain.flow_boundary_point:
                    pnt.data += vv
                
            self.domain.write_flow_boundary_conditions(file_name = 'tmp')
            
            
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

        if self.wave and self.wave_nested:
            
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

            nest2(self.wave_nested.domain,
                  self.domain,
                  output_path=self.wave_nested.cycle_output_path,
                  option="wave")

            if self.wave_nested.type == "beware":                
                self.domain.input.wfpfile = "sfincs.wfp"
                self.domain.input.whifile = "sfincs.whi"
                self.domain.input.wtifile = "sfincs.wti"
                self.domain.input.wstfile = "sfincs.wst"
                self.domain.write_wavemaker_forcing_points()
                self.domain.write_wavemaker_forcing_conditions()
            else:
                self.domain.input.bhsfile = "sfincs.bhs"
                self.domain.input.btpfile = "sfincs.btp"
                self.domain.input.bwdfile = "sfincs.bwd"
                self.domain.input.bdsfile = "sfincs.bds"
                self.domain.write_wave_boundary_conditions()
                    
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
            self.domain.input.spwfile = "sfincs.spw"
            self.domain.input.utmzone = self.crs.utm_zone
            self.domain.input.amufile = None
            self.domain.input.amvfile = None
            self.domain.input.ampfile = None
            self.domain.input.amprfile = None
            meteo_path = os.path.join(cosmos.config.main_path, "meteo", "spiderwebs")
            src = os.path.join(meteo_path, self.meteo_spiderweb)
            fo.copy_file(src, self.job_path)
               
        # Now write input file (sfincs.inp)
        self.domain.write_input_file()

        # Make run batch file
        batch_file = os.path.join(self.job_path, "run.bat")
        fid = open(batch_file, "w")
        fid.write("@ echo off\n")
        fid.write("DATE /T > running.txt\n")
        exe_path = os.path.join(cosmos.config.sfincs_exe_path, "sfincs.exe")
        #fid.write(exe_path + "\n")
        fid.write("move running.txt finished.txt\n")
        fid.close()

        # Now loop through ensemble members
        if cosmos.scenario.track_ensemble and self.ensemble:
            
            # Use main folder as best_track
            # os.rename(self.job_path, self.job_path + "_besttrack")
            fo.copy_file(cosmos.scenario.best_track_file, os.path.join(self.job_path, "sfincs.spw"))
            self.domain.input.spwfile = "sfincs.spw"
            self.domain.input.utmzone = self.crs.utm_zone
            self.domain.input.amufile = None
            self.domain.input.amvfile = None
            self.domain.input.ampfile = None
            self.domain.input.amprfile = None
            self.domain.write_input_file()

            for member_name in cosmos.scenario.member_names:
                
                # Job path for this ensemble member
                member_path = self.job_path + "_" + member_name
                fo.mkdir(member_path)
                    
                # Boundary conditions     
                if self.flow_nested:
        
                    # Correct boundary water levels. Assuming that output from overall
                    # model is in MSL !!!
                    zcor = self.boundary_water_level_correction - self.vertical_reference_level_difference_with_msl
                    
                    # Get boundary conditions from overall model (Nesting 2)

                    # This is necessary for reading the timeseries output for nesting
                    # when this model has already run
                    if self.flow_nested.ensemble:
                        if self.flow_nested.type == "beware":
                            output_file = "beware_his_" + member_name + '.nc'
                        elif self.flow_nested.type == "sfincs":
                            output_file = "sfincs_his_" + member_name + '.nc'
                    else:
                        output_file= None


                        #if not self.flow_nested.domain.observation_point:
                        #    obs_file = os.path.join(self.flow_nested.results_path,
                        #                            "archive",
                        #                            cosmos.cycle_string,
                        #                            "input",
                        #                            "sfincs.obs")
                        #    self.flow_nested.domain.read_observation_points(file_name=obs_file)                    
                    
                    nest2(self.flow_nested.domain,
                        self.domain,
                        output_path=self.flow_nested.cycle_output_path,
                        output_file= output_file,
                        boundary_water_level_correction=zcor)                        

                    if self.domain.input.corfile:
                
                        # Add astronomic correction to time series (should really do this in nesting.py)
                        
                        # Read cor file
                        corfile = os.path.join(self.domain.path, self.domain.input.corfile)
                        d = IniStruct(filename=corfile)
                        astro = d.section[0].data

                        times = self.domain.flow_boundary_point[0].data.index
                        names = []
                        amp   = []
                        phi   = []
                        
                        for icmp, cmp in enumerate(astro.index):                
                            names.append(cmp)
                            amp.append(astro[1][icmp])
                            phi.append(astro[2][icmp])
                        
                        df = pd.DataFrame()
                        df["component"] = pd.Series(names) 
                        df["amplitude"] = pd.Series(amp) 
                        df["phase"]     = pd.Series(phi) 
                        df = df.set_index("component")
                        vv = predict(df, times)

                        for pnt in self.domain.flow_boundary_point:
                            pnt.data += vv

                    self.domain.input.bzsfile = "sfincs.bzs"
                    self.domain.write_flow_boundary_conditions(file_name= os.path.join(member_path, self.domain.input.bzsfile))

                elif self.domain.input.bcafile:
                    self.domain.input.bcafile = r"..\\" + os.path.basename(self.domain.path) + r"\\sfincs.bca"
                    self.domain.input.bzsfile = r"..\\" + os.path.basename(self.domain.path) + r"\\sfincs.bzs"

                if self.wave and self.wave_nested:
                    if self.wave_nested.ensemble:
                        if self.wave_nested.type == "beware":
                            output_file = "beware_his_" + member_name + '.nc'
                        elif self.wave_nested.type == "hurrywave":
                            output_file = "hurrywave_his_" + member_name + '.nc'
                    else:
                        output_file= None
                    
                    nest2(self.wave_nested.domain,
                        self.domain,
                        output_path=self.wave_nested.cycle_output_path,
                        output_file= output_file,
                        option="wave")

                    if self.wave_nested.type == "beware":                
                        self.domain.input.wfpfile = "sfincs.wfp"
                        self.domain.input.whifile = "sfincs.whi"
                        self.domain.input.wtifile = "sfincs.wti"
                        self.domain.input.wstfile = "sfincs.wst"

                        self.domain.write_wavemaker_forcing_points(file_name = os.path.join(member_path, self.domain.input.wfpfile))
                        self.domain.write_whi_file(file_name = os.path.join(member_path, self.domain.input.whifile))
                        self.domain.write_wti_file(file_name = os.path.join(member_path, self.domain.input.wtifile))
                        self.domain.write_wst_file(file_name = os.path.join(member_path, self.domain.input.wstfile))
                    elif self.wave_nested.type == "hurrywave":
                        self.domain.input.bhsfile = "sfincs.bhs"
                        self.domain.input.btpfile = "sfincs.btp"
                        self.domain.input.bwdfile = "sfincs.bwd"
                        self.domain.input.bdsfile = "sfincs.bds"

                        self.domain.write_bhs_file(file_name = os.path.join(member_path, self.domain.input.bhsfile))
                        self.domain.write_btp_file(file_name = os.path.join(member_path, self.domain.input.btpfile))
                        self.domain.write_bwd_file(file_name = os.path.join(member_path, self.domain.input.bwdfile))
                        self.domain.write_bds_file(file_name = os.path.join(member_path, self.domain.input.bdsfile))    

                # Copy spw file to member path
                meteo_path = os.path.join(cosmos.config.main_path, "meteo")
                spwfile = os.path.join(meteo_path,
                                       cosmos.scenario.track_ensemble,
                                       member_name + ".spw")
                fo.copy_file(spwfile, os.path.join(member_path, "sfincs.spw"))

                # Adjust input and save to .inp file
                self.domain.input.spwfile = "sfincs.spw"
                self.domain.input.utmzone = self.crs.utm_zone
                self.domain.input.amufile = None
                self.domain.input.amvfile = None
                self.domain.input.ampfile = None
                self.domain.input.amprfile = None
                self.domain.input.mskfile = r"..\\" + os.path.basename(self.domain.path) + r"\\sfincs.msk"
                self.domain.input.indexfile = r"..\\" + os.path.basename(self.domain.path) + r"\\sfincs.ind"
                self.domain.input.bndfile = r"..\\" + os.path.basename(self.domain.path) + r"\\sfincs.bnd"
                self.domain.input.sbgfile = r"..\\" + os.path.basename(self.domain.path) + r"\\sfincs.sbg"
                self.domain.input.obsfile = r"..\\" + os.path.basename(self.domain.path) + r"\\sfincs.obs"

                self.domain.write_input_file(input_file= os.path.join(member_path, "sfincs.inp"))
                fo.copy_file(os.path.join(self.job_path, 'run.bat'), member_path)

        # Set the path back to the one in cosmos\models\etc.
        self.domain.path = pth

    def move(self):
        
        # output_path = self.cycle_output_path
        # input_path  = self.cycle_input_path
        
        # Output        
        fo.move_file(os.path.join(self.job_path, "*.dat"), self.cycle_output_path)
        fo.move_file(os.path.join(self.job_path, "*.txt"), self.cycle_output_path)
        fo.move_file(os.path.join(self.job_path, "sfincs_his.nc"), self.cycle_output_path)
        fo.move_file(os.path.join(self.job_path, "sfincs_map.nc"), self.cycle_output_path)
        
        fo.move_file(os.path.join(self.job_path, "sfincs.rst"), self.cycle_input_path)

        # Restart files 
        fo.move_file(os.path.join(self.job_path, "*.rst"), self.restart_flow_path)
        # Input
        fo.move_file(os.path.join(self.job_path, "*.*"), self.cycle_input_path)
        
        if cosmos.scenario.track_ensemble and self.ensemble:
            # And now for the ensemble members
            # Only output
            for member_name in cosmos.scenario.member_names:
                
                pth = self.job_path + "_" + member_name

                if os.path.isfile(os.path.join(pth, "zst.txt")):
                    fo.move_file(os.path.join(pth, "zst.txt"), os.path.join(self.cycle_output_path, 'zst_'+ member_name +'.txt'))
                if os.path.isfile(os.path.join(pth, "zs.dat")):
                    fo.move_file(os.path.join(pth, "zs.dat"), os.path.join(self.cycle_output_path, 'zs_'+ member_name +'.dat'))
                if os.path.isfile(os.path.join(pth, "zsmax.dat")):
                    fo.move_file(os.path.join(pth, "zsmax.dat"), os.path.join(self.cycle_output_path, 'zsmax_'+ member_name +'.dat'))
                if os.path.isfile(os.path.join(pth, "sfincs_his.nc")):
                    fo.move_file(os.path.join(pth, "sfincs_his.nc"), os.path.join(self.cycle_output_path, 'sfincs_his_'+ member_name +'.nc'))
                if os.path.isfile(os.path.join(pth, "sfincs_map.nc")):
                    fo.move_file(os.path.join(pth, "sfincs_map.nc"), os.path.join(self.cycle_output_path, 'sfincs_map_'+ member_name +'.nc'))

                try:
                    shutil.rmtree(pth)
                except:
                    # Folder was probably open in another application
                    pass
        
    def post_process(self):
        import cht.misc.prob_maps as pm

        # Extract water levels

        output_path = self.cycle_output_path
        post_path   = self.cycle_post_path
        
        if cosmos.scenario.track_ensemble and self.ensemble:
            
            # Make probabilistic flood maps
            file_list= fo.list_files(os.path.join(output_path, "sfincs_map_*"))
            prcs= [0.05, 0.5, 0.95]#np.concatenate((np.arange(0, 0.9, 0.05), np.arange(0.9, 1, 0.01)))            
            vars= ["zs", "zsmax"]
            output_file_name = os.path.join(output_path, "sfincs_map_ensemble.nc")
            #pm.prob_floodmaps(file_list=file_list, variables=vars, prcs=prcs, delete = False, output_file_name=output_file_name)

            # Make probabilistic water level timeseries
            file_list= fo.list_files(os.path.join(output_path, "sfincs_his_*"))
            prcs=  [0.05, 0.5, 0.95]
            vars= ["point_zs"]
            output_file_name = os.path.join(output_path, "sfincs_his_ensemble.nc")
            #pm.prob_floodmaps(file_list=file_list, variables=vars, prcs=prcs, delete = False, output_file_name=output_file_name)

        if self.station:

            cosmos.log("Extracting time series from model " + self.name)    

            if self.domain.input.outputformat=="bin":
                nc_file = os.path.join(output_path, "zst.txt")
            else:    
                nc_file = os.path.join(output_path, "sfincs_his.nc")
            
            v = self.domain.read_timeseries_output(file_name=nc_file)
            
            # Water levels in the csv files have the same datum as the model !!!            
            for station in self.station:
                df = pd.DataFrame(index=v.index)
                df.index.name='date_time' 
                df['wl']= v[station.name]                          
                df['wl'] = df['wl'] + station.water_level_correction

                if cosmos.scenario.track_ensemble and self.ensemble:
                    nc_file = os.path.join(output_path, "sfincs_his_ensemble.nc")
                    for ii,vv in enumerate(prcs):
                        tmp = self.domain.read_timeseries_output(file_name=nc_file, parameter = "point_zs_" + str(round(vv*100)))
                        df["wl_" + str(round(vv*100))]=tmp[station.name]
                        df["wl_" + str(round(vv*100))]= df["wl_" + str(round(vv*100))]+ station.water_level_correction

                file_name = os.path.join(post_path,
                                         "waterlevel." + station.name + ".csv")
                df.to_csv(file_name,
                          date_format='%Y-%m-%dT%H:%M:%S',
                          float_format='%.3f')        


        # Make flood map tiles
        if cosmos.config.make_flood_maps and self.make_flood_map:

            flood_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                          "flood_map")
            
            index_path = os.path.join(self.path, "tiling", "indices")
            topo_path = os.path.join(self.path, "tiling", "topobathy")
            
            if os.path.exists(index_path) and os.path.exists(topo_path):
                
                cosmos.log("Making flood map tiles for model " + self.long_name + " ...")                

                # 24 hour increments  
                dtinc = 24
    
                # Wave map for the entire simulation
                dt1 = datetime.timedelta(hours=1)
                dt  = datetime.timedelta(hours=dtinc)
                t0  = cosmos.cycle_time.replace(tzinfo=None)    
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
                    for it, t in enumerate(requested_times):
    
                        zsmax = self.domain.read_zsmax(zsmax_file=zsmax_file,
                                                       time_range=[t - dt + dt1, t + dt1])
                        flood_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                                      "flood_map",
                                                      pathstr[it])                                            
                        make_flood_map_tiles(zsmax, index_path, topo_path, flood_map_path,
                                                 water_level_correction=0.0)
    
                    # Full simulation        
                    flood_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                                  "flood_map",
                                                   pathstr[-1])                    
                    zsmax = self.domain.read_zsmax(zsmax_file=zsmax_file,
                                                   time_range=[t0 + dt1, t1 + dt1])
                    make_flood_map_tiles(zsmax, index_path, topo_path, flood_map_path,
                                         water_level_correction=0.0)

                    if cosmos.scenario.track_ensemble and self.ensemble:
                        pass
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
