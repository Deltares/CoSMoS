# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:02:04 2021

@author: ormondt
"""

import os
import pandas as pd
import numpy as np
from pyproj import CRS
from pyproj import Transformer

from .cosmos_main import cosmos
from .cosmos_model import Model
import cht.misc.xmlkit as xml
from cht.delft3dfm.delft3dfm import Delft3DFM
import cht.misc.fileops as fo
from cht.nesting.nesting import nest1
from cht.nesting.nesting import nest2
import cosmos.cosmos_meteo as meteo

from cht.misc.misc_tools import findreplace

class CoSMoS_Delft3DFM(Model):
    """Cosmos class for Delft3d FM model.

    Delft3D FM is a hydrodynamic and morphodynamic numerical model used for simulating and predicting water flow, sediment transport, 
    and morphological changes in rivers, estuaries, coasts, and oceans (see also https://oss.deltares.nl/web/delft3dfm).

    This cosmos class reads Delft3D FM model data, pre-processes, moves and post-processes Delft3D FM models.

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
        """Read Delft3D FM specific model attributes.

        See Also
        ----------
        cht.delft3dfm.delft3dfm

        """   
        # First set some defaults
#        self.flow_spinup_time = 0.0
        
#        xml_obj = xml.xml2obj(self.file_name)        
#        if hasattr(xml_obj, "flowspinup"):
#            self.flow_spinup_time = float(xml_obj.flowspinup[0].value)
                        
        # Now read in the domain data
#        if self.wave:
        self.input_path_flow = os.path.join(self.path, "input", "flow")
        self.input_path_wave = os.path.join(self.path, "input", "wave")
#        else:
#            self.input_path_flow = os.path.join(self.path, "input")
#            self.input_path_wave = None
                
        input_file  = os.path.join(self.input_path_flow, self.runid + ".mdu")
        self.domain = Delft3DFM(input_file, crs=self.crs)

        # Copy some attributes to the model domain (needed for nesting)
        self.domain.crs   = self.crs
        self.domain.type  = self.type
        self.domain.name  = self.name
        self.domain.runid = self.runid        
        
    def pre_process(self):
        """Preprocess Delft3D FM model.
        - Extract and write wave and water level conditions.
        - Write input file. 
        - Write meteo forcing.
        - Add observation points for nested models and observation stations.

        See Also
        ----------
        cht.nesting.nest2
        
        """   
        # Set path temporarily to job path
#        pth = self.domain.path
        
#        if self.wave:
#        self.domain.path = os.path.join(self.domain.path, "fm")
#        else:
#            self.domain.path = self.job_path
        
        job_path_flow = os.path.join(self.job_path, "flow")
        job_path_wave = os.path.join(self.job_path, "wave")
        
        # Start and stop times
        self.domain.input.refdate = cosmos.scenario.ref_date
        self.domain.input.tstart  = self.flow_start_time
        self.domain.input.tstop   = self.flow_stop_time
        
        # Change refdate in mdw file
        if self.wave:
            tstr = cosmos.scenario.ref_date.strftime("%Y-%m-%d")
            mdw_file = os.path.join(job_path_wave, "wave.mdw")
            findreplace(mdw_file, "REFDATEKEY", tstr)
            
            t0 = (self.domain.input.tstart - self.domain.input.refdate).total_seconds()
            t1 = (self.domain.input.tstop  - self.domain.input.refdate).total_seconds()
            dt = 1800.0
#            tstr = str(0.0) + " " + str(dt) + " " + str(t1 - t0)
            tstr = str(0.0) + " " + str(dt) + " " + str(t1)
            dmr_file = os.path.join(self.job_path, "dimr_config.xml")
            findreplace(dmr_file, "TIMEKEY", tstr)
        
        # Make sure model starts and stops automatically
        self.domain.input.autostart = 2
        # Turn off pressure correction at open boundaries
        if self.flow_nested:
            self.domain.input.pavbnd = -999.0

        # Boundary conditions        
        if self.flow_nested:

            # Get boundary conditions from overall model (Nesting 2)
#            output_path = os.path.join(self.flow_nested.cycle_path, "output")    
            nest2(self.flow_nested.domain,
                  self.domain,
                  output_path=self.flow_nested.cycle_output_path)

        if self.wave_nested:
            # TODO
            pass
                    
        # Meteo forcing
        if self.meteo_wind or self.meteo_atmospheric_pressure or self.meteo_precipitation:
                    
            meteo.write_meteo_input_files(self,
                                          "delft3dfm",
                                          self.domain.input.refdate,
                                          path=job_path_flow)
            
            if self.meteo_wind:                
                self.domain.meteo.amu_file = "delft3dfm.amu"
                self.domain.meteo.amv_file = "delft3dfm.amv"
    
            if self.meteo_atmospheric_pressure:
                self.domain.meteo.amp_file = "delft3dfm.amp"
                            
            if self.meteo_precipitation:                
                self.domain.meteo.ampr_file = "delft3dfm.ampr"
                
            # if self.meteo_spiderweb:
            #     self.domain.input.spwfile = self.meteo_spiderweb
            #     self.domain.input.baro    = 1
            #     src = os.path.join("d:\\cosmos\\externalforcing\\meteo\\",
            #                        "spiderwebs",
            #                        self.meteo_spiderweb)
            #     fo.copy_file(src, self.job_path)
            if not self.domain.input.extforcefile:
                self.domain.input.extforcefile = "meteo.ext"
                self.domain.write_ext_meteo()
            
        # Make observation points
        for station in self.station:
            self.domain.add_observation_point(station.x,
                                              station.y,
                                              station.name)
                
        # Add observation points for nested models (Nesting 1)
        if self.nested_flow_models:

            if not self.domain.input.obsfile:
                self.domain.input.obsfile = "dflowfm.xyn"

            for nested_model in self.nested_flow_models:
                nest1(self.domain, nested_model.domain)

        if self.nested_wave_models:
            pass

        # Add other observation stations 
        if self.nested_flow_models or len(self.station)>0:
            if not self.domain.input.obsfile:
                self.domain.input.obsfile = self.runid + ".xyn"
            self.domain.write_observation_points(path=job_path_flow)       
        if self.nested_wave_models:
            self.domain.write_observation_points(path=job_path_wave)    
            findreplace(mdw_file, "OBSFILEKEY", self.domain.input.obsfile)    

        # Make restart file
        trstsec = self.domain.input.tstop.replace(tzinfo=None) - self.domain.input.refdate            
        if self.meteo_subset:
            if self.meteo_subset.last_analysis_time:
                trstsec = self.meteo_subset.last_analysis_time.replace(tzinfo=None) - self.domain.input.refdate
        self.domain.input.rstinterval = trstsec.total_seconds()
        
        # # Get restart file from previous cycle
        # if self.flow_restart_file:
        #     src = os.path.join(self.restart_path, "flow",
        #                        self.flow_restart_file)
        #     dst = os.path.join(self.job_path,
        #                        "dflowfm.rst")
        #     fo.copy_file(src, dst)
        #     self.domain.input.rstfile = "dflowfm.rst"
        #     self.domain.input.tspinup = 0.0

        
        # Now write input file
        mdufile = os.path.join(job_path_flow, self.runid + ".mdu")
        self.domain.write_input_file(input_file=mdufile)
        

        batch_file = os.path.join(self.job_path, "run.bat")
        fid = open(batch_file, "w")            
        fid.write("@ echo off\n")
        fid.write("DATE /T > running.txt\n")
        exe_path = os.path.join("call " + cosmos.config.delft3dfm_exe_path,
                                 "x64\\dimr\\scripts\\run_dimr.bat dimr_config.xml\n")
        fid.write(exe_path)
        fid.write("move running.txt finished.txt\n")
        fid.write("exit\n")
        fid.close()
            
  
        # Set the path back
#        self.domain.path = pth

    def move(self):
        """Move Delft3D FM model input, output, and restart files.
        """     
        # Move files from job folder to archive folder
        
        # First clear archive folder      
        
        job_path    = self.job_path

        # Delete finished.txt file
        fo.delete_file(os.path.join(job_path, "finished.txt"))
        
        output_path = self.cycle_output_path
        input_path  = self.cycle_input_path

        # FLOW
                                   
        # Restart files 
        # First rename the restart files
        joboutpath = os.path.join(job_path, "flow", "output")
        flist = fo.list_files(os.path.join(joboutpath, "*_rst.nc"))
        for rstfile0 in flist:
            dstr = rstfile0[-22:-14]
            tstr = rstfile0[-13:-7]
            rstfile1 = "delft3dfm." + dstr + "." + tstr + ".rst"            
            fo.move_file(rstfile0,
                         os.path.join(self.restart_flow_path, rstfile1))
        
        # Output        
        fo.move_file(os.path.join(joboutpath, "*.nc"), output_path)
        
#        fo.move_file(os.path.join(job_path, "sfincs.rst"), input_path)


        # Input
        # Delete net file (this is typically quite big)
        fo.delete_file(os.path.join(job_path, "flow", self.domain.input.netfile))
        fo.move_file(os.path.join(job_path, "flow", "*.*"), input_path)
        
        # WAVE

        # Restart files 
        # First rename the restart files
        joboutpath = os.path.join(job_path, "wave")
        # flist = fo.list_files(os.path.join(joboutpath, "*_rst.nc"))
        # for rstfile0 in flist:
        #     dstr = rstfile0[-22:-14]
        #     tstr = rstfile0[-13:-7]
        #     rstfile1 = "delft3dfm." + dstr + "." + tstr + ".rst"            
        #     fo.move_file(rstfile0,
        #                  os.path.join(self.restart_path, "flow", rstfile1))
        
        # Output        
        fo.move_file(os.path.join(joboutpath, "wav*.nc"), output_path)
        fo.delete_file(os.path.join(joboutpath, "*.nc"))
        fo.delete_file(os.path.join(joboutpath, "wavm-wave.d*"))

        # Input
        fo.move_file(os.path.join(joboutpath, "*.*"), input_path)

    def post_process(self):
        """Post-process Delft3D FM output: generate wave and water level timeseries.        
        """         
        # Extract water levels

        output_path = self.cycle_output_path
        post_path   = self.cycle_post_path

        hisfile = os.path.join(output_path, self.runid + "_his.nc")
        
        if self.station:

            cosmos.log("Extracting time series from model " + self.name)    

            v = self.domain.read_timeseries_output(file_name=hisfile)
            for station in self.station:
                vv=v[station.name]
                vv.index.name='date_time'
                vv.name='wl'
                vv = vv + station.water_level_correction
                file_name = os.path.join(post_path,
                                         "waterlevel." + station.name + ".csv")
                vv.to_csv(file_name,
                          date_format='%Y-%m-%dT%H:%M:%S',
                          float_format='%.3f')

        # Extract waves
        if self.wave:
            
            if self.station:

                cosmos.log("Extracting wave time series from model " + self.name)    
                wavefile = [os.path.join(output_path, "wavh-wave-nest.nc"), os.path.join(output_path, "wavh-wave-Entire_swn.nc")]
                v = self.domain.read_timeseries_output(file_name=hisfile, file_name_wave = wavefile)
                for station in self.station:
                    vv=v[station.name]
                    vv.index.name='date_time'
                    file_name = os.path.join(post_path,
                                            "waves." + station.name + ".csv")
                    vv.to_csv(file_name,
                            date_format='%Y-%m-%dT%H:%M:%S',
                            float_format='%.3f')        
