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
try:
    from .cosmos_argo import Argo
except:
    print("Argo not available")
import cht.misc.fileops as fo

class ModelLoop():
    """Pre-process, submit, move, and post-process all models and initialize webviewer once all models are finished.

    Parameters
    ----------
    start : func
        Start running model loop with scheduler
    run : func
        Run model loop
    stop : func
        Stop model loop

    See Also
    -------
    cosmos.cosmos_main_loop.MainLoop
    cosmos.cosmos_model.Model
    cosmos.cosmos_beware.CoSMoS_BEWARE
    cosmos.cosmos_delft3dfm.CoSMoS_Delft3DFM
    cosmos.cosmos_hurrywave.CoSMoS_HurryWave
    cosmos.cosmos_sfincs.CoSMoS_SFINCS
    cosmos.cosmos_xbeach.CoSMoS_XBeach
    """
    def __init__(self):
        pass
        
    def start(self):
        """Start cosmos_model_loop.run with scheduler.

        See Also
        -------
        cosmos.cosmos_model_loop.ModelLoop.run
        """

        self.status = "running"
        while self.status == "running":        
            # This will be repeated until the status of the model loop changes to "done" 
            self.scheduler = sched.scheduler(time.time,
                                              time.sleep)
            if cosmos.config.run.run_mode == "cloud":
                dt = 20.0 # Execute the next model loop 1 second from now
            else:                
                dt = 1.0 # Execute the next model loop 1 second from now
            self.scheduler.enter(dt, 1, self.run, ())
            self.scheduler.run()

    def stop(self):
        """Stop cosmos_model_loop.
        """
        self.scheduler.cancel()

    def run(self):
        """ Run all cosmos models defined in the scenario file.

        - Check for finished simulations and move them to scenario folder
        - Make waiting list, prepare input and submit these models
        - Post process models from Step 1 (time series data)
        - Check if all models are finished. If true: make webviewer 

        See Also
        -------
        cosmos.cosmos_sfincs.CoSMoS_SFINCS.move
        cosmos.cosmos_sfincs.CoSMoS_SFINCS.pre_process
        cosmos.cosmos_model.Model.submit_job
        cosmos.cosmos_sfincs.CoSMoS_SFINCS.post_process
        """

        # First check for finished simulations (returns a list with model objects that just finished)
        finished_list = check_for_finished_simulations()
    
        # If there are simulations ready ...
        for model in finished_list:    
            # First move data from all finished simulations
            # (so that pre-processing of next model can commence)
            # Post-processing will happen later
            if not model.status == 'failed':
                if cosmos.config.run.run_mode == "cloud":
                    # Download job folder from cloud storage (ideally we do not need to do this, but then extraction of time series data needs to be done in the cloud as well)
                    # Alternatively, we could just download the his file for local post-processing
                    subfolder = cosmos.scenario.name + "/" + "models" + "/" + model.name + "/"
                    cosmos.cloud.download_folder("cosmos-scenarios",
                                                 subfolder,
                                                 model.job_path)
                # Moving files to input, output and restart folders
                cosmos.log("Moving model " + model.long_name)
                # First make folders
                fo.mkdir(model.cycle_input_path)
                fo.mkdir(model.cycle_output_path)
                # fo.mkdir(model.cycle_figures_path)
                fo.mkdir(model.cycle_post_path)
                # Call model specific move function (this will move new restart files to restart folder, inputs to input folder, and outputs to output folder)
                model.move()
                model.status = "simulation_finished"
    
        # Now prepare new models ready to run (returns a list with model objects that are ready to run)        
        waiting_list = update_waiting_list()

        # Pre process all waiting simulations
        for model in waiting_list:
            
            cosmos.log("Pre-processing " + model.long_name + " ...")
            
            # Make job path and copy inputs
            fo.rmdir(model.job_path)
            fo.mkdir(model.job_path)
            # Also make restart paths in scenario folder
            fo.mkdir(model.restart_flow_path)
            fo.mkdir(model.restart_wave_path)

            # Copy base inputs to job folder
            src = os.path.join(model.path, "input", "*")
            fo.copy_file(src, model.job_path)

            model.pre_process()  # Adjust model input (this happens in model.job_path)

            cosmos.log("Submitting " + model.long_name + " ...")
            model.status = "running"

            if model.ensemble:
                # In case of ensemble, we move all inputs to base_input subfolder
                fo.mkdir(os.path.join(model.job_path, "base_input"))
                fo.move_file(os.path.join(model.job_path, "*"), os.path.join(model.job_path, "base_input"))
                # Copy ensemble members file to job folder
                fo.copy_file(os.path.join(model.job_path, "base_input", "ensemble_members.txt"), model.job_path)
                # Copy run_job_2.py to job folder
                fo.copy_file(os.path.join(model.job_path, "base_input", "run_job_2.py"), model.job_path)
                # Copy config.yml to job folder
                fo.copy_file(os.path.join(model.job_path, "base_input", "config.yml"), model.job_path)
            
            # Time to submit the job
            # First prepare batch file
            if cosmos.config.run.run_mode == "cloud":
                # No need for a bach file. Workflow template will take care of different steps.
                pass
            else:  
                # Make windows batch file (run.bat) that activates the correct environment and runs run_job.py   
                fid = open(os.path.join(model.job_path, "run.bat"), "w")
                fid.write("@ echo off\n")
                fid.write("DATE /T > running.txt\n")
                fid.write('set CONDAPATH=' + cosmos.config.conda.path + '\n')
                if hasattr(cosmos.config.conda, "env"):
                    fid.write(r"call %CONDAPATH%\Scripts\activate.bat "+ cosmos.config.conda.env + "\n")
                else:
                    fid.write(r"call %CONDAPATH%\Scripts\activate.bat cosmos" + "\n")
                if model.ensemble:
                    fid.write("python run_job_2.py prepare_ensemble\n")
                    fid.write("python run_job_2.py simulate\n")
                    fid.write("python run_job_2.py merge_ensemble\n")
                    if not model.type == "beware":
                        fid.write("python run_job_2.py map_tiles\n")   
                    fid.write("python run_job_2.py clean_up\n")   
                else:
                    fid.write("python run_job_2.py simulate\n")
                    if not model.type == "beware":
                        fid.write("python run_job_2.py map_tiles\n")   
                fid.write("move running.txt finished.txt\n")

                #fid.write("exit\n")
                
                fid.close()

            # And now actually kick off this job
            if cosmos.config.run.run_mode == "serial":
                #or self.type=="beware":
                # Model needs to be run in serial mode (local on the job path of a windows machine)        
                cosmos.log("Writing tmp.bat in " + os.getcwd() + " ...")
                fid = open("tmp.bat", "w")
                fid.write(model.job_path[0:2] + "\n")
                fid.write("cd " + model.job_path + "\n")
                fid.write("call run.bat\n")
                fid.write("exit\n")
                fid.close()
                os.system('start tmp.bat')
                
            elif cosmos.config.run.run_mode == "cloud":
                cosmos.log("Ready to submit to Argo - " + model.long_name + " ...")
                s3key = cosmos.scenario.name + "/" + "models" + "/" + model.name
                tilesfolder = model.region + "/" + model.type + "/" + model.deterministic_name
#                webviewerfolder = cosmos.config.webviewer.name + "/data/" + cosmos.scenario.name + "/" + cosmos.cycle_string
                webviewerfolder = cosmos.config.webviewer.name + "/data"
                # Delete existing folder in cloud storage
                cosmos.log("Deleting model folder on S3 : " + model.name)
                cosmos.cloud.delete_folder("cosmos-scenarios", s3key)
                # Upload job folder to cloud storage
                cosmos.log("Uploading to S3 : " + s3key)
                cosmos.cloud.upload_folder("cosmos-scenarios",
                                           model.job_path,
                                           s3key)
                if model.ensemble:
                    # Should really make sure this all happens cosmos_cloud
                    cosmos.cloud.upload_folder("cosmos-scenarios",
                                               os.path.join(model.job_path, "base_input"),
                                               s3key + "/base_input")
                cosmos.log("Submitting template job : " + model.workflow_name)
                model.cloud_job = cosmos.argo.submit_template_job(
                    workflow_name=model.workflow_name, 
                    job_name=model.name, 
                    subfolder=s3key,
                    scenario=cosmos.scenario.name,
                    cycle=cosmos.cycle_string, 
                    webviewerfolder=webviewerfolder,
                    tilingfolder=tilesfolder
                    )


            elif cosmos.config.run.run_mode == "parallel":
                # Model will be run on WCP node, write file to jobs folder (WCP nodes will pick up this job)
                
                # Make directory in jobs folder (if non-existent) 
                os.makedirs(os.path.join(cosmos.config.path.jobs, cosmos.scenario.name), exist_ok=True)
                            
                # write file name containing job path to jobs folder
                file_name = os.path.join(cosmos.config.path.jobs, cosmos.scenario.name, f"{model.name}_{cosmos.cycle_string}.txt")
                fid = open(file_name, "w")
                fid.write(model.job_path)
                fid.close()

            else:
                print("No run mode defined, should be either serial, parallel or cloud")


        # Now do post-processing on simulations that were finished
        for model in finished_list:
            # For now, only extract time series data
            cosmos.log("Post-processing " + model.long_name + " ...")

            try:
                model.post_process()
                cosmos.log("Post-processing " + model.long_name + " done.")
            except Exception as e:
                print("An error occured while post-processing : " + model.name)
                print(f"Error: {e}")

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
            # Try to run post-processing. If it fails, print error message and continue.

            try:
                cosmos.webviewer.make()        
                if cosmos.config.run.upload:
                    current_path = os.getcwd()
                    try:
                        cosmos.webviewer.upload()
                    except:
                        print("An error occurred when uploading web viewer to server !!!")
                    os.chdir(current_path)
            except Exception as e:
                print("An error occured while making web viewer !")
                print(f"Error: {e}")

            self.status = "done"
                                    
            # Move log file to scenario cycle path               
            log_file = os.path.join(cosmos.config.path.main, "cosmos.log")
            fo.move_file(log_file, cosmos.scenario.cycle_path)
            
            # Delete jobs folder
            if cosmos.config.run.run_mode == "serial":
                pth = os.path.join(cosmos.config.path.jobs,
                                   cosmos.scenario.name)
                fo.rmdir(pth)

            # Check if we need to start a new cycle
            if cosmos.config.run.mode == "continuous" and cosmos.next_cycle_time:
                # Start new main loop
                cosmos.main_loop.start(cycle=cosmos.next_cycle_time)
            else:
                cosmos.log("All done.")

        else:
            # Do another model loop 
            pass

def check_for_finished_simulations():
    """Check if there finished simulations to be post-processed.
    """    
    finished_list = []
    
    for model in cosmos.scenario.model:
        try:
            if model.status == "running":
                if cosmos.config.run.run_mode == "cloud":
                    #TODO: Implement handling of failed workflow. What happens
                    #      when a workflow fails?
                    if Argo.get_task_status(model.cloud_job) != "Running":
                        finished_list.append(model)
                else:
                    file_name = os.path.join(model.job_path,
                                            "finished.txt")
                    if os.path.exists(file_name):
                        finished_list.append(model)
        except:
            print("An error occurred when checking job status!")                
                              
    return finished_list

def update_waiting_list():
    """Check which models can be run next according to their status and prioritization level.
    """
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
            if model.bw_nested:
                if model.bw_nested.status != "finished":
                    okay = False
                if model.bw_nested.status == "failed":
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
        if cosmos.config.run.run_mode == "serial":
            # Only put first job in waiting list
            waiting_list = waiting_list[:1]        
            if running:
                # There is already a model running. Wait for it to finish.
                waiting_list = []
        elif cosmos.config.run.run_mode == "parallel":
            # Put all jobs at certain priority level in waiting list
            waiting_list = waiting_list[:]        

    return waiting_list
