# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:36:35 2021

@author: ormondt
"""
from cosmos.cosmos import cosmos

main_path = r"c:\cosmos_run_folder\run_folder"

# Initialize CoSMoS configuration
cosmos.initialize(main_path,
                  config_file="config.toml")

cosmos.run("hurricane_fiona_coamps", cycle="20220917_00z")
