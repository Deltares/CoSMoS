# Run SFINCS model (including pre and post processing)

import os

# Read config file (config.yml)

if config["ensemble"]:
    # Read in the list of overland ensemble members
    with open('ensemble_members.txt') as f:
        ensemble_members = f.readlines()
    ensemble_members = [x.strip() for x in ensemble_members]

if config["run_mode"] == "cloud": 
    pass
else:
    if config["ensemble"]:
        # Loop over ensemble members
        for ensemble_member in ensemble_members:
            print('Running ensemble member ' + ensemble_member)
            os.system('python3 run_sfincs_member.py ' + ensemble_member)
            # Delete everything except the output files
    else:
        os.system('python3 run_sfincs_member.py')


# Merge output files
os.system('python3 merge_SFINCS.py')

# Make floodmap tiles
os.system('python3 make_floodmap_tiles.py')




