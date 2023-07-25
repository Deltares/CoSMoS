# Run SFINCS model (including pre and post processing)

import os
from cht.misc.misc_tools import yaml2dict
import cht.misc.fileops as fo

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
    if config["ensemble"]:

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
                # Delete everything except the output files
                flist = fo.list_files(".", full_path=False)
                for f in flist:
                    if f != 'sfincs_his.nc' and f != 'sfincs_map.nc':
                        fo.delete_file(f)
                os.chdir(curdir)

    else:

        os.system('python cosmos_run_sfincs_member.py')


# # Merge output files
# os.system('python3 merge_SFINCS.py')

# # Make floodmap tiles
# os.system('python3 make_floodmap_tiles.py')




