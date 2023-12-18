""" Run COSMOS for a single scenario. """

# TODO: Add multiple scenarios to create a testebd

from cosmos.cosmos_main import cosmos

main_path = "p:\\11206085-onr-fhics\\cosmos_test\\run_folder"

scenario_name = "nopp_test"

cosmos.initialize(main_path,
                  mode="single_shot",
                  config_file="config.toml",
                  make_wave_maps=False,
                  only_run_ensemble=False,
                  get_meteo=True)

cosmos.run(scenario_name, "20230829_00z")
