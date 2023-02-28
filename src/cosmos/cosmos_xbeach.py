# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:02:04 2021

@author: ormondt
"""

import os
import numpy as np
import datetime
import xarray as xr

from .cosmos import cosmos
from .cosmos_model import Model
from .cosmos_tiling import make_sedero_tiles
from .cosmos_tiling import make_bedlevel_tiles



import cht.misc.xmlkit as xml
import cht.misc.fileops as fo
from cht.xbeach.xbeach import XBeach
import cht.nesting.nesting as nesting

class CoSMoS_XBeach(Model):
    
    def read_model_specific(self):
        
        # Read in the XBeach model
        
        # First set some defaults
        
        flow_nesting_point_x = []
        flow_nesting_point_y = []
        wave_nesting_point_x = []
        wave_nesting_point_y = []
                  
        xml_obj = xml.xml2obj(self.file_name)        
        if hasattr(xml_obj, "flow_nesting_point_1"):
            xystr = xml_obj.flow_nesting_point_1[0].value.split(",")
            flow_nesting_point_x.append(float(xystr[0]))
            flow_nesting_point_y.append(float(xystr[1]))
        if hasattr(xml_obj, "flow_nesting_point_2"):
            xystr = xml_obj.flow_nesting_point_2[0].value.split(",")
            flow_nesting_point_x.append(float(xystr[0]))
            flow_nesting_point_y.append(float(xystr[1]))
        if hasattr(xml_obj, "flow_nesting_point_3"):
            xystr = xml_obj.flow_nesting_point_3[0].value.split(",")
            flow_nesting_point_x.append(float(xystr[0]))
            flow_nesting_point_y.append(float(xystr[1]))
        if hasattr(xml_obj, "flow_nesting_point_4"):
            xystr = xml_obj.flow_nesting_point_4[0].value.split(",")
            flow_nesting_point_x.append(float(xystr[0]))
            flow_nesting_point_y.append(float(xystr[1]))            
                        
        if hasattr(xml_obj, "wave_nesting_point_1"):
            xystr = xml_obj.wave_nesting_point_1[0].value.split(",")
            wave_nesting_point_x.append(float(xystr[0]))
            wave_nesting_point_y.append(float(xystr[1]))   
                        
        # Now read in the domain data
        input_file  = os.path.join(self.path, "input", "params.txt")
        self.domain = XBeach(input_file=input_file, get_boundary_coordinates=False)
        # Give names to the boundary points
        for ipnt, pnt in enumerate(self.domain.flow_boundary_point):
            pnt.name = str(ipnt + 1).zfill(4)
        for ipnt, pnt in enumerate(self.domain.wave_boundary_point):
            pnt.name = str(ipnt + 1).zfill(4)
        
        # Replace boundary points for nesting    
        if flow_nesting_point_x:
            #remove the default found boundary locations based on the tideloc and xbeach routine
            self.domain.flow_boundary_point[len(flow_nesting_point_x):] = []
            for ipnt, pnt in enumerate(flow_nesting_point_x):            
                self.domain.flow_boundary_point[ipnt].geometry.x = flow_nesting_point_x[ipnt]
                self.domain.flow_boundary_point[ipnt].geometry.y = flow_nesting_point_y[ipnt]

        if wave_nesting_point_x:
            for ipnt, pnt in enumerate(wave_nesting_point_x):            
                self.domain.wave_boundary_point[ipnt].geometry.x = wave_nesting_point_x[ipnt]
                self.domain.wave_boundary_point[ipnt].geometry.y = wave_nesting_point_y[ipnt]

        if hasattr(xml_obj, "zb_deshoal"):
            self.domain.zb_deshoal = xml_obj.zb_deshoal[0].value
            
        # Copy some attributes to the model domain (needed for nesting)
        self.domain.crs   = self.crs
        self.domain.type  = self.type
        self.domain.name  = self.name
        self.domain.runid = self.runid
        
        
    def pre_process(self):
        
        # First generate input that is identical for all members
                
        # Set path temporarily to job path
        pth = self.domain.path
        self.domain.path = self.job_path
        
        # Start and stop times
        self.domain.tref   = self.flow_start_time
        self.domain.tstop = self.flow_stop_time
        self.domain.params["tstop"] = (self.flow_stop_time - self.flow_start_time).total_seconds()

        t0 = None
        t1 = None
        if self.peak_boundary_time:
            # Round to nearest hour
            h0 = self.peak_boundary_time.hour
            tpeak = self.peak_boundary_time.replace(microsecond=0, second=0, minute=0, hour=h0)
            t0 = tpeak - 12*datetime.timedelta(hours=1)
            t1 = tpeak + 12*datetime.timedelta(hours=1)
            t0 = max(t0, self.flow_start_time)
            t1 = min(t1, self.flow_stop_time)
            self.domain.tref  = t0
            self.domain.tstop = t1
            self.domain.params["tstop"] = (t1 - t0).total_seconds()
            self.domain.params["tintg"] = (t1 - t0).total_seconds()
            self.domain.params["tintm"] = (t1 - t0).total_seconds()

        # Boundary conditions        
        if self.flow_nested:

            # Get boundary conditions from overall model (Nesting 2)
            
            # Correct boundary water levels. Assuming that output from overall
            # model is in MSL !!!
            zcor = self.boundary_water_level_correction - self.vertical_reference_level_difference_with_msl

            nesting.nest2(self.flow_nested.domain,
                          self.domain,
                          output_path=self.flow_nested.cycle_output_path,
                          boundary_water_level_correction=zcor)

            self.domain.write_flow_boundary_conditions()

        # Boundary conditions        
        if self.wave_nested:

            # Get boundary conditions from overall model (Nesting 2)
            
            #define whether you want to use jonstable or sp2-files as boundary conditions
            option = "timeseries"
                            
            nesting.nest2(self.wave_nested.domain,
                          self.domain,
                          output_path=self.wave_nested.cycle_output_path,
                          option=option)

            if option == "sp2":
                self.domain.params["bcfile"] = "sp2list.txt"
                self.domain.params["instat"] = 5
            elif option == "timeseries":
                self.domain.params["bcfile"] = "jonswap.txt"
                self.domain.params["wbctype"] = "jonstable"
                                            
            self.domain.write_wave_boundary_conditions(option=option)
                    
        # Now write input file (params.txt)
        params_file = os.path.join(self.job_path, "params.txt")
        self.domain.params.tofile(filename=params_file)

        # Make run batch file
        batch_file = os.path.join(self.job_path, "run.bat")
        fid = open(batch_file, "w")
        fid.write("@ echo off\n")
        fid.write("DATE /T > running.txt\n")
        fid.write("set xbeachdir=" + cosmos.config.xbeach_exe_path + "\n")
        fid.write('set mpidir="c:\\Program Files\\MPICH2\\bin"\n')
        fid.write("set PATH=%xbeachdir%;%PATH%\n")
        fid.write("set PATH=%mpidir%;%PATH%\n")
        fid.write("mpiexec.exe -n 5 %xbeachdir%\\xbeach.exe\n")
        fid.write("del q_*\n")
        fid.write("del E_*\n")
        fid.write("move running.txt finished.txt\n")
        fid.close()

        # Set the path back to the one in cosmos\models\etc.
        self.domain.path = pth

    def move(self):
        
        # Move files from job folder to archive folder
        
        # First clear archive folder      
        
        job_path    = self.job_path
        output_path = self.cycle_output_path
        input_path = self.cycle_input_path
        
        # Output        
        fo.move_file(os.path.join(job_path, "*.nc"), output_path)
        fo.move_file(os.path.join(job_path, "finished.txt"), output_path)

        # Input
        fo.move_file(os.path.join(job_path, "*.*"), input_path)

    def post_process(self):
        
        output_path = self.cycle_output_path
        sedero_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                       "sedero")
        zb0_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                       "zb0")  
        zbend_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                       "zbend")              
        index_path = os.path.join(self.path, "tiling", "indices")
        
        if os.path.exists(index_path):
            # settings
            try:
                # read xbeach output
                output_file = os.path.join(output_path, 'xboutput.nc')
                dt = xr.open_dataset(output_file)
            except:
                print("ERROR while making xbeach tiles")
                return
        
            var = 'sedero'
            elev_min = -2
            # mask xbeach output based on a min elevation of the initial topobathymetry
            val = dt[var][-1, :, :].where(dt['zb'][0, :, :] > elev_min)
            val_masked = val.values
            
            cosmos.log("Making sedimenation/erosion tiles for model " + self.name)
            # make pngs
            make_sedero_tiles(val_masked, index_path, sedero_map_path)
            cosmos.log("Sedimentation/erosion tiles done.")
            
            zb0 = dt['zb'][0, :, :].values
            zbend = dt['zb'][-1, :, :].values
            cosmos.log("Making bedlevel tiles for model " + self.name)
            make_bedlevel_tiles(zb0, index_path, zb0_map_path)
            make_bedlevel_tiles(zbend, index_path, zbend_map_path)
            cosmos.log("Bed level tiles done.")
            

                
