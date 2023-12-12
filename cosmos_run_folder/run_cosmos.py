# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:36:35 2021

@author: ormondt
"""
from cosmos.cosmos import cosmos

main_path = r"c:\cosmos_run_folder\run_folder"

# Initialize CoSMoS configuration
cosmos.initialize(main_path,
                  config_file="config.toml",
                  make_wave_maps=True,
                  get_meteo = False,
                  ensemble = False)

cosmos.run("hurricane_fiona_coamps")
# cosmos.post_process("hurricane_fiona_coamps", model = ['hurrywave_north_atlantic', 'hurrywave_us_east_coast',])
# cosmos.make_webviewer("hurricane_fiona_coamps")
