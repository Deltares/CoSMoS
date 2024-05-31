# -*- coding: utf-8 -*-
"""
Spyder Editor

@author: goede_rl
"""
import time
import sched
import os
import socket
import shutil

import psutil
from random import random
   
class CosmosRunParallel:
    
    def __init__(self):
        running = 0
        for i in psutil.process_iter():
           if "cmd.exe" in i.name():
               running = running + 1
        self.running = running
    
    def start(self, job_path, local_path, scenario):    

        self.status = "searching"
        if scenario is not None:
            self.job_path = os.path.join(job_path, scenario)
        else:
            self.job_path = job_path
        
        self.local_path = local_path
        attempts = 0
        while self.status == "searching":
            # This will be repeated until the status of the model loop changes to "done" 
            self.scheduler = sched.scheduler(time.time, time.sleep)
            dt = random() * 10.0 # Execute the next model loop ... seconds from now
            if not os.path.exists(job_path):
                attempts += 1
                time.sleep(10)
                print("Attempt " + str(attempts) + " to find jobs-folder")
                if attempts > 100:
                    self.status = "finished"
                    print("All models finished")
                else:
                    continue
            else:
                # First check whether we still want to continue running, or want to kill all simulations
                if os.path.exists(os.path.join(job_path, "kill_all.txt")):
                    os.system('taskkill /fi "WINDOWTITLE eq Running CoSMoS"')
                else:
                    attempts = 0
                    self.scheduler.enter(dt,1,self.run,())
                    self.scheduler.run()
            
    def stop(self):
        self.scheduler.cancel()

    def run(self):
        #first check whether something is running already
        running = 0
        for i in psutil.process_iter():
            try:
                if "cmd.exe" in i.name():
                    running = running + 1
            except Exception as e:
                print(str(e))
            
        if running == self.running:
            try:
                # Get a list of all .txt files recursively
                model_name_list = []
                job_path_list = []

                for dirpath, dirnames, filenames in os.walk(self.job_path):
                    for filename in filenames:
                        if filename.endswith('.txt'):
                            model_name_list.append(filename)
                            job_path_list.append(os.path.join(dirpath, filename))
            except:
                time.sleep(10)
                return None
            
            for ijob, job_path in enumerate(job_path_list):
                model_name = model_name_list[ijob].split('.')[0]

                if os.path.exists(job_path):
                    try:
                        fid = open(job_path, "r")
                        model_path = fid.read()
                        fid.close()
                        os.remove(job_path)
                    except:
                        # model is already been copied to another instance
                        continue
                    
                    # Copy remote folder to local copy
                    shutil.copytree(os.path.join(model_path), os.path.join(self.local_path, model_name))
                    
                    # Check if files in folder exist
                    files_local = os.listdir(os.path.join(self.local_path, model_name))
                    if len(files_local) == 0:
                        time.sleep(5)
                        try:
                            shutil.copytree(os.path.join(model_path), os.path.join(self.local_path, model_name), exist_ok = True)
                        except Exception as e:
                            print(str(e))
                            
                    fid = open("tmp.bat", "w")
                    fid.write(self.local_path[0:2] + "\n")
                    fid.write("cd " + os.path.join(self.local_path, model_name) + "\n")
                    fid.write("call run.bat\n")
                    fid.write("move finished.txt finished_local.txt" + " \n")
                    fid.write("echo " + socket.gethostname() + ">> finished_local.txt"  + " \n" )
                    fid.write("xcopy " + os.path.join(self.local_path, model_name) + " " + os.path.join(model_path) + " /E /Q /Y" + "\n")
                    fid.write(model_path[0:2] + "\n")
                    fid.write("cd " + os.path.join(model_path) + "\n")
                    fid.write("move finished_local.txt finished.txt" + " \n")
                    fid.write("rmdir " + os.path.join(self.local_path, model_name) + " /s /q" + "\n")
                    fid.write("exit\n")
                    fid.close()
                        
                    os.system('start tmp.bat')
                    print("Running " + model_name)
                    break



