# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:02:04 2021

@author: ormondt
"""

import os
from matplotlib import cm

import cht.misc.xmlkit as xml
from .cosmos_main import cosmos
from cht.misc.misc_tools import rgb2hex

def read_config_file():
    
    main_path = cosmos.config.main_path
    
    config_file = os.path.join(main_path,
                               "configurations",
                               cosmos.config.config_file)
    
    # Defaults
    cosmos.config.ftp_hostname       = None
    cosmos.config.ftp_path           = None
    cosmos.config.ftp_username       = None
    cosmos.config.ftp_password       = None
    cosmos.config.webviewer_version  = None
    cosmos.config.sfincs_exe_path    = os.path.join(main_path, "exe", "sfincs")
    cosmos.config.hurrywave_exe_path = os.path.join(main_path, "exe", "hurrywave")
    cosmos.config.xbeach_exe_path    = os.path.join(main_path, "exe", "xbeach")
    cosmos.config.delft3dfm_exe_path = os.path.join(main_path, "exe", "delft3dfm")
    cosmos.config.beware_exe_path    = os.path.join(main_path, "exe", "beware")
    cosmos.config.cycle_interval     = 6
    cosmos.config.run_mode           = "serial"
    cosmos.config.forecast           = False
    cosmos.config.remove_old_cycles  = 0

    # Read xml config file
    xml_obj = xml.xml2obj(config_file)

    if hasattr(xml_obj, "ftp_hostname"):
        if hasattr(xml_obj.ftp_hostname[0],"value"):
            cosmos.config.ftp_hostname = xml_obj.ftp_hostname[0].value
    if hasattr(xml_obj, "ftp_path"):
        if hasattr(xml_obj.ftp_path[0],"value"):
            cosmos.config.ftp_path = xml_obj.ftp_path[0].value
    if hasattr(xml_obj, "ftp_username"):
        if hasattr(xml_obj.ftp_username[0],"value"):
            cosmos.config.ftp_username = xml_obj.ftp_username[0].value
    if hasattr(xml_obj, "ftp_password"):
        if hasattr(xml_obj.ftp_password[0],"value"):
            cosmos.config.ftp_password = xml_obj.ftp_password[0].value
    if hasattr(xml_obj, "webviewer_version"):
        cosmos.config.webviewer_version = xml_obj.webviewer_version[0].value
    if hasattr(xml_obj, "sfincs_exe_path"):
        cosmos.config.sfincs_exe_path = xml_obj.sfincs_exe_path[0].value
    if hasattr(xml_obj, "hurrywave_exe_path"):
        cosmos.config.hurrywave_exe_path = xml_obj.hurrywave_exe_path[0].value
    if hasattr(xml_obj, "xbeach_exe_path"):
        cosmos.config.xbeach_exe_path = xml_obj.xbeach_exe_path[0].value
    if hasattr(xml_obj, "delft3dfm_exe_path"):
        cosmos.config.delft3dfm_exe_path = xml_obj.delft3dfm_exe_path[0].value
    if hasattr(xml_obj, "cycle_interval"):
        cosmos.config.cycle_interval = xml_obj.cycle_interval[0].value
    if hasattr(xml_obj, "run_mode"):
        cosmos.config.run_mode = xml_obj.run_mode[0].value
    if hasattr(xml_obj, "remove_old_cycles"):
        cosmos.config.remove_old_cycles = xml_obj.remove_old_cycles[0].value

    # Map contours
    contour_file = os.path.join(main_path, "configurations", "map_contours.xml")
    xml_obj = xml.xml2obj(contour_file)
    cosmos.config.map_contours = []
    maps = xml_obj.tile_map
    for tm in maps:
        map_type = {}
        map_type["name"] = tm.name
        map_type["string"] = tm.legend_text[0].value
        map_type["contours"] = []
        if hasattr(tm, "contour"):
            for c in tm.contour:
                cnt = {}
                cnt["string"] = c.legend_text[0].value
                cnt["lower_value"] = c.lower[0].value
                cnt["upper_value"] = c.upper[0].value
                cnt["rgb"]   = c.rgb[0].value
                cnt["hex"]   = rgb2hex(tuple(cnt["rgb"]))
                
                map_type["contours"].append(cnt)
        elif hasattr(tm, 'rgb_file'):
            filename = tm.rgb_file[0].value
            # filename = r"p:\11206085-onr-fhics\03_cosmos\configurations\GMT_globe.txt"
            with open(filename) as f:
                array = []
                for line in f: # read rest of lines
                    array.append([float(x) for x in line.split()])
                    
            nsteps = len(array)        
            zmin = tm.lower[0].value
            zmax = tm.upper[0].value
            
            difference = zmax - zmin
            step = difference/nsteps
            
            for i in range(nsteps):

                zl = round(zmin + i*step,1)
                zu = round(zl + step,1)
                z  = round(zl + 0.5*step,1)
                
                rgb = []
                rgb.append(int(array[i][0]))
                rgb.append(int(array[i][1]))
                rgb.append(int(array[i][2]))
                cnt={}
                if i==0:
                    cnt["string"] = "< " + str(zmin)
                elif i==nsteps - 1:
                    cnt["string"] = "> " + str(zmax)
                else: 
                    cnt["string"] = str(zl) + " - " + str(zu)                    
                cnt["lower_value"] = zl
                cnt["upper_value"] = zu
                cnt["rgb"]   = rgb
                cnt["hex"]   = rgb2hex(tuple(rgb))

                map_type["contours"].append(cnt)
            
            map_type["contours"] = map_type["contours"][::-1]
            
        else:
            zmin = tm.lower[0].value
            zmax = tm.upper[0].value
            step = tm.step[0].value
            nsteps = int((zmax - zmin)/step) + 2
            for i in range(nsteps):

                zl = zmin + (i - 1)*step
                zu = zl + step
                z  = zl + 0.5*step
                zrel = (z - zmin + step)/(zmax + 0.5*step - zmin + 0.5*step)
                rgb0 = cm.jet(zrel)
                rgb = []
                rgb.append(int(rgb0[0]*255))
                rgb.append(int(rgb0[1]*255))
                rgb.append(int(rgb0[2]*255))
                cnt={}
                if i==0:
                    cnt["string"] = "< " + str(zmin)
                elif i==nsteps - 1:
                    cnt["string"] = "> " + str(zmax)
                else: 
                    cnt["string"] = str(zl) + " - " + str(zu)                    
                cnt["lower_value"] = zl
                cnt["upper_value"] = zu
                cnt["rgb"]   = rgb
                cnt["hex"]   = rgb2hex(tuple(rgb))

                map_type["contours"].append(cnt)
            
            map_type["contours"] = map_type["contours"][::-1]

        cosmos.config.map_contours.append(map_type)    
