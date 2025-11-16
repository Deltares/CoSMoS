# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:29:24 2021

@author: ormondt
"""
import os
import datetime

from .cosmos_main import cosmos
import cht_utils.fileops as fo

def clean_up():
    """Remove old files in the jobs folder that are older than 1 day.
    """
    if cosmos.config.run.clean_up_mode == "risk_map":
        # Remove all files in the jobs folder that are older than 1 day
        remove_input_folders()
        remove_overall_model_folders()
        remove_all_restart_folders()
        remove_track_folder()
        remove_job_list_folder()

    if cosmos.config.run.clean_up_mode == "continuous":
        # Remove older cycles restart files
        remove_older_cycles()
        remove_older_restart_files()
        remove_older_webviewer_cycles()

    if cosmos.config.run.clean_up_mode == "continuous_hindcast":
        remove_input_folders()
        remove_job_list_folder()
        remove_older_restart_files()


def remove_input_folders():
    for model in cosmos.scenario.model:
        input_path = model.cycle_input_path  
        fo.rmdir(input_path)

def remove_overall_model_folders():
    for model in cosmos.scenario.model:
        if len(model.nested_flow_models) > 0:
            fo.rmdir(model.cycle_path)

def remove_all_restart_folders():
    fo.rmdir(cosmos.scenario.restart_path)

def remove_track_folder():
    fo.rmdir(cosmos.scenario.cycle_track_spw_path)

def remove_job_list_folder():
    fo.rmdir(cosmos.scenario.cycle_job_list_path)

def remove_older_cycles():
    """Remove older cycles restart files, keeping only the latest cycle.
    """
    # List all folders 
    all_cycles = fo.list_folders(os.path.join(cosmos.scenario.path,'*'), basename=True)
    # Loop through cycles. The names are in the format YYYYMMDD_HHz. No need to sort, put need to check that folder name ends with 'z'
    # Then check if time is less than current cycle time (cosmos.cycle) - 2 days. cosmos.cycle has the time zone.
    for cycle in all_cycles:
        if cycle.endswith('z'):
            tstr = cycle.replace('z', '')
            t = datetime.datetime.strptime(tstr, "%Y%m%d_%H").replace(tzinfo=cosmos.cycle.tzinfo)
            if t < cosmos.cycle - datetime.timedelta(hours=cosmos.config.run.prune_after_hours):
                pth = os.path.join(cosmos.scenario.path, cycle)
                fo.rmdir(pth)
 
def remove_older_restart_files():
    # Remove restart files older than 3 days prior to the current cycle
    rstpath = cosmos.scenario.restart_path
    if os.path.exists(rstpath):
        all_models = fo.list_folders(os.path.join(rstpath,'*'), basename=True)
        for model in all_models:
            # FLOW
            restart_path_flow = os.path.join(rstpath, model, 'flow')
            flow_restart_files = fo.list_files(restart_path_flow, full_path=False)
            for file in flow_restart_files:
                # The files are in the format modeltype.YYYYMMDD.HHMMSS.rst
                if file.endswith('.rst'):
                    tstr = file.replace('.rst', '')[-15:]  # Get the YYYYMMDDHHMMSS part
                    t = datetime.datetime.strptime(tstr, "%Y%m%d.%H%M%S").replace(tzinfo=cosmos.cycle.tzinfo)
                    if t < cosmos.cycle - datetime.timedelta(hours=cosmos.config.run.prune_after_hours):
                        pth = os.path.join(restart_path_flow, file)
                        cosmos.log(f"Removing old restart file : {pth}")
                        os.remove(pth)
            # WAVE
            restart_path_wave = os.path.join(rstpath, model, 'wave')
            wave_restart_files = fo.list_files(restart_path_wave, full_path=False)
            for file in wave_restart_files:
                # The files are in the format modeltype.YYYYMMDD.HHMMSS.rst
                if file.endswith('.rst'):
                    tstr = file.replace('.rst', '')[-15:]  # Get the YYYYMMDDHHMMSS part
                    t = datetime.datetime.strptime(tstr, "%Y%m%d.%H%M%S").replace(tzinfo=cosmos.cycle.tzinfo)
                    if t < cosmos.cycle - datetime.timedelta(hours=cosmos.config.run.prune_after_hours):
                        pth = os.path.join(restart_path_wave, file)
                        cosmos.log(f"Removing old restart file : {pth}")
                        os.remove(pth)            

def remove_older_webviewer_cycles():
    # Remove older webviewer cycles, keeping only the latest 5 cycles
    # List all folders
    wvpath = os.path.join(cosmos.webviewer.path,
                          "data",
                          cosmos.scenario.name)

    all_cycles = fo.list_folders(os.path.join(wvpath,'*'), basename=True)
    # Loop through cycles. The names are in the format YYYYMMDD_HHz. No need to sort, put need to check that folder name ends with 'z'
    # Then check if time is less than current cycle time (cosmos.cycle) - 3 days. cosmos.cycle has the time zone.
    for cycle in all_cycles:
        if cycle.endswith('z'):
            tstr = cycle.replace('z', '')
            t = datetime.datetime.strptime(tstr, "%Y%m%d_%H").replace(tzinfo=cosmos.cycle.tzinfo)
            if t < cosmos.cycle - datetime.timedelta(hours=24):
                pth = os.path.join(wvpath, cycle)
                fo.rmdir(pth)
