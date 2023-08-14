# -*- coding: utf-8 -*-
"""
Created on Sat May 29 10:28:52 2021

@author: ormondt
"""

import os
#import numpy as np
#import pandas as pd
#import datetime

from .cosmos_main import cosmos
from .cosmos_webviewer import WebViewer
#from .cosmos_tiling import make_wave_map_tiles

def post_process():

    # if cosmos.config.make_figures:
    #     make_waterlevel_figure()
    
    if cosmos.config.webviewer:
        # Build new web viewer, or copy scenario data to existing viewer
        
        wv = WebViewer(cosmos.config.webviewer)
        wv.make()
        
        if cosmos.config.upload and os.path.isabs(cosmos.config.ftp_path):
            try:
                wv.copy_to_webviewer()
            except:
                print("An error occurred when uploading web viewer to server !!!")
        elif cosmos.config.upload:
            current_path = os.getcwd()
            try:
                wv.upload()
            except:
                print("An error occurred when uploading web viewer to server !!!")
            os.chdir(current_path)
