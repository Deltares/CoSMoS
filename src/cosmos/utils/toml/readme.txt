%% Readme conversion yml/xml to toml

For the latest cosmos version, the toml format is used for all configuration files. This includes:

- ..\cosmos\run_folder\configuration\color_maps\map_contours.toml
- ..\cosmos\run_folder\configuration\stations\[station_name].toml
- ..\cosmos\run_folder\configuration\super_regions\[super_region_name].toml
- ..\cosmos\run_folder\configuration\config_mvo.toml
- ..\cosmos\run_folder\meteo\meteo_subsets.toml
- ..\cosmos\run_folder\scenarios\[scenario_name]\scenario.toml
- ..\cosmos\model_database\[region_name]\[model_type]\[model_name]\model.toml

Use the scripts in cosmos\src\utils for file conversion.