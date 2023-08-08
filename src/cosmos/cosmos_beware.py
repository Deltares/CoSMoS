# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:02:04 2021

@author: roelvink
"""

import os
import pandas as pd
import numpy as np
#from pyproj import CRS
#from pyproj import Transformer
import shutil

from cht.beware.beware import BEWARE
import cht.misc.fileops as fo
from cht.misc.deltares_ini import IniStruct
from cht.tide.tide_predict import predict
from cht.misc.misc_tools import findreplace

from .cosmos import cosmos
from .cosmos_model import Model
from .cosmos_tiling import make_flood_map_tiles

import cht.nesting.nesting as nesting

class CoSMoS_BEWARE(Model):
    """Cosmos class for BEWARE model.

    BEWARE is a meta-model based on XBeach for predicting nearshore wave heights and total water levels at reef-lined coasts.

    This cosmos class reads BEWARE model data, pre-processes, moves and post-processes BEWARE models.

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
        """Read BEWARE specific model attributes.

        See Also
        ----------
        cht.beware.beware
        """        
        # Read in the BEWARE model

        # Now read in the domain data
        # input_file  = os.path.join(self.path, "input", "profile_characteristics.mat")
        input_file  = os.path.join(self.path, "input", "beware.inp")
        self.domain = BEWARE(input_file)
        
        self.domain.crs   = self.crs
        self.domain.type  = self.type
        self.domain.name  = self.name
        self.domain.runid = self.runid

    def pre_process(self):
        """Preprocess BEWARE model.
        
        - Extract and write wave and water level conditions.
        - Write input file. 
        - Optional: make ensemble of models.

        See Also
        ----------
        cht.nesting.nest2 
        """   
        
        # Set path temporarily to job path
        pth = self.domain.path
        self.domain.path = self.job_path
        self.domain.input.tref    = cosmos.scenario.ref_date
        self.domain.input.tstart  = self.flow_start_time
        self.domain.input.tstop   = self.flow_stop_time
        
        # Boundary conditions        
        if self.flow_nested:
            # Get boundary conditions from overall model (Nesting 2)

            # Correct boundary water levels. Assuming that output from overall
            # model is in MSL !!!
            zcor = self.boundary_water_level_correction - self.vertical_reference_level_difference_with_msl       

            self.domain.input.bzsfile = 'beware.bzs'
            # Get boundary conditions from overall model (Nesting 2)
            if self.ensemble:
                # Loop through ensemble members
                for iens in range(cosmos.scenario.track_ensemble_nr_realizations):
                    name = cosmos.scenario.ensemble_names[iens]
                    nesting.nest2(self.flow_nested.domain,
                          self.domain,
                          output_path=os.path.join(self.flow_nested.cycle_output_path, name),
                          boundary_water_level_correction=zcor,
                          option="flow",
                          bc_file=os.path.join(self.job_path, name, self.domain.input.bzsfile))

            else:
                nesting.nest2(self.flow_nested.domain,
                    self.domain,
                    output_path=self.flow_nested.cycle_output_path,
                    boundary_water_level_correction=zcor,
                    option = 'flow',
                    bc_file=os.path.join(self.job_path, self.domain.input.bzsfile))

            self.domain.input.bndfile = 'beware.bnd'
            self.domain.write_flow_boundary_points()


        if self.wave and self.wave_nested:
            self.domain.input.btpfile = 'beware.btp'
            self.domain.input.bhsfile = 'beware.bhs'
            self.domain.input.bwvfile = 'beware.bwv'
            
            # Get boundary conditions from overall model (Nesting 2)
            if self.ensemble:
                # Loop through ensemble members
                for iens in range(cosmos.scenario.track_ensemble_nr_realizations):
                    name = cosmos.scenario.ensemble_names[iens]
                    nesting.nest2(self.wave_nested.domain,
                        self.domain,
                        output_path=os.path.join(self.wave_nested.cycle_output_path, name),
                        option= 'wave',
                        bc_path =  os.path.join(self.job_path, name))

            else:
                nesting.nest2(self.wave_nested.domain,
                    self.domain,
                    output_path=self.wave_nested.cycle_output_path,
                    option= 'wave',
                    bc_path = self.job_path)

            self.domain.write_wave_boundary_points()
        
        # Now write input file (sfincs.inp)
        self.domain.write_input_file()

        # Make run batch file
        src = os.path.join(cosmos.config.executables.beware_path, "run_bw.bas")
        batch_file = os.path.join(self.job_path, "run.bat")
        shutil.copyfile(src, batch_file)
        findreplace(batch_file, "EXEPATHKEY", cosmos.config.executables.beware_path)

        # Set the path back to the one in cosmos\models\etc.
        self.domain.path = pth           

        
    def move(self):
        """Move BEWARE model input and output files.
        """        
        # Move files from job folder to archive folder
        
        # First clear archive folder      
        
        job_path    = self.job_path         
        output_path = self.cycle_output_path
        input_path  = self.cycle_input_path
                      
        if self.ensemble:
            # And now for the ensemble members
            # Only output
            for member_name in cosmos.scenario.ensemble_names:                
                pth0 = os.path.join(job_path, member_name)
                pth1 = os.path.join(output_path, member_name)
                fo.mkdir(pth1)
                fo.move_file(os.path.join(pth0, "beware_his.nc"), pth1)
        else:
            fo.move_file(os.path.join(job_path, "beware_his.nc"), output_path)

        # Input
        fo.move_file(os.path.join(job_path, "*.*"), input_path)

    def post_process(self):
        """Post-process BEWARE output: generate (probabilistic) runup timeseries.
        
        See Also
        ----------
        cht.misc.prob_maps
        """        
        # Post-processing occurs in cosmos_webviewer.py
        import numpy as np
        import cht.misc.prob_maps as pm
        import cht.misc.misc_tools
        
        output_path = self.cycle_output_path
        # post_path   = self.cycle_post_path
        post_path =  os.path.join(cosmos.config.path.webviewer, 
                            cosmos.config.webviewer.name,
                            "data",
                            cosmos.scenario.name)

        if self.ensemble:
            
            # Make probabilistic runup timeseries
            file_list = []
            for member in cosmos.scenario.ensemble_names:
                file_list.append(os.path.join(output_path, member, "beware_his.nc"))
            prcs= [5, 50, 95]
            vars= ["R2", "R2_setup", "WL"]
            output_file_name = os.path.join(output_path, "beware_his_ensemble.nc")
            pm.prob_floodmaps(file_list=file_list, variables=vars, prcs=prcs, delete = False, output_file_name=output_file_name)

            # Write timeseries
            self.domain.read_data(os.path.join(output_path, "beware_his_ensemble.nc"), prcs= prcs)       

            for ip in range(len(self.domain.filename)):
                
                d= {'WL': self.domain.WL[ip,:],'Setup': self.domain.R2_setup[ip,:], 'Swash': self.domain.swash[ip,:], 'Runup': self.domain.R2[ip,:],
                        'Setup_5': self.domain.R2_setup_prc["5"][ip,:],'Setup_50': self.domain.R2_setup_prc["50"][ip,:],'Setup_95': self.domain.R2_setup_prc["95"][ip,:],
                        'Runup_5': self.domain.R2_prc["5"][ip,:],'Runup_50': self.domain.R2_prc["50"][ip,:],'Runup_95': self.domain.R2_prc["95"][ip,:],}    

                v= pd.DataFrame(data=d, index =  pd.date_range(self.domain.input.tstart, periods=len(self.domain.swash[ip,:]), freq= '0.5H'))
                local_file_path = os.path.join(post_path,  
                                                "timeseries",
                                                     "extreme_runup_height." + self.name + "." + str(self.domain.filename[ip]) + ".csv.js")
                                                     
                s= v.to_csv(path_or_buf=None,
                                date_format='%Y-%m-%dT%H:%M:%S',
                                float_format='%.3f',
                                header= False, index_label= 'datetime') 
                        
                cht.misc.misc_tools.write_csv_js(local_file_path, s, "var csv = `date_time,wl,setup,swash,runup, setup_5, setup_50, setup_95, runup_5, runup_50, runup_95")

        else:
            self.domain.read_data(os.path.join(output_path, "beware_his.nc"))       
            for ip in range(len(self.domain.filename)):
                d= {'WL': self.domain.WL[ip,:],'Setup': self.domain.R2_setup[ip,:], 'Swash': self.domain.swash[ip,:], 'Runup': self.domain.R2[ip,:]}       
        
                v= pd.DataFrame(data=d, index =  pd.date_range(self.domain.input.tstart, periods=len(self.domain.swash[ip,:]), freq= '0.5H'))
                local_file_path = os.path.join(post_path,  
                                                "timeseries",
                                                     "extreme_runup_height." + self.name + "." + str(self.domain.filename[ip]) + ".csv.js")
                s= v.to_csv(path_or_buf=None,
                                date_format='%Y-%m-%dT%H:%M:%S',
                                float_format='%.3f',
                                header= False, index_label= 'datetime') 
                cht.misc.misc_tools.write_csv_js(local_file_path, s, "var csv = `date_time,wl,setup,swash,runup")
       
        # output_path = self.cycle_output_path
        # post_path   = self.cycle_post_path

        # self.domain.read_data(os.path.join(output_path, "BW_output.nc"))
        # self.domain.write_to_geojson(output_path, cosmos.scenario.name)
        # # Time series
        # self.domain.write_to_csv(post_path, cosmos.scenario.name)
