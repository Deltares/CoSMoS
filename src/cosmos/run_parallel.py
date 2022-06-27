# -*- coding: utf-8 -*-
"""
Created on Wed May 18 16:29:05 2022

@author: goede_rl
"""

import sys
import os

# either use single copy of cosmos_run_parallel and add path (e.g. c:\\fhics)
sys.path.append(r'c:\\fhics')
from cosmos_run_parallel import CosmosRunParallel

# or use both from cosmos-package
# from cosmos.cosmos_run_parallel import CosmosRunParallel

main_path = "p:\\11206085-onr-fhics\\03_cosmos\\"
scenario = "hurricane_michael_coamps"
job_path = os.path.join(main_path,"jobs", scenario)

local_path = os.path.join("c:\\fhics", "running")
if not os.path.exists(local_path):
    os.mkdir(local_path)

runloop = CosmosRunParallel()
runloop.start(job_path=job_path,local_path=local_path)

