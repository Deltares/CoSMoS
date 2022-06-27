# -*- coding: utf-8 -*-
"""
Spyder Editor

@author: goede_rl
"""
import time
import sched
import os

import psutil
from random import random

class CosmosRunParallel:
    
    def __init__(self):
        running = 0
        for i in psutil.process_iter():
           if "cmd.exe" in i.name():
               running = running + 1
        self.running = running
    
    def start(self, job_path,local_path):    

        self.status = "searching"
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
                if attempts > 10:
                    self.status = "finished"
                    print("All models finished")
                else:
                    continue
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
           if "cmd.exe" in i.name():
               running = running + 1
               
        if running == self.running:
            # model_list = [ f.path for f in os.scandir(self.job_path) if f.is_dir() ]
            model_list = [ f.name for f in os.scandir(self.job_path) if f.is_dir() ]
        
            for model in model_list:
                #
                file_name = os.path.join(self.job_path,model,
                                         "ready.txt")
                       
                if os.path.exists(file_name):
                    os.remove(file_name)
                    
                    # Make run batch file
                    fid = open("tmp.bat", "w")
                    fid.write("mkdir " + os.path.join(self.local_path,model) + "\n")
                    fid.write("xcopy " + os.path.join(self.job_path,model) + " " + os.path.join(self.local_path,model) + " /E /Q /Y" + "\n")
                    fid.write(self.local_path[0:2] + "\n")
                    fid.write("cd " + os.path.join(self.local_path,model) + "\n")
                    fid.write("call run.bat\n")
                    fid.write("move finished.txt finished_local.txt" + " \n")
                    fid.write("xcopy " + os.path.join(self.local_path,model) + " " + os.path.join(self.job_path,model) + " /E /Q /Y" + "\n")
                    fid.write(self.job_path[0:2] + "\n")
                    fid.write("cd " + os.path.join(self.job_path,model) + "\n")
                    fid.write("move finished_local.txt finished.txt" + " \n")
                    fid.write("rmdir " + os.path.join(self.local_path,model) + " /s /q" + "\n")
                    fid.write("exit\n")
                    fid.close()
                    
                    os.system('start tmp.bat')
                    print("Running " + model)
                    break
                    
                
    def move_file(src, dst):
        import shutil
        import glob
        
        for full_file_name in glob.glob(src):
            src_name = os.path.basename(full_file_name)        
            if os.path.exists(os.path.join(dst, src_name)):
                os.remove(os.path.join(dst, src_name))
            shutil.move(full_file_name, dst)
