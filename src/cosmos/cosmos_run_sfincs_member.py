import yaml
import sys
import os

from cht.sfincs.sfincs import SFINCS
from cht.nesting import nest2
import cht.misc.fileops as fo
from cht.misc.misc_tools import yaml2dict

# Read config file (config.yml)
config = yaml2dict("config.yml")

if len(sys.argv) == 1:
    # Not an ensemble member
    ensemble_member_name = None
else:
    ensemble_member_name = sys.argv[1]


# Read SFINCS model
sf = SFINCS("sfincs.inp")

# Nesting
if "flow_nested_path" in config:

    # Get boundary conditions from overall model (Nesting 2)

    # Correct boundary water levels. Assuming that output from overall
    # model is in MSL !!!
    zcor = config["boundary_water_level_correction"] - config["vertical_reference_level_difference_with_msl"]

    # Get boundary conditions from overall model (Nesting 2)
    if config["ensemble"]:
        nest2(self.flow_nested.domain,
                self.domain,
                output_path=os.path.join(self.flow_nested.cycle_output_path, ensemble_member_name),
                output_file= 'sfincs_his.nc',
                boundary_water_level_correction=zcor,
                option="flow",
                bc_path=os.path.join(self.job_path, name))
    else:
        # Deterministic    
        nest2(self.flow_nested.domain,
                self.domain,
                output_path=self.flow_nested.cycle_output_path,
                output_file='sfincs_his.nc',
                boundary_water_level_correction=zcor,
                option="flow",
                bc_path=self.job_path)
    
if "wave_nested_path" in config:
    # Get wave boundary conditions from overall model (Nesting 2)

    # Get boundary conditions from overall model (Nesting 2)
    if config["ensemble"]:
        # Loop through ensemble members
        nest2(self.wave_nested.domain,
                self.domain,
                output_path=os.path.join(self.wave_nested.cycle_output_path, ensemble_member_name),
                option="wave",
                bc_path=os.path.join(self.job_path, ensemble_member_name))
    else:
        # Deterministic    
        nest2(self.wave_nested.domain,
                self.domain,
                output_path=self.wave_nested.cycle_output_path,
                option="wave",
                bc_path=self.job_path)

# If SFINCS nested in Hurrywave for SNAPWAVE setup, separately run BEWARE nesting for LF waves
if "bw_nested_path" in config:

    # Get wave maker conditions from overall model (Nesting 2)
    if config["ensemble"]:
        # Loop through ensemble members
        nest2(self.bw_nested.domain,
                self.domain,
                output_path=os.path.join(self.bw_nested.cycle_output_path, ensemble_member_name),
                option="wave",
                bc_path=os.path.join(self.job_path, name))
    else:
        # Deterministic    
        nest2(self.bw_nested.domain,
                self.domain,
                output_path=self.bw_nested.cycle_output_path,
                option="wave",
                bc_path=self.job_path)

    sf.write_wavemaker_forcing_points()

# Copy the correct spiderweb file
if config["ensemble"]:
    # Copy all spiderwebs to jobs folder
    fname0 = os.path.join(config["spw_path"],
                            "ensemble" + ensemble_member_name + ".spw")
    fo.copy_file(fname0, "sfincs.spw")

# Run the SFINCS model (this is only for windows now)
os.system("call run_sfincs.bat\n")
