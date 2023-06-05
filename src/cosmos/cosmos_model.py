# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:38:37 2021

@author: ormondt
"""

import os
from pyproj import CRS
from pyproj import Transformer
import copy
from matplotlib import path   
import pandas as pd                     
from scipy import interpolate
import numpy as np

from .cosmos_main import cosmos
from .cosmos_cluster import cluster_dict as cluster

import cht.misc.xmlkit as xml
from cht.nesting.nest1 import nest1
from cht.nesting.nest2 import nest2

class Model:
    """Read generic model data from xml file, prepare model run paths, and submit jobs.

    """
    def __init__(self):
        """Initialize model attributes described in xml file.

        See Also
        --------
        cosmos.cosmos_scenario

        """

        self.flow               = False
        self.wave               = False
        self.priority           = 10    
#        self.flow_nested        = False
#        self.wave_nested        = False
        self.flow_nested        = None
        self.wave_nested        = None
        self.bw_nested        = None
        self.flow_nested_name   = None
        self.wave_nested_name   = None
        self.bw_nested_name   = None
        self.nested_flow_models = []
        self.nested_wave_models = []
        self.nested_bw_models = []
        self.flow_spinup_time   = 0.0
        self.wave_spinup_time   = 0.0
        self.xlim               = None
        self.ylim               = None
        self.flow_restart_file  = None
        self.wave_restart_file  = None
        self.vertical_reference_level_name = "MSL"
        self.vertical_reference_level_difference_with_msl = 0.0
        self.boundary_water_level_correction = 0.0
        self.station            = []
        self.meteo_subset       = None
        self.meteo_spiderweb    = None
        self.meteo_dataset      = None
        self.meteo_wind         = True
        self.meteo_atmospheric_pressure = True
        self.meteo_precipitation        = False
        self.runid              = None
        self.polygon            = None
        self.make_flood_map     = False
        self.make_wave_map      = False
        self.make_sedero_map    = False
        self.sa_correction      = None
        self.ssa_correction     = None
        self.wave               = False
        self.mhhw               = 0.0
        self.cluster            = None
        self.boundary_twl_treshold = 999.0
        self.peak_boundary_twl     = None
        self.peak_boundary_time    = None
        self.zb_deshoal         = None

    def read_generic(self):
        """Read model attributes from xml file.

        See Also
        --------
        cosmos.cosmos_scenario
        cht.misc.xmlkit

        """
        try:
            xml_obj = xml.xml2obj(self.file_name)
        except:
            print("Error reading " + self.file_name + " !")
        
        self.long_name = xml_obj.longname[0].value
        self.type      = xml_obj.type[0].value.lower()
        self.runid     = xml_obj.runid[0].value
                
        if hasattr(xml_obj, "flownested"):
            if not xml_obj.flownested[0].value == "none":
#                self.flow_nested = True
                self.flow_nested_name = xml_obj.flownested[0].value
        if hasattr(xml_obj, "wavenested"):
            if not xml_obj.wavenested[0].value == "none":
#                self.wave_nested = True
                self.wave_nested_name = xml_obj.wavenested[0].value
        if hasattr(xml_obj, "bwnested"):
            if not xml_obj.bwnested[0].value == "none":
#                self.wave_nested = True
                self.bw_nested_name = xml_obj.bwnested[0].value
        coordsys     = xml_obj.coordsys[0].value
        self.crs = CRS(coordsys)        
        if hasattr(xml_obj, "xlim1") and hasattr(xml_obj, "xlim2") and hasattr(xml_obj, "ylim1")  and hasattr(xml_obj, "ylim2"):
            self.xlim = [xml_obj.xlim1[0].value, xml_obj.xlim2[0].value]
            self.ylim = [xml_obj.ylim1[0].value, xml_obj.ylim2[0].value]
        if hasattr(xml_obj, "flowspinup"):
            self.flow_spinup_time = xml_obj.flowspinup[0].value
        if hasattr(xml_obj, "wavespinup"):
            self.wave_spinup_time = xml_obj.wavespinup[0].value
        if hasattr(xml_obj, "vertical_reference_level_name"):
            self.vertical_reference_level_name = xml_obj.vertical_reference_level_name[0].value
        if hasattr(xml_obj, "vertical_reference_level_difference_with_msl"):
            self.vertical_reference_level_difference_with_msl = xml_obj.vertical_reference_level_difference_with_msl[0].value
        if hasattr(xml_obj, "boundary_water_level_correction"):
            self.boundary_water_level_correction = xml_obj.boundary_water_level_correction[0].value
        if hasattr(xml_obj, "make_flood_map"):
            if xml_obj.make_flood_map[0].value[0].lower() == "y":
                self.make_flood_map = True
        if hasattr(xml_obj, "make_wave_map"):
            if xml_obj.make_wave_map[0].value[0].lower() == "y":
                self.make_wave_map = True
        if hasattr(xml_obj, "make_sedero_map"):
            if xml_obj.make_sedero_map[0].value[0].lower() == "y":
                self.make_sedero_map = True
        if hasattr(xml_obj, "sa_correction"):
            self.sa_correction = xml_obj.sa_correction[0].value
        if hasattr(xml_obj, "ssa_correction"):
            self.ssa_correction = xml_obj.ssa_correction[0].value
        if hasattr(xml_obj, "wave"):
            if xml_obj.wave[0].value[0].lower() == "y":
                self.wave = True
        if hasattr(xml_obj, "cluster"):
            self.cluster = xml_obj.cluster[0].value[0].lower()
        if hasattr(xml_obj, "boundary_twl_treshold"):
            self.boundary_twl_treshold = xml_obj.boundary_twl_treshold[0].value
            
                
        # Read polygon around model
        polygon_file  = os.path.join(self.path, "misc", self.name + ".txt")
        if os.path.exists(polygon_file):
            df = pd.read_csv(polygon_file, index_col=False, header=None,
                 delim_whitespace=True, names=['x', 'y'])
            xy = df.to_numpy()
            self.polygon = path.Path(xy)
            if not self.xlim:
                self.xlim = [self.polygon.vertices.min(axis=0)[0],
                             self.polygon.vertices.max(axis=0)[0]]
                self.ylim = [self.polygon.vertices.min(axis=0)[1],
                             self.polygon.vertices.max(axis=0)[1]]
           
        # Stations
        if hasattr(xml_obj, "station"):

            for istat in range(len(xml_obj.station)):
                
                # Find matching stations from complete stations list

                name = xml_obj.station[istat].value
                self.add_stations(name)
                
        
    def prepare(self):
        """Set model paths (input, output, figures, restart, job).

        See Also
        --------
        cosmos.cosmos_main_loop

        """        
        # First model and restart folders if necessary

        cycle_path      = cosmos.scenario.cycle_path
        restart_path    = cosmos.scenario.restart_path
        timeseries_path = cosmos.scenario.cycle_timeseries_path
        region          = self.region
        tp              = self.type
        name            = self.name

        # Path with model results in cycle
        self.cycle_path = os.path.join(cycle_path,
                                       "models", region, tp, name)
        self.cycle_input_path = os.path.join(cycle_path,
                                             "models", region, tp, name, "input")
        self.cycle_output_path = os.path.join(cycle_path,
                                              "models", region, tp, name, "output")
        self.cycle_figures_path = os.path.join(cycle_path,
                                              "models", region, tp, name, "figures")
        self.cycle_post_path = os.path.join(timeseries_path,
                                            region, tp, name)
        
        # Restart paths
        self.restart_flow_path = os.path.join(restart_path,
                                              region, tp, name, "flow")
        self.restart_wave_path = os.path.join(restart_path,
                                              region, tp, name, "wave")

        # Model folder in the jobs folder
        self.job_path = os.path.join(cosmos.config.job_path,
                                     cosmos.scenario.name,
                                     self.name)        


        # # Should do this later on
        # fo.mkdir(self.cycle_path)
        # fo.mkdir(self.cycle_input_path)
        # fo.mkdir(self.cycle_output_path)
        # fo.mkdir(self.cycle_figures_path)
        # fo.mkdir(self.cycle_post_path)
        # fo.mkdir(self.restart_flow_path)
        # fo.mkdir(self.restart_wave_path)

#         fo.mkdir(path)

#         self.restart_path = os.path.join(path, "restart")        
#         fo.mkdir(self.restart_path)
#         fo.mkdir(os.path.join(self.restart_path, "flow"))
#         fo.mkdir(os.path.join(self.restart_path, "wave"))

# #        self.archive_path = os.path.join(path,
# #                                         "archive")        
#         fo.mkdir(self.archive_path)

#         self.cycle_path = os.path.join(self.archive_path,
#                                        cosmos.cycle_string)        
#         fo.mkdir(self.cycle_path)

#         fo.mkdir(os.path.join(self.cycle_path, "input"))
#         fo.mkdir(os.path.join(self.cycle_path, "output"))
#         fo.mkdir(os.path.join(self.cycle_path, "figures"))
#         fo.mkdir(os.path.join(self.cycle_path, "post"))

        self.ensemble_path = os.path.join(cycle_path, "ensemble")
        
        # Make scenario, restart, 
# tmpdir=hm.tempDir;
# jobdir=hm.jobDir;

# %% Clear temp directory
# lst=dir(tmpdir);
# for i=1:length(lst)
#     if isdir([tmpdir lst(i).name])
#         switch lst(i).name
#             case{'.','..'}
#             otherwise
#                 [success,message,messageid]=rmdir([tmpdir lst(i).name],'s');
#         end
#     end
# end
# try
#     delete([tmpdir '*']);
# end
        # Prepare job folder and copy all input to that folder
        

        # # Delete existing job folder
        # fo.rmdir(job_path)

        # # Make new job folder
        # fo.mkdir(job_path)
        
        # # Copy all input files to job folder
        # src = os.path.join(self.path, "input", "*")
        # fo.copy_file(src, job_path)
                
#        self.job_path = job_path      

    def submit_job(self):

        if cosmos.scenario.track_ensemble and self.ensemble:
            
            # Make run batch file
            fid = open("tmp.bat", "w")
            fid.write(self.job_path[0:2] + "\n")     

            for member_name in cosmos.scenario.member_names:
            
                # Job path for this ensemble member
                pth = self.job_path + "_" + member_name      
                fid.write("cd " + pth + "\n")
                fid.write("call run.bat\n")

            fid.write("cd " + self.job_path + "\n")
            fid.write("call run.bat\n")
            fid.write("exit\n")

            fid.close()

        else:

            # Make run batch file
            cosmos.log("Writing tmp.bat in " + os.getcwd() + " ...")
            fid = open("tmp.bat", "w")
            fid.write(self.job_path[0:2] + "\n")
            fid.write("cd " + self.job_path + "\n")
            fid.write("call run.bat\n")
            fid.write("exit\n")
            fid.close()

        os.system('start tmp.bat')
#        os.remove('tmp.bat')

    def get_all_nested_models(self, tp, all_nested_models=None):
        # def get_all_nested_models(self, tp, all_nested_models=[]):
        # don't define empty list as default ! (https://nikos7am.com/posts/mutable-default-arguments/)
        # Return a list of all models nested in this model

        if all_nested_models is None:
            all_nested_models = []        
        
        if tp == "flow":
            for mdl in self.nested_flow_models:
                all_nested_models.append(mdl)
                if mdl.nested_flow_models:
                    all_nested_models = mdl.get_all_nested_models("flow",
                                        all_nested_models=all_nested_models)
        
        if tp == "wave":
            for mdl in self.nested_wave_models:
                all_nested_models.append(mdl)
                if mdl.nested_wave_models:
                    all_nested_models = mdl.get_all_nested_models("wave",
                                        all_nested_models=all_nested_models)
        
        return all_nested_models
        
    def add_stations(self, name):

        wgs84 = CRS.from_epsg(4326)
        transformer = Transformer.from_crs(wgs84, self.crs, always_xy=True)
        
        if name[-3:].lower() == "xml":

            # Get all stations in file
            stations = cosmos.stations.find_by_file(name)

            for st in stations:

                station = copy.copy(st)
                station.longitude_model = station.longitude
                station.latitude_model  = station.latitude
                
                x, y = transformer.transform(station.longitude_model,
                                             station.latitude_model)
                station.x = x
                station.y = y
                
                # Check whether this station lies with model domain
                
                if self.polygon:                            
                    if not self.polygon.contains_points([(x, y)])[0]:
                        # On to the next station
                        continue

                self.station.append(station)
                                        
        else:

            station = copy.copy(cosmos.stations.find_by_name(name))

            station.longitude_model = station.longitude
            station.latitude_model  = station.latitude
            
            x, y = transformer.transform(station.longitude_model,
                                         station.latitude_model)
            station.x = x
            station.y = y

            self.station.append(station)
            
    def get_peak_boundary_conditions(self):
        
            # Water level boundary conditions

            # Get boundary conditions from overall model (Nesting 2)
#            output_path = os.path.join(self.flow_nested.cycle_path, "output")   
            zcor = self.boundary_water_level_correction - self.vertical_reference_level_difference_with_msl                    

            if self.type == "xbeach":
                self.domain.tref  = self.flow_start_time
                self.domain.tstop = self.flow_stop_time

            z_max = nest2(self.flow_nested.domain,
                          self.domain,
                          output_path=self.flow_nested.cycle_output_path,
                          boundary_water_level_correction=zcor,
                          return_maximum=True)
            t = z_max.index
            z = z_max.values

            # Wave boundary conditions
            if self.wave_nested:
    
                # Get boundary conditions from overall model (Nesting 2)
#                output_path = os.path.join(self.wave_nested.cycle_path, "output")                                   
                hm0_max = nest2(self.wave_nested.domain,
                                self.domain,
                                output_path=self.wave_nested.cycle_output_path,
                                option="timeseries",
                                return_maximum=True)

                # Interpolate to flow boundary times
                flow_secs = z_max.index.values.astype(float)
                wave_secs = hm0_max.index.values.astype(float)
                f = interpolate.interp1d(wave_secs, hm0_max.values)
                hm0 = f(flow_secs)
                hm0 = np.nan_to_num(hm0)
                            
            else:
                hm0 = np.zeros(np.size(z))

            # Estimate total water level above MHHW with tide + surge + 0.2*Hm0
            twl = z + cluster[self.cluster].hm0fac*hm0 - self.mhhw 
            
            # Index of peak
            imax = np.argmax(twl)
            
            self.peak_boundary_twl  = z[imax]
            self.peak_boundary_time = t[imax].to_pydatetime()
            