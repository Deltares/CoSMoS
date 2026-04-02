"""Script to run CoSMoS model jobs in parallel on a worker node.

Monitors a shared job folder and executes queued model simulations locally
using the CosmosRunParallel job runner.
"""

import sys
import os

# either use single copy of cosmos_run_parallel and add path (e.g. c:\\fhics)
sys.path.append(r"c:\\fhics")
from cosmos.cosmos_run_parallel import CosmosRunParallel

# or use both from cosmos-package
# from cosmos.cosmos_run_parallel import CosmosRunParallel

main_path = "p:\\11206085-onr-fhics\\03_cosmos\\"
# scenario = "gom_forecast"
# scenario = "gom_forecast"
scenario = None
job_path = os.path.join(main_path, "jobs")

local_path = os.path.join("c:\\fhics", "running")
if not os.path.exists(local_path):
    os.mkdir(local_path)

runloop = CosmosRunParallel()
runloop.start(job_path, local_path, scenario)
