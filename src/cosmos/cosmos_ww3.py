# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:02:04 2021

@author: ormondt
"""
import shutil
import os

from .cosmos_main import cosmos
from .cosmos_model import Model
import cht_utils.xmlkit as xml

class CoSMoS_WW3(Model):
    
    def read_model_specific(self):
        
        # First set some defaults
        self.wave_spinup_time = 0.0
        
        xml_obj = xml.xml2obj(self.file_name)        
        if hasattr(xml_obj, "wavespinup"):
            self.wave_spinup_time = float(xml_obj.wavespinup[0].value)
        

    def move(self):
        
        # Delete everything for now
        job_path    = os.path.join(cosmos.config.job_path,
                                   cosmos.scenario.name,
                                   self.name)
        files = os.listdir(job_path)
        for file_name in files:
            full_file_name = os.path.join(job_path, file_name)
            os.remove(full_file_name)
        try:    
            os.rmdir(job_path)
        except:
            cosmos.log("Could not delete " + job_path)

    def pre_process(self):
        
        job_path    = os.path.join(cosmos.config.job_path,
                                   cosmos.scenario.name,
                                   self.name)
        if not os.path.exists(job_path):
            os.mkdir(job_path)

        # Copy all input files to job folder
        src = os.path.join(self.path, "input")        
        src_files = os.listdir(src)
        for file_name in src_files:
            full_file_name = os.path.join(src, file_name)
            if os.path.isfile(full_file_name):
                shutil.copy(full_file_name, job_path)        
        
    def post_process(self):
        pass
        
    def submit_job(self):
        pass
