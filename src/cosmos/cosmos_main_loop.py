# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:28:48 2021

@author: ormondt
"""

import time
import datetime
import sched
import os
import numpy as np

from .cosmos_main import cosmos
from .cosmos_meteo import download_meteo, collect_meteo
from .cosmos_track_ensemble import setup_track_ensemble
from .cosmos_scenario import Scenario
from .cosmos_cloud import Cloud
from .cosmos_tsunami import CoSMoS_Tsunami
from .cosmos_webviewer import WebViewer

try:
    from .cosmos_argo import Argo
except:
    print("Argo not available")

import cht_utils.fileops as fo


class MainLoop:
    """Read the scenario.toml file, determine cycle times, and run cosmos model loop.

    Parameters
    ----------
    start : func
        Start cosmos scenario
    run : func
        Run main loop

    See Also
    --------
    cosmos.cosmos_main.CoSMoS
    cosmos.cosmos_scenario.Scenario
    cosmos.cosmos_model_loop.ModelLoop
    cosmos.cosmos_model.Model
    """

    def __init__(self):
        # Try to kill all instances of main loop and model loop
        self.just_initialize = False
        self.run_models = True
        self.clean_up = False

    def start(self, cycle=None):
        """Update the configuration, read the scenario.toml file, determine cycle times, initialize webviewer, and start cosmos_main_loop.run with scheduler.

        Parameters
        ----------
        cycle : int
            Datestring of cycle time

        See Also
        --------
        cosmos.cosmos_configuration.Configuration
        cosmos.cosmos_main_loop.MainLoop.run
        """

        # Determines cycle time and runs main loop

        cosmos.log("Starting main loop ...")

        # DO NOT DO THIS ANYMORE (once config is set, it should not be read in anymore)
        # # Update config (it's possible that this was changed while running a forecast scenario)
        # cosmos.config.set()

        # Set cloud object
        if cosmos.config.run.run_mode == "cloud":
            cosmos.cloud = Cloud()
            cosmos.argo = Argo()

        # Read scenario
        cosmos.scenario = Scenario(cosmos.scenario_name)
        # This also determines which models are part of this scenario
        cosmos.scenario.read()

        if not cycle:
            # Determine cycle time
            # if cosmos.scenario.cycle:
            #     # Cycle provided in scenario file
            #     cosmos.cycle = cosmos.scenario.cycle.replace(
            #         tzinfo=datetime.timezone.utc
            #     )
            # else:
            # First main loop in forecast scenario
            # Determine which cycle to run
            delay = 0
            t = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
                hours=delay
            )
            h0 = t.hour
            h0 = h0 - np.mod(h0, cosmos.config.run.interval)
            cosmos.cycle = t.replace(microsecond=0, second=0, minute=0, hour=h0)
        else:
            cosmos.cycle = cycle.replace(tzinfo=datetime.timezone.utc)

        # Determine end time of cycle
        cosmos.stop_time = cosmos.cycle + datetime.timedelta(
            hours=cosmos.scenario.runtime
        )

        # Determine next cycle time
        if cosmos.config.run.mode == "continuous":
            cosmos.next_cycle_time = cosmos.cycle + datetime.timedelta(hours=cosmos.config.run.interval)
            if cosmos.last_cycle:
                if cosmos.cycle >= cosmos.last_cycle:
                    cosmos.next_cycle_time = None
        else:            
            # Single shot mode, so no next cycle
            cosmos.next_cycle_time = None

        # Cycle string (used for file and folder names)
        cosmos.cycle_string = cosmos.cycle.strftime("%Y%m%d_%Hz")

        # Web viewer
        if cosmos.config.webviewer and cosmos.config.run.make_webviewer:
            # Prepare new web viewer, or copy scenario data to existing viewer
            # Add scenario folder, cycle folder to web viewer
            cosmos.webviewer = WebViewer(cosmos.config.webviewer.name)

        # Set scenario paths
        cosmos.scenario.set_paths()

        # Determine time at which this cycle should start running
        # When running in single_shot mode, the simulation should start immediately
        delay = datetime.timedelta(hours=0)  # Delay in hours
        tnow = datetime.datetime.now(datetime.timezone.utc)
        print(cosmos.config.run.mode)
        if tnow > cosmos.cycle + delay or cosmos.config.run.mode == "single_shot":
            # start now
            start_time = tnow + datetime.timedelta(seconds=1)
        else:
            # start after delay
            start_time = cosmos.cycle + delay + datetime.timedelta(seconds=5)
        self.scheduler = sched.scheduler(time.time, time.sleep)
        dt = start_time - tnow

        # Kick off main_loop run
        cosmos.log(
            "Next cycle "
            + cosmos.cycle_string
            + " will start at "
            + start_time.strftime("%Y-%m-%d %H:%M:%S")
            + " UTC"
        )
        self.scheduler.enter(dt.seconds, 1, self.run, ())
        self.scheduler.run()

    def run(self):
        """Run main loop.

        - Prepare models: Get list of nested models and set paths
        - Check if model data needs to be uploaded to webviewer
        - Get start and stop times
        - Download and collect meteo
        - Optional: Make track ensemble or spiderweb from track file
        - Check which models are finished
        - Start model loop

        See Also
        --------
        cosmos.cosmos_model.Model.get_nested_models
        cosmos.cosmos_model.Model.set_paths
        cosmos.cosmos_meteo.Meteo.download_and_collect_meteo
        cosmos.cosmos_track_ensemble.setup_track_ensemble
        cosmos.cosmos_model_loop.ModelLoop.start
        """

        # Start by reading all available models, stations, etc.
        cosmos.log("Starting cycle ...")

        # Clean up should be moved to different function
        if self.clean_up:
            # Don't allow clean up when just initializing or continuous mode
            if not self.just_initialize and cosmos.config.run.mode == "single_shot":
                # Remove all old modelruns in scenario folder
                pths = fo.list_folders(os.path.join(cosmos.scenario.path, "*"))
                for pth in pths:
                    fo.rmdir(pth)
                # Remove all the webviewer tiles from the local webviewer folder
                pths = fo.list_folders(
                    os.path.join(
                        cosmos.config.webviewer.data_path, cosmos.scenario.name, "*"
                    )
                )
                for pth in pths:
                    fo.rmdir(pth)
                # Clear the job list
                fo.rmdir(os.path.join(cosmos.config.path.jobs, cosmos.scenario.name))

        # Remove older cycles
        if not self.just_initialize and cosmos.config.run.mode == "continuous":
            if cosmos.config.run.remove_old_cycles > 0 and not cosmos.storm_flag:
                # Get list of all cycles in scneario folder
                cycle_list = fo.list_folders(os.path.join(cosmos.scenario.path, "*z"))
                tkeep = cosmos.cycle.replace(tzinfo=None) - datetime.timedelta(
                    hours=cosmos.config.run.remove_old_cycles
                )
                for cycle in cycle_list:
                    if cycle in cosmos.storm_keeplist:
                        continue
                    keepfile_name = os.path.join(cycle, "keep.txt")
                    if os.path.exists(keepfile_name):
                        cosmos.storm_keeplist.append(cycle)
                        continue
                    t = datetime.datetime.strptime(cycle[-12:], "%Y%m%d_%Hz")
                    if t < tkeep:
                        cosmos.log("Removing older cycle : " + cycle[-12:])
                        fo.rmdir(cycle)
                        cosmos.log(
                            "Also removing webviewer tiles of older cycle : "
                            + cycle[-12:]
                        )
                        try:
                            fo.rmdir(
                                os.path.join(
                                    cosmos.config.webviewer.data_path,
                                    cosmos.scenario.name,
                                    cycle[-12:],
                                )
                            )
                        except:
                            pass

            elif cosmos.storm_flag:
                cycle_list = fo.list_folders(os.path.join(cosmos.scenario.path, "*z"))
                cosmos.storm_keeplist.append(cycle_list[-1])

        # Create scenario cycle paths
        fo.mkdir(cosmos.scenario.cycle_path)
        fo.mkdir(cosmos.scenario.cycle_models_path)
        fo.mkdir(cosmos.scenario.cycle_job_list_path)

        # Prepare some stuff for each model
        for model in cosmos.scenario.model:
            model.get_nested_models()
            model.set_paths()
            # Set model status
            model.status = "waiting"
            if model.priority == 0:
                model.run_simulation = False

        # Check if model data needs to be uploaded to webviewer (only upload for high-res nested models)
        # Can this be moved to the model class?
        modelopt = ["flow", "wave"]
        modeloptnames = ["tide_gauge", "wave_buoy"]
        for model in cosmos.scenario.model:
            for iopt, opts in enumerate(modelopt):
                all_nested_models = model.get_all_nested_models(opts)
                if all_nested_models:
                    all_nested_stations = []
                    if all_nested_models[0].type == "beware":
                        all_nested_models = [model]
                        bw = 1
                    else:
                        bw = 0
                    for mdl in all_nested_models:
                        for st in mdl.station:
                            all_nested_stations.append(st.name)
                    for station in model.station:
                        if station.type == modeloptnames[iopt]:
                            if station.name in all_nested_stations and bw == 0:
                                station.upload = False

        # Start and stop times
        cosmos.log("Getting start and stop times ...")
        get_start_and_stop_times()

        # Set reference date to minimum of all start times
        rfdate = datetime.datetime(2200, 1, 1, 0, 0, 0)
        for model in cosmos.scenario.model:
            if model.flow:
                rfdate = min(rfdate, model.flow_start_time)
            if model.wave:
                rfdate = min(rfdate, model.wave_start_time)
        cosmos.scenario.ref_date = datetime.datetime(
            rfdate.year, rfdate.month, rfdate.day, 0, 0, 0
        )

        # Write start and stop times to log file
        for model in cosmos.scenario.model:
            if model.flow:
                cosmos.log(
                    model.long_name
                    + " : "
                    + model.flow_start_time.strftime("%Y%m%d %H%M%S")
                    + " - "
                    + model.flow_stop_time.strftime("%Y%m%d %H%M%S")
                )
            else:
                cosmos.log(
                    model.long_name
                    + " : "
                    + model.wave_start_time.strftime("%Y%m%d %H%M%S")
                    + " - "
                    + model.wave_stop_time.strftime("%Y%m%d %H%M%S")
                )

        # if self.just_initialize:
        #     # No need to do anything else here 
        #     return

        if cosmos.config.run.event_mode == "meteo":
            # Running storm or other weather event

            # Download meteo data
            if cosmos.config.run.download_meteo:
                download_meteo()

            # Merge meteo data (in case of forcing with track file, this is also where the spiderweb is generated)
            collect_meteo()

            if cosmos.scenario.run_ensemble and cosmos.tropical_cyclone:    
                # Make track ensemble (this also add 'new' ensemble models that fall within the cone)
                setup_track_ensemble()
            # elif cosmos.scenario.meteo_spiderweb or not os.path.isabs(cosmos.scenario.meteo_track):
            #     # Make spiderweb if does not exist yet
            #     track_to_spw()

        elif cosmos.config.run.event_mode == "tsunami":
            # Generate tsunami NetCDF file. Initial conditions for model(s) are generated from this file.
            cosmos.log("Generating tsunami NetCDF file ...")
            cosmos.tsunami = CoSMoS_Tsunami()
            cosmos.tsunami.generate_from_scenario(cosmos.scenario.finite_fault_file)

        # Should remove this at some point?
        if self.just_initialize:
            # No need to do anything else here, except for setting the status of the models
            for model in cosmos.scenario.model:
                model.status = "finished"
            return

        # Get list of models that have already finished and set their status to finished
        finished_list = os.listdir(cosmos.scenario.cycle_job_list_path)
        for model in cosmos.scenario.model:
            for file_name in finished_list:
                model_name = file_name.split(".")[0]
                if model.name.lower() == model_name.lower():
                    model.status = "finished"
                    model.run_simulation = False
                    break

        # Can run_models be False?
        if self.run_models:
            # Upload spw files to S3
            if (
                cosmos.scenario.run_ensemble
                and cosmos.tropical_cyclone
                and cosmos.config.run.run_mode == "cloud"
            ):
                # Upload spw files to S3
                cosmos.log("Uploading spiderweb files to S3")
                path = cosmos.scenario.cycle_track_ensemble_spw_path
                subfolder = cosmos.scenario.name + "/track_ensemble/spw"
                cosmos.cloud.upload_folder("cosmos-scenarios", path, subfolder)

            # And now start the model loop
            cosmos.log("Starting model loop ...")
            cosmos.model_loop.start()


def get_start_and_stop_times():
    """Get cycle start and stop times."""

    y = cosmos.cycle.year
    cosmos.reference_time = datetime.datetime(y, 1, 1)

    start_time = cosmos.cycle

    stop_time = cosmos.stop_time

    start_time = start_time.replace(tzinfo=None)
    stop_time = stop_time.replace(tzinfo=None)

    cosmos.stop_time = stop_time

    # Find all the models that do not have any models nested in them

    # First waves

    for model in cosmos.scenario.model:
        if model.wave:
            model.wave_start_time = start_time
            model.wave_stop_time = stop_time

    not_nested_models = []
    for model in cosmos.scenario.model:
        if model.wave:
            # This is a wave model
            if not model.nested_wave_models:
                # And it does not have any model nested in it
                not_nested_models.append(model)

    # Now for each of these models, loop up in the model tree until
    # not nested in any other model
    for not_nested_model in not_nested_models:
        nested = True
        model = not_nested_model
        nested_wave_start_time = start_time

        while nested:
            model.wave_start_time = min(model.wave_start_time, nested_wave_start_time)

            # Check for restart files
            restart_time, restart_file = check_for_wave_restart_files(model)
            if not restart_time:
                # No restart file available, so subtract spin-up time
                tok = start_time - datetime.timedelta(hours=model.wave_spinup_time)
                model.wave_start_time = min(model.wave_start_time, tok)
                model.wave_restart_file = None
            else:
                model.wave_start_time = restart_time
                model.wave_restart_file = restart_file

            if model.wave_nested:
                # This model gets it's wave boundary conditions from another model
                nested_wave_start_time = model.wave_start_time
                model = model.wave_nested

            else:
                # Done looping through the tree
                nested = False

    # And now flow

    for model in cosmos.scenario.model:
        if model.flow:
            if model.wave:
                model.flow_start_time = model.wave_start_time
                model.flow_stop_time = model.wave_stop_time
            else:
                model.flow_start_time = start_time
                model.flow_stop_time = stop_time

    not_nested_models = []
    for model in cosmos.scenario.model:
        if model.flow:
            # This is a flow model
            if not model.nested_flow_models:
                # And it does not have any model nested in it
                not_nested_models.append(model)

    # Now for each of these models, loop up in the model tree until
    # not nested in any other model
    for not_nested_model in not_nested_models:
        nested = True
        model = not_nested_model
        nested_flow_start_time = start_time

        while nested:
            model.flow_start_time = min(model.flow_start_time, nested_flow_start_time)

            # Check for restart files
            restart_time, restart_file = check_for_flow_restart_files(model)

            if not restart_time:
                # No restart file available, so subtract spin-up time
                tok = start_time - datetime.timedelta(hours=model.flow_spinup_time)
                model.flow_start_time = min(model.flow_start_time, tok)
                model.flow_restart_file = None
            else:
                model.flow_start_time = restart_time
                model.flow_restart_file = restart_file

            if model.flow_nested:
                # This model gets it's flow boundary conditions from another model
                nested_flow_start_time = model.flow_start_time
                # On to the next model in the chain
                model = model.flow_nested

            else:
                # Done looping through the tree
                nested = False

    # For only wave model, also add flow start and stop time (used for meteo)
    for model in cosmos.scenario.model:
        if model.wave:
            if not model.flow_start_time:
                model.flow_start_time = model.wave_start_time
            if not model.flow_stop_time:
                model.flow_stop_time = model.wave_stop_time


def check_for_wave_restart_files(model):
    """Check if there are wave restart files."""
    restart_time = None
    restart_file = None

    path = model.restart_wave_path

    if os.path.exists(path):
        restart_list = os.listdir(path)
        times = []
        files = []
        for file_name in restart_list:
            tstr = file_name[-19:-4]
            t = datetime.datetime.strptime(tstr, "%Y%m%d.%H%M%S")
            times.append(t)
            files.append(file_name)

        # Now find the last time that is greater than the start time
        # and smaller than
        for it, t in enumerate(times):
            if (
                t
                > model.wave_start_time
                - datetime.timedelta(hours=model.wave_spinup_time)
                and t <= model.wave_start_time
            ):
                restart_time = t
                restart_file = files[it]
    else:
        fo.mkdir(path)

    return restart_time, restart_file


def check_for_flow_restart_files(model):
    """Check if there are flow restart files."""
    restart_time = None
    restart_file = None

    path = model.restart_flow_path

    if os.path.exists(path):
        restart_list = os.listdir(path)
        times = []
        files = []
        for file_name in restart_list:
            tstr = file_name[-19:-4]
            t = datetime.datetime.strptime(tstr, "%Y%m%d.%H%M%S")
            times.append(t)
            files.append(file_name)

        # Now find the last time that is greater than the start time
        # and smaller than
        for it, t in enumerate(times):
            if (
                t
                >= model.flow_start_time
                - datetime.timedelta(hours=model.flow_spinup_time)
                and t <= model.flow_start_time
            ):
                restart_time = t
                restart_file = files[it]
    else:
        fo.mkdir(path)

    return restart_time, restart_file
