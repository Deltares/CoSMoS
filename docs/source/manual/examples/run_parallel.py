# -*- coding: utf-8 -*-
"""
run_parallel.py

Created on Wed May 18 16:29:05 2022

@author: goede_rl
"""

import sys
import os

# either use single copy of cosmos_run_parallel and add path
sys.path.append(r'c:\\cosmos_run_folder')
from cosmos_run_parallel import CosmosRunParallel

# or use both from cosmos-package
# from cosmos.cosmos_run_parallel import CosmosRunParallel

main_path = "p:\\cosmos\\run_folder\\"
# scenario = "hurricane_laura"
scenario = None
job_path = os.path.join(main_path,"jobs")

local_path = os.path.join("c:\\cosmos_run_folder", "running")
if not os.path.exists(local_path):
    os.mkdir(local_path)

runloop = CosmosRunParallel()
runloop.start(job_path, local_path, scenario)

