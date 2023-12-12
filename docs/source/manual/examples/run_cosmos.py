# -*- coding: utf-8 -*-
"""
run_cosmos.py

Created on Mon May 10 14:36:35 2021

@author: ormondt
"""
from cosmos.cosmos import cosmos

main_path = "c:\\cosmos_run_folder\\run_folder"

# Initialize CoSMoS configuration
cosmos.initialize(main_path,
                  config_file="config.toml",
                  make_wave_maps=False,
		  get_meteo = False,
                  ensemble = False,
		  run_mode = "serial")

cosmos.run("hurricane_laura")
