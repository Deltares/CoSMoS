# Run SFINCS model (including pre and post processing)

import os
import pandas as pd  
import numpy as np
from cht.misc.misc_tools import yaml2dict
import cht.misc.fileops as fo
from cht.misc.prob_maps import merge_nc_his
from cht.misc.prob_maps import merge_nc_map
from cht.tiling.tiling import make_floodmap_tiles
import datetime
from cht.sfincs.sfincs import SFINCS

sf = SFINCS()

# Read config file (config.yml)
config = yaml2dict("config.yml")

if config["ensemble"]:

    # Read in the list of overland ensemble members
    with open('ensemble_members.txt') as f:
        ensemble_members = f.readlines()
    ensemble_members = [x.strip() for x in ensemble_members]

    if config["run_mode"] == "cloud": 
        # Run sfincs members and wait for all members to be finished
        pass

    else:
        # Loop over ensemble members and run them in one by one
        curdir = os.getcwd()
        for ensemble_member in ensemble_members:
            print('Running ensemble member ' + ensemble_member)
            # Make folder for ensemble member and copy all input files
            fo.mkdir(ensemble_member)
            fo.copy_file("*.*", ensemble_member)
            os.chdir(ensemble_member)
            os.system('python cosmos_run_sfincs_member.py ' + ensemble_member)
            os.chdir(curdir)

    # Merge output files
    his_files = []
    map_files = []
    for ensemble_member in ensemble_members:
        his_files.append(ensemble_member + '/sfincs_his.nc')
        map_files.append(ensemble_member + '/sfincs_map.nc')
    merge_nc_his(his_files, ["point_zs"], output_file_name="./sfincs_his.nc")
    if "flood_map" in config:
        merge_nc_map(map_files, ["zsmax"], output_file_name="./sfincs_map.nc")

    # Copy restart files from the first ensemble member (restart files are the same for all members)
    fo.copy_file(ensemble_members[0] + '/sfincs.*.rst', './')    

else:

    if config["run_mode"] == "cloud": 
        # Run sfincs simulation and wait for it to be finished
        pass
    
    else:
        os.system('python cosmos_run_sfincs_member.py')

# Make flood map tiles
if "flood_map" in config:

    print("Make flood map")

    flood_map_path = config["flood_map"]["png_path"]
    index_path     = config["flood_map"]["index_path"]
    topo_path      = config["flood_map"]["topo_path"]
            
    if os.path.exists(index_path) and os.path.exists(topo_path):
        
        print("Making flood map tiles for model " + config["name"] + " ...")                

        # 24 hour increments  
        dtinc = 12

        # Wave map for the entire simulation
        dt1 = datetime.timedelta(hours=1)
        dt  = datetime.timedelta(hours=dtinc)
        t0  = config["flood_map"]["start_time"].replace(tzinfo=None)
        t1  = config["flood_map"]["stop_time"].replace(tzinfo=None)
            
        requested_times = pd.date_range(start=t0 + dt,
                                        end=t1,
                                        freq=str(dtinc) + "H").to_pydatetime().tolist()

        color_values = config["flood_map"]["color_map"]["contours"]

        pathstr = []
        for it, t in enumerate(requested_times):
            pathstr.append((t - dt).strftime("%Y%m%d_%HZ") + "_" + (t).strftime("%Y%m%d_%HZ"))

        pathstr.append("combined_" + (t0).strftime("%Y%m%d_%HZ") + "_" + (t1).strftime("%Y%m%d_%HZ"))

        zsmax_file = "./sfincs_map.nc"
        if config["ensemble"]:
            varname = "zsmax_90"
        else:
            varname = "zsmax"    

        try:

            # Inundation map over dt-hour increments                    
            for it, t in enumerate(requested_times):

                zsmax = sf.read_zsmax(zsmax_file=zsmax_file,
                                      time_range=[t - dt + dt1, t + dt1],
                                      varname=varname)


                # Difference between MSL and NAVD88 (used in topo data)
                zsmax += config["vertical_reference_level_difference_with_msl"]
                zsmax = np.transpose(zsmax)

                png_path = os.path.join(flood_map_path,
                                        config["scenario"],
                                        config["cycle"],
                                        config["flood_map"]["name"],
                                        pathstr[it])                                            

                make_floodmap_tiles(zsmax,
                                    index_path,
                                    png_path,
                                    topo_path,
                                    color_values=color_values,
                                    zoom_range=[0, 13],
                                    zbmax=1.0,
                                    quiet=True)

            # Full simulation        
            zsmax = sf.read_zsmax(zsmax_file=zsmax_file,
                                  time_range=[t0 + dt1, t1 + dt1],
                                  varname=varname)
            zsmax += config["vertical_reference_level_difference_with_msl"]
            zsmax = np.transpose(zsmax)

            png_path = os.path.join(flood_map_path,
                                    config["scenario"],
                                    config["cycle"],
                                    config["flood_map"]["name"],
                                    pathstr[-1]) 

            make_floodmap_tiles(zsmax, index_path, png_path, topo_path,
                                color_values=color_values,
                                zoom_range=[0, 13],
                                zbmax=1.0,
                                quiet=True)

        except:
            print("An error occured while making flood map tiles")

if config["ensemble"]:
    # Remove ensemble members
    for ensemble_member in ensemble_members:
        fo.delete_folder(ensemble_member)




