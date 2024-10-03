# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:02:04 2021

@author: ormondt
"""
import os

from .cosmos_main import cosmos
from cht_tsunami.tsunami import Tsunami

# Don't really need a class here, but what the heck. It may come in handy later and makes the code more like the other modules.
# Use super to inherit from the CHT Tsunami class.

class CoSMoS_Tsunami(Tsunami):

    def __init__(self):
        super().__init__()
    
    def generate_from_scenario(self, source_file):
        """Generate tsunami"""

        # Check if source file is full path or just filename
        if not os.path.isfile(source_file):
            # It is just a file name, so assume it is in the scenario/tsunami folder
            source_file = os.path.join(cosmos.scenario.path, "tsunami", source_file)

        self.read_fault_file(source_file)
        self.compute(smoothing=True, dx=1.0/60.0)

        output_file = os.path.join(cosmos.scenario.path, "tsunami", "tsunami.nc")
        self.write(output_file)

    # def read(self, output_file):
    #     output_file = os.path.join(cosmos.scenario.path, "tsunami", "tsunami.nc")
    #     ds = xr.open_dataset(output_file)
    #     return ds
