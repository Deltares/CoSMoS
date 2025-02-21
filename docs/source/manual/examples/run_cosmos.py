# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:36:35 2021

@author: ormondt
"""
from cosmos.cosmos_main import cosmos

main_path = r"c:\work\cosmos\run_folder"

scenario_name = "philippines_nov2013_ifs"

# CoSMoS is always initialized with the main path and optianlly a configuration file
cosmos.initialize(
    main_path,
    config_file="config.toml",
    )

# Eventually, you can overwrite configuration settings like this:
# cosmos.config.run.mode = "single"
# cosmos.config.run.just_initialize = False
# cosmos.config.run.clean_up = False
cosmos.config.run.download_meteo = False

# Finally, run the scenario and optionally specify the cycle
cosmos.run(scenario_name, cycle="20131107_00z")