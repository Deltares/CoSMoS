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
#import toml

from .cosmos import cosmos
#from .cosmos_meteo import read_meteo_sources
from .cosmos_meteo import download_and_collect_meteo
from .cosmos_track_ensemble import setup_track_ensemble


class MainLoop2:
    """Test
    """

    def __init__(self):
        # Try to kill all instances of main loop and model loop
        self.just_initialize = False  
