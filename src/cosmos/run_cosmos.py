""" Run COSMOS for a single scenario. """

# TODO: Add multiple scenarios to create a testebd

from cosmos.cosmos_main import cosmos

main_path = "p:\\11206085-onr-fhics\\cosmos_test\\run_folder"

scenario_name = "nopp_test"

# CoSMoS is always initialized with the main path and optianlly a configuration file
cosmos.initialize(
    main_path,
    config_file="config.toml",
    )

# Eventually, you can overwrite configuration settings like this:
cosmos.config.run.mode = "single_shot"
cosmos.config.run.make_wave_maps = False
# cosmos.config.run.make_wave_maps=False,
# cosmos.config.run.only_run_ensemble=False,
# cosmos.config.run.get_meteo=True

# Finally, run the scenario and optionally specify the cycle
cosmos.run(scenario_name, cycle="20230829_00z")
