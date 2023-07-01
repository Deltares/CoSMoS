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

from cht.nesting.nest2 import nest2

class CoSMoS_BEWARE(Model):
    """Cosmos class for BEWARE model.

    BEWARE is a meta-model based on XBeach for predicting nearshore wave heights and total water levels at reef-lined coasts.

    Parameters
    ----------
    Model : class
        Generic cosmos model attributes

    See Also
    ----------
    cosmos.cosmos_model_loop: invokes current class
    cosmos.cosmos_model: function call
    """    
    def read_model_specific(self):
        """Read BEWARE specific model attributes

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
        """Preprocess BEWARE model: write wave and water level conditions, input file, run.bat

        See Also
        ----------
        cht.nesting.nest2
        
        """   
        # First generate input that is identical for all members
        
        # Set path temporarily to job path
        pth = self.domain.path
        self.domain.path = self.job_path
        self.domain.input.tref    = cosmos.scenario.ref_date
        self.domain.input.tstart  = self.flow_start_time
        self.domain.input.tstop   = self.flow_stop_time
        
        # Boundary conditions        
        if self.flow_nested:
            # Get boundary conditions from overall model (Nesting 2)
#            output_path = os.path.join(self.flow_nested.cycle_path, "output")   
            # output_path = os.path.join(r'p:\11204750-onr-westernpacific\Year2-3\cosmos\version01\cosmos\scenarios\hurricane_michael_coamps_spw\models\northamerica\delft3dfm\delft3dfm_gom\archive\20181009_00z\\',
            #                             "output")   

            # Correct boundary water levels. Assuming that output from overall
            # model is in MSL !!!
            zcor = self.boundary_water_level_correction - self.vertical_reference_level_difference_with_msl       

            nest2(self.flow_nested.domain,
                  self.domain,
                  output_path=self.flow_nested.cycle_output_path,
                  option = 'flow',
                  boundary_water_level_correction=zcor)
            self.domain.input.bzsfile = 'beware.bzs'
            self.domain.write_flow_boundary_conditions()
            self.domain.input.bndfile = 'beware.bnd'
            self.domain.write_flow_boundary_points()


        if self.wave and self.wave_nested:
            
            # Get wave boundary conditions from overall model (Nesting 2)
#            output_path = os.path.join(self.wave_nested.cycle_path, "output")   
            # output_path = os.path.join(r'p:\11204750-onr-westernpacific\Year2-3\cosmos\version01\cosmos\scenarios\hurricane_michael_coamps_spw\models\northamerica\delft3dfm\delft3dfm_gom\archive\20181009_00z\\',
            #                             "output")   

            nest2(self.wave_nested.domain,
                  self.domain,
                  output_path=self.wave_nested.cycle_output_path,
                  option= 'wave')

            self.domain.input.btpfile = 'beware.btp'
            self.domain.input.bhsfile = 'beware.bhs'
            self.domain.input.bwvfile = 'beware.bwv'
            self.domain.write_wave_boundary_conditions()
            self.domain.write_wave_boundary_points()
        
        # Now write input file (sfincs.inp)
        self.domain.write_input_file()

        # Make inp file
        #inp_file = os.path.join(self.job_path, "beware.inp")
        #with open(inp_file,'w') as fid:
#       #     fid.write(f'folder   = {self.job_path} \n')
        #    fid.write(f'tref     = {self.domain.input.tref.strftime("%Y%m%d %H%M%S")} \n')
        #    fid.write(f'tstart   = {self.domain.input.tstart.strftime("%Y%m%d %H%M%S")} \n')
        #    fid.write(f'tstop    = {self.domain.input.tstop.strftime("%Y%m%d %H%M%S")} \n')
        #    fid.write(f'dT       = {self.domain.input.dT} \n')
        #    fid.write(f'runup    = {self.domain.input.runup} \n')
        #    fid.write(f'flooding = {self.domain.input.flooding} \n')
        #fid.close()

        # Make run batch file
        src = os.path.join(cosmos.config.beware_exe_path, "run_bw.bas")
        batch_file = os.path.join(self.job_path, "run.bat")

        shutil.copyfile(src, batch_file)
        # findreplace(batch_file, "DISKKEY", 'P')
        findreplace(batch_file, "EXEPATHKEY", cosmos.config.beware_exe_path)
#        findreplace(batch_file, "RUNPATHKEY", self.job_path)
#         fid = open(batch_file, "w")
#         fid.write("@ echo off\n")
#         fid.write("DATE /T > running.txt\n")
#         exe_path = os.path.join(cosmos.config.beware_exe_path, "run_beware.py")
#         fid.write(exe_path + "\n")
# #        fid.write("d:\\checkouts\\SFINCS\\branches\\subgrid_openacc_12_wavemaker\\sfincs\\x64\\Release\\sfincs.exe\n")
#         fid.write("move " + os.path.join(cosmos.config.beware_exe_path, "beware.inp") + " " +  os.path.join(self.domain.path, "beware.inp") + " \n")
#         fid.write("move running.txt finished.txt\n")
# #        fid.write("exit\n")
#         fid.close()

        if cosmos.scenario.track_ensemble and self.ensemble:
            profsfile = self.domain.input.profsfile
            if self.domain.input.r2matchfile is not None:
                r2matchfile = self.domain.input.r2matchfile

            if self.domain.input.flmatchfile is not None:
                flmatchfile = self.domain.input.flmatchfile

            for member_name in cosmos.scenario.member_names:

                # Job path for this ensemble member
                member_path = self.job_path + "_" + member_name
                fo.mkdir(member_path)

                 # Boundary conditions        
                if self.flow_nested:
                    # Get boundary conditions from overall model (Nesting 2)

                    # Correct boundary water levels. Assuming that output from overall
                    # model is in MSL !!!
                    zcor = self.boundary_water_level_correction - self.vertical_reference_level_difference_with_msl       

                    if self.flow_nested.ensemble:
                        if self.flow_nested.type == "sfincs":
                            output_file = "sfincs_his_" + member_name + '.nc'
                    else:
                        output_file= None

                    nest2(self.flow_nested.domain,
                        self.domain,
                        output_path=self.flow_nested.cycle_output_path,
                        output_file= output_file,
                        option = 'flow',
                        boundary_water_level_correction=zcor)
                    self.domain.input.bzsfile = 'beware.bzs'
                    self.domain.write_flow_boundary_conditions(file_name= os.path.join(member_path, self.domain.input.bzsfile))
                    self.domain.input.bndfile = r"..\\" + os.path.basename(self.domain.path) + r"\\beware.bnd"

                if self.wave and self.wave_nested:
        
                    # Get wave boundary conditions from overall model (Nesting 2)
                    if self.flow_nested.ensemble:
                        if self.wave_nested.type == "hurrywave":
                            output_file = "hurrywave_his_" + member_name + '.nc'
                        else:
                            output_file= None

                    nest2(self.wave_nested.domain,
                        self.domain,
                        output_path=self.wave_nested.cycle_output_path,
                        output_file= output_file,
                        option= 'wave')

                    self.domain.input.btpfile = 'beware.btp'
                    self.domain.input.bhsfile = 'beware.bhs'
                    self.domain.write_bhs_file(file_name = os.path.join(member_path, self.domain.input.bhsfile))
                    self.domain.write_btp_file(file_name = os.path.join(member_path, self.domain.input.btpfile))
                    self.domain.input.bwvfile = r"..\\" + os.path.basename(self.domain.path) + r"\\beware.bwv"

                # Copy inp & run.bat files to member folder
                fo.copy_file(os.path.join(self.job_path, 'run.bat'), member_path)
                self.domain.input.profsfile = r"..\\" + os.path.basename(self.domain.path) + r"\\" + profsfile
                if self.domain.input.r2matchfile is not None:
                    self.domain.input.r2matchfile = r"..\\" + os.path.basename(self.domain.path) + r"\\" + r2matchfile
                if self.domain.input.flmatchfile is not None:
                    self.domain.input.flmatchfile = r"..\\" + os.path.basename(self.domain.path) + r"\\" + flmatchfile
                self.domain.write_input_file(input_file= os.path.join(member_path, "beware.inp"))

        # Set the path back to the one in cosmos\models\etc.
        self.domain.path = pth           

        
    def move(self):
        """Move BEWARE model input and output files
        """        
        # Move files from job folder to archive folder
        
        # First clear archive folder      
        
        job_path    = self.job_path         
        output_path = self.cycle_output_path
        input_path  = self.cycle_input_path
        
        # Output        
        fo.move_file(os.path.join(job_path, "*.nc"), output_path)
        
        # Input
        fo.move_file(os.path.join(job_path, "*.*"), input_path)
        
        if cosmos.scenario.track_ensemble and self.ensemble:
            # And now for the ensemble members
            # Only output
            for member_name in cosmos.scenario.member_names:
                pth = self.job_path + "_" + member_name
                if os.path.isfile(os.path.join(pth, "beware_his.nc")):
                    fo.move_file(os.path.join(pth, "beware_his.nc"), os.path.join(self.cycle_output_path, 'beware_his_'+ member_name +'.nc'))

                try:
                    shutil.rmtree(pth)
                except:
                    # Folder was probably open in another application
                    pass

    def post_process(self):
        """Post-process BEWARE output
        
        See Also
        ----------
        cht.misc.prob_maps
        
        """        
        # Post-processing occurs in cosmos_webviewer.py
        import numpy as np
        import cht.misc.prob_maps as pm
        
        output_path = self.cycle_output_path
        post_path   = self.cycle_post_path

        if cosmos.scenario.track_ensemble and self.ensemble:
            
            # Make probabilistic runup timeseries
            file_list= fo.list_files(os.path.join(output_path, "beware_his_*"))
            prcs= [0.05, 0.5, 0.95] #np.concatenate((np.arange(0, 0.9, 0.1), np.arange(0.9, 1, 0.01)))
            vars= ["R2_tot", "R2_set", "WL"]
            output_file_name = os.path.join(output_path, "beware_his_ensemble.nc")
            pm.prob_floodmaps(file_list=file_list, variables=vars, prcs=prcs, delete = False, output_file_name=output_file_name)

       
        # output_path = self.cycle_output_path
        # post_path   = self.cycle_post_path

        # self.domain.read_data(os.path.join(output_path, "BW_output.nc"))
        # self.domain.write_to_geojson(output_path, cosmos.scenario.name)
        # # Time series
        # self.domain.write_to_csv(post_path, cosmos.scenario.name)
