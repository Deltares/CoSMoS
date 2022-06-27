# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:36:35 2021

@author: ormondt
"""

from cosmos.cosmos_main import cosmos

main_path = "d:\\cosmos"

scenario_name = "michael_gfs_test02"

cosmos.initialize(main_path)

cosmos.run(scenario_name,
           config_file="default.xml",
           clean_up=False,
           mode="single_shot",
           make_flood_maps=True,
           make_wave_maps=True,
           upload=False,
           webviewer="psips_event_viewer")

# cosmos.make_webviewer(scenario_name, "psips_event_viewer")
# cosmos.upload(webviewer="psips_event_viewer")
# cosmos.post_process(scenario_name, model="sfincs_north_florida")

