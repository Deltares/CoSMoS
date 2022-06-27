# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:36:35 2021

@author: ormondt
"""

from cosmos.cosmos_main import cosmos

# Run cosmos_addpaths.py before executing run_cosmos.py

sfincs_exe_path    = "d:\\checkouts\\SFINCS\\branches\\sfincs20_v01\\sfincs\\x64\\Release"
hurrywave_exe_path = "d:\\checkouts\\hurrywave\\trunk\\hurrywave\\x64\\Release"
delft3dfm_exe_path = "d:\\programs\\dflowfm\\2.01.00_55735"

main_path = "d:\\cosmos"

scenario_name = "hurricane_michael_coamps"

cosmos.initialize(main_path)

cosmos.run(mode="single_shot",
           run_models=True,
           make_flood_maps=False,
           make_wave_maps=False,
           get_meteo=True,
           upload_data=False,
           make_figures=False,
           ensemble=False)
