# Run Ensemble model (including pre and post processing)

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
        # Loop over ensemble members and run them in one by one
        curdir = os.getcwd()
        for ensemble_member in ensemble_members:
            print('Running ensemble member ' + ensemble_member)
            # Make folder for ensemble member and copy all input files
            fo.mkdir(ensemble_member)
            fo.copy_file("*.*", ensemble_member)
            os.chdir(ensemble_member)
            os.system("call run.bat\n")
            # Delete everything except for the output files (is this really necessary at this point?)
            flist = fo.list_files(".", full_path=False)
            for f in flist:
                if f != 'sfincs_his.nc' and f != 'sfincs_map.nc' and f != 'hurrywave_his.nc' and f != 'hurrywave_map.nc' and f != 'hurrywave_sp2.nc' and f != 'beware_his.nc':
                    fo.delete_file(f)
            os.chdir(curdir)

#    # Merge output files
#    os.system('python3 merge_SFINCS.py')

else:

    if config["run_mode"] == "cloud": 
        # Run sfincs simulation and wait for it to be finished
        pass
    
    else:
        os.system("call run.bat\n")



# # Make floodmap tiles
# os.system('python3 make_floodmap_tiles.py')




