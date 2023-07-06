# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:36:35 2021

@author: ormondt
"""
from cosmos.cosmos import cosmos

main_path = "c:\\work\\cosmos\\run_folder"

# Initialize CoSMoS configuration
cosmos.initialize(main_path,
                  config_file="config_mvo.toml",
                  make_wave_maps=False)

cosmos.run("hurricane_laura")
