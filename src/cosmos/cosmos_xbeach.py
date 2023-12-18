# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:02:04 2021

@author: ormondt
"""

import os
import datetime
import toml
import xarray as xr

from .cosmos_main import cosmos
from .cosmos_model import Model
from .cosmos_tiling import make_sedero_tiles
from .cosmos_tiling import make_bedlevel_tiles

import cht.misc.fileops as fo
from cht.xbeach.xbeach import XBeach

class CoSMoS_XBeach(Model):
    """Cosmos class for XBeach model.

    XBeach (XB) is a physics-based nearshore model that solves the horizontal equations for flow, 
    wave propagation, sediment transport, and changes in bathymetry (see also https://xbeach.readthedocs.io/en/latest/).

    This cosmos class reads XBeach model data, pre-processes, moves and post-processes XBeach models.

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
        """Read XBeach specific model attributes.

        See Also
        ----------
        cht.xbeach.xbeach
        """
      
        # Now read in the domain data
        input_file  = os.path.join(self.path, "input", "params.txt")
        self.domain = XBeach(input_file=input_file, get_boundary_coordinates=False)
        # Give names to the boundary points
        for ipnt, pnt in enumerate(self.domain.flow_boundary_point):
            pnt.name = str(ipnt + 1).zfill(4)
        for ipnt, pnt in enumerate(self.domain.wave_boundary_point):
            pnt.name = str(ipnt + 1).zfill(4)
        
        mdl_dict = toml.load(self.file_name)
        if "flow_nesting_points" in mdl_dict:
            flow_nesting_points = mdl_dict["flow_nesting_points"]

            #remove the default found boundary locations based on the tideloc and xbeach routine
            self.domain.flow_boundary_point[len(flow_nesting_points):] = []
            for ipnt, pnt in enumerate(flow_nesting_points):
                self.domain.flow_boundary_point[ipnt].geometry.x = pnt[0]
                self.domain.flow_boundary_point[ipnt].geometry.y = pnt[1]
                #TODO change tideloc in the params as a function of the new boundary points?

        if "wave_nesting_point" in mdl_dict:
            wave_nesting_point = mdl_dict["wave_nesting_point"]
            self.domain.wave_boundary_point[0].geometry.x = wave_nesting_point[0]
            self.domain.wave_boundary_point[0].geometry.y = wave_nesting_point[1]

        if "zb_deshoal" in mdl_dict:
            self.domain.zb_deshoal = mdl_dict["zb_deshoal"]
            
        # Copy some attributes to the model domain (needed for nesting)
        self.domain.crs   = self.crs
        self.domain.type  = self.type
        self.domain.name  = self.name
        self.domain.runid = self.runid
        
        
    def pre_process(self):
        """Preprocess XBeach model.

        - Extract and write water level and wave conditions.
        - Optional: only run XBeach for peak conditions.
        - Write input file. 

        See Also
        ----------
        cht.nesting.nest2
        """
        
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
            pass

        # Boundary conditions        
        if self.wave_nested:
            
            #define whether you want to use jonstable or sp2-files as boundary conditions
            option = "timeseries"
                            
            if option == "sp2":
                self.domain.params["bcfile"] = "sp2list.txt"
                self.domain.params["instat"] = 5
            elif option == "timeseries":
                self.domain.params["bcfile"] = "jonswap.txt"
                self.domain.params["wbctype"] = "jonstable"
                                                                
        # Now write input file (params.txt)
        params_file = os.path.join(self.job_path, "params.txt")
        self.domain.params.tofile(filename=params_file)

        # And now prepare the job files

        # Copy the correct run script to run_job.py
        pth = os.path.dirname(__file__)
        fo.copy_file(os.path.join(pth, "cosmos_run_xbeach.py"), os.path.join(self.job_path, "run_job_2.py"))

        # Write config.yml file to be used in job
        self.write_config_yml()

        if self.ensemble:
            # Write ensemble members to file
            with open(os.path.join(self.job_path, "ensemble_members.txt"), "w") as f:
                for member in cosmos.scenario.ensemble_names:
                    f.write(member + "\n")

        if cosmos.config.cycle.run_mode != "cloud":
            # Make run batch file (only for windows)
            batch_file = os.path.join(self.job_path, "run_xbeach.bat")
            fid = open(batch_file, "w")
            fid.write("@ echo off\n")
            fid.write("DATE /T > running.txt\n")
            fid.write("set xbeachdir=" + cosmos.config.executables.xbeach_path + "\n")
            fid.write('set mpidir="c:\\Program Files\\MPICH2\\bin"\n')
            fid.write("set PATH=%xbeachdir%;%PATH%\n")
            fid.write("set PATH=%mpidir%;%PATH%\n")
            fid.write("mpiexec.exe -n 5 %xbeachdir%\\xbeach.exe\n")
            fid.write("del q_*\n")
            fid.write("del E_*\n")
            fid.write("move running.txt finished.txt\n")
            fid.close()
 
        if cosmos.config.cycle.run_mode == "cloud":
            # Set workflow names
            if self.ensemble:
                self.workflow_name = "xbeach-ensemble-workflow"
            else:
                self.workflow_name = "xbeach-deterministic-workflow"   

        # Set the path back to the one in cosmos\models\etc.
        self.domain.path = pth

    def move(self):
        """Move XBeach model input and output files.
        """   
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
        """Post-process XBeach output: generate sedimentation/erosion maps.        
        """
        
        output_path = self.cycle_output_path
        post_path =  os.path.join(cosmos.config.path.webviewer, 
                            cosmos.config.webviewer.name,
                            "data",
                            cosmos.scenario.name)
        sedero_map_path = os.path.join(post_path,
                                       "sedero")
        zb0_map_path = os.path.join(post_path,
                                       "zb0")  
        zbend_map_path = os.path.join(post_path,
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
            

                
