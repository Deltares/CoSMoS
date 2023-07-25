import yaml
import sys
import os

from cht.sfincs import SFINCS
from cht.nesting import nest2
import cht.misc.fileops as fo

if len(sys.argv) == 1:
    # Not an ensemble member
    ensemble_member_name = None
else:
    ensemble_member_name = sys.argv[1]

# Read config file (config.yml)
config = {}
config["ensemble"] = True

if config["ensemble"]:
    # Make folder for ensemble member and copy all input files
    fo.make_folder(ensemble_member_name)
    fo.copy_file("*", ensemble_member_name)
    os.chdir(ensemble_member_name)

# Read SFINCS model
sf = SFINCS("sfincs.inp")

# Nesting
if config["flow_nested"]:

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
    
if config["wave_nested"]:
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
if config["bw_nested"]:

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
    fname0 = os.path.join(cosmos.scenario.cycle_track_ensemble_spw_path,
                            "ensemble" + ensemble_member_name + ".spw")
    fname1 = os.path.join(self.job_path, name, "sfincs.spw")
    fo.copy_file(fname0, fname1)

# Run the SFINCS model
