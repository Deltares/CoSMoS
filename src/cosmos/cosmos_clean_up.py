# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:29:24 2021

@author: ormondt
"""

from .cosmos_main import cosmos
import cht_utils.fileops as fo

def clean_up():
    """Remove old files in the jobs folder that are older than 1 day.
    """
    # Remove all files in the jobs folder that are older than 1 day
    if cosmos.config.run.clean_up_mode == "risk_map":
        remove_input_folders()
        remove_overall_model_folders()
        remove_all_restart_folders()
        remove_track_folder()
        remove_job_list_folder()


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
