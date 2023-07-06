# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:36:35 2021

@author: ormondt
"""

from cosmos.cosmos_main import cosmos

main_path = r"c:\cosmos"

scenario_name = "hurricane_irma_gfs"

cosmos.initialize(main_path)

cosmos.run(scenario_name,
           config_file="default.xml",
           clean_up=False,
           mode="single_shot",
           make_flood_maps=True,
           make_wave_maps=True,
           upload=False,
           make_figures= False,
           webviewer="version02",
           ensemble= False,
           get_meteo = True)

# cosmos.post_process(scenario_name, model = 'all')
# cosmos.make_webviewer(scenario_name, "version02")


