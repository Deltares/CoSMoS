# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:36:35 2021

@author: ormondt
"""

from cosmos.cosmos_main import cosmos

# Run cosmos_addpaths.py before executing run_cosmos.py

# sfincs_exe_path    = "d:\\checkouts\\SFINCS\\branches\\sfincs20_v01\\sfincs\\x64\\Release"
# hurrywave_exe_path = "d:\\checkouts\\hurrywave\\trunk\\hurrywave\\x64\\Release"
# delft3dfm_exe_path = "d:\\programs\\dflowfm\\2.01.00_55735"

main_path = "p:\\11206085-onr-fhics\\cosmos_test\\run_folder"

scenario_name = "nopp_test"

cosmos.initialize(main_path,
                  mode="single_shot",
                  config_file="config.toml",
                  make_wave_maps=False,
                  only_run_ensemble=False,
                  get_meteo=True)

cosmos.run(scenario_name, "20230829_00z")

