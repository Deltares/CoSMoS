"""Example script to run CoSMoS models in parallel on a worker node."""

import os

from cosmos.run_parallel import CosmosRunParallel

main_path = r"p:\cosmos\run_folder"
scenario = None  # or e.g. "hurricane_laura"
job_path = os.path.join(main_path, "jobs")

local_path = os.path.join(r"c:\cosmos_run_folder", "running")
if not os.path.exists(local_path):
    os.mkdir(local_path)

runloop = CosmosRunParallel()
runloop.start(job_path, local_path, scenario)
