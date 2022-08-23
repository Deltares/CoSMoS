# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:29:24 2021

@author: ormondt
"""
import time
import sched
import os

from .cosmos_main import cosmos
from .cosmos_cluster import cluster_dict as cluster
from .cosmos_postprocess import post_process
import cht.misc.fileops as fo

class ModelLoop:

    def __init__(self):
        pass
        
    def start(self):
        
        self.status = "running"
        while self.status == "running":        
            # This will be repeated until the status of the model loop changes to "done" 
            self.scheduler = sched.scheduler(time.time, time.sleep)
            dt = 1.0 # Execute the next model loop 1 second from now
            self.scheduler.enter(dt, 1, self.run, ())
            self.scheduler.run()

    def stop(self):

        self.scheduler.cancel()

    def run(self):

        # First check for finished simulations
        finished_list = check_for_finished_simulations()
    
        # If there are simulations ready ...
        for model in finished_list:    
            # First move data from all finished simulations
            # (so that pre-processing of next model can commence)
            # Post-processing will happen later
            if not model.status == 'failed':
                # Moving model input and output from job folder
                cosmos.log("Moving model " + model.long_name)
                model.move()
                # Delete job path
                fo.delete_folder(model.job_path)                
                model.status = "simulation_finished"
    
        # Now prepare new models ready to run        
        waiting_list = update_waiting_list()

        # Pre process all waiting simulations
        for model in waiting_list:
            
            cosmos.log("Pre-processing " + model.long_name + " ...")
            
            # Make job path and copy inputs
            fo.rmdir(model.job_path)
            fo.mkdir(model.job_path)
            src = os.path.join(model.path, "input", "*")
            fo.copy_file(src, model.job_path)

            # Also make model cycle paths
            fo.mkdir(model.cycle_path)
            fo.mkdir(model.cycle_input_path)
            fo.mkdir(model.cycle_output_path)
            fo.mkdir(model.cycle_figures_path)
            fo.mkdir(model.cycle_post_path)
            fo.mkdir(model.restart_flow_path)
            fo.mkdir(model.restart_wave_path)
                                        
            model.pre_process()  # Adjust model input (nesting etc.)

            if cosmos.config.run_mode == "serial":
                cosmos.log("Submitting " + model.long_name + " ...")
                model.submit_job()
            elif cosmos.config.run_mode == "parallel":
                cosmos.log("Ready to run " + model.long_name + " ...")
                # Write ready file            
                file_name = os.path.join(cosmos.config.job_path,
                                         cosmos.scenario.name,
                                         model.name,
                                         "ready.txt")
                fid = open(file_name, "w")
                fid.write("Model is ready to run")
                fid.close()
            
            model.status = "running"

        # Now do post-processing on simulations that were finished
        for model in finished_list:

            cosmos.log("Post-processing " + model.long_name + " ...")
            # Make plots etc.
            model.post_process()
            model.status = "finished"
            
            # Write finished file
            #later change to if cosmos.config.run_mode == "parallel":            
            try: 
                finished_file_name = os.path.join(model.cycle_output_path, "finished.txt")
                fid = open(finished_file_name, 'r')
                pcname = fid.read().splitlines()[1]
                fid.close()
                
                cosmos.log(model.long_name + " was run by " + pcname)
                
                file_name = os.path.join(cosmos.scenario.cycle_job_list_path,
                         model.name + ".finished")            
                fid = open(file_name, "w")
                fid.write("finished by " + pcname)
                fid.close()
                             
            except:
                file_name = os.path.join(cosmos.scenario.cycle_job_list_path,
                                         model.name + ".finished")            
                fid = open(file_name, "w")
                fid.write("finished")
                fid.close()

        
        # Now check if all simulations are completely finished    
        all_finished = True
        for model in cosmos.scenario.model:
            if model.status != "failed" and model.status != "finished":
                all_finished = False

        if all_finished:

            cosmos.log("All models finished!")

            # Post process data (making floodmaps, uploading to server etc.)
            post_process()

            self.status = "done"
                                    
            # Move log file to scenario cycle path               
            log_file = os.path.join(cosmos.config.main_path, "cosmos.log")
            fo.move_file(log_file, cosmos.scenario.cycle_path)
            
            # Delete jobs folder
            if cosmos.config.run_mode == "serial":
                pth = os.path.join(cosmos.config.job_path,
                                   cosmos.scenario.name)
                fo.rmdir(pth)

            if cosmos.config.cycle_mode == "continuous" and cosmos.next_cycle_time:
                # Start new main loop
                cosmos.main_loop.start(cycle_time=cosmos.next_cycle_time)
            else:
                cosmos.log("All done.")

        else:
            # Do another model loop 
            pass

def check_for_finished_simulations():
    
    finished_list = []
    
    for model in cosmos.scenario.model:
        if model.status == "running":
            file_name = os.path.join(model.job_path,
                                     "finished.txt")
            if os.path.exists(file_name):
                finished_list.append(model)
                              
    return finished_list

def update_waiting_list():

    # Check which models need to run next
    
    waiting_list = []
    priorities   = []
    running      = False

    # Check for all clusters if they are ready to run 
    for cl in cluster.values():
        cl.check_ready_to_run()
            
    for model in cosmos.scenario.model:

        if model.status == "waiting":
            # This model is waiting
            
            okay = True
            
            if model.flow_nested:
                if model.flow_nested.status != "finished":
                    okay = False
                if model.flow_nested.status == "failed":
                    model.status = "failed"
            if model.wave_nested:
                if model.wave_nested.status != "finished":
                    okay = False
                if model.wave_nested.status == "failed":
                    model.status = "failed"
                    
            if okay and model.cluster:
                # Model appears ready to run, and is member of a cluster
                # if not model.peak_boundary_twl:
                #     #  Peak boundary data has not yet been determined
                #     model.get_peak_boundary_conditions()
                if not cluster[model.cluster].ready:
                    # This model sits in a cluster that is not ready to run
                    okay = False
                                                
            if okay:
                waiting_list.append(model)
                priorities.append(model.priority)

        if model.status == "running":
            # There are model(s) running
            running = True

    if waiting_list:
        
        # Sort waiting list according to prioritization
        waiting_list.sort(key=lambda x: priorities, reverse = True)
        if cosmos.config.run_mode == "serial":
            # Only put first job in waiting list
            waiting_list = waiting_list[:1]        
            if running:
                # There is already a model running. Wait for it to finish.
                waiting_list = []
        elif cosmos.config.run_mode == "parallel":
            # Put all jobs at certain priority level in waiting list
            waiting_list = waiting_list[:]        

    return waiting_list
