# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:02:04 2021

@author: ormondt
"""

import os
from matplotlib import cm
import numpy as np

import cht.misc.xmlkit as xml
from .cosmos_main import cosmos
from cht.misc.misc_tools import rgb2hex

def read_config_file():
    
    main_path = cosmos.config.main_path
    config_path = os.path.join(main_path,
                               "configurations")
    
    config_file = os.path.join(config_path,
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
    cosmos.config.no_coamps          = False

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
    if hasattr(xml_obj, "no_coamps"):
        cosmos.config.no_coamps = xml_obj.no_coamps[0].value

    # Map contours
    contour_file = os.path.join(config_path, "map_contours.xml")
    xml_obj = xml.xml2obj(contour_file)
    cosmos.config.map_contours = []
    maps = xml_obj.tile_map
    for tm in maps:
        map_type = {}
        map_type["name"] = tm.name
        map_type["string"] = tm.legend_text[0].value
        map_type["contours"] = []
        if not hasattr(tm, "scale"):
            scale = "linear"
        else:
            scale = tm.scale[0].value
        
        if hasattr(tm, "contour"):

            # Contours are provided

            for c in tm.contour:
                cnt = {}
                cnt["string"] = c.legend_text[0].value
                cnt["lower_value"] = c.lower[0].value
                cnt["upper_value"] = c.upper[0].value
                cnt["rgb"]   = c.rgb[0].value
                cnt["hex"]   = rgb2hex(tuple(cnt["rgb"]))
                
                map_type["contours"].append(cnt)
        else:

            # Contours from contour map in config folder

            filename = os.path.join(config_path, tm.color_map[0].value + ".txt")

            vals  = np.loadtxt(filename)
            nrows = np.shape(vals)[0]
            ncols = np.shape(vals)[1]
            if ncols==4:
                v = np.squeeze(vals[:,0])
                r = np.squeeze(vals[:,1])
                g = np.squeeze(vals[:,2])
                b = np.squeeze(vals[:,3])
            else:    
                v = np.arange(0.0, 1.000001, 1.0/(nrows-1))
                r = np.squeeze(vals[:,0])
                g = np.squeeze(vals[:,1])
                b = np.squeeze(vals[:,2])
                
            if scale == "linear":    
                    
                zmin = tm.lower[0].value
                zmax = tm.upper[0].value
                step = tm.step[0].value
                nsteps = round((zmax-zmin)/step + 2)    
                
                for i in range(nsteps):
                    
                    # Interpolate
                    zl = zmin + (i - 1)*step
                    zu = zl + step
                    z  = i/((nsteps - 1)*1.0)
                    rr = round(np.interp(z, v, r))
                    gg = round(np.interp(z, v, g))
                    bb = round(np.interp(z, v, b))                
                    rgb = [rr, gg, bb]
    
                    cnt={}
                    if i==0:
                        cnt["string"] = "< " + str(zmin)
                        cnt["lower_value"] = -1.0e6
                        cnt["upper_value"] = zu
                    elif i==nsteps - 1:
                        cnt["string"] = "> " + str(zmax)
                        cnt["lower_value"] = zl
                        cnt["upper_value"] = 1.0e6
                    else: 
                        cnt["string"] = str(zl) + " - " + str(zu)                    
                        cnt["lower_value"] = zl
                        cnt["upper_value"] = zu
                    cnt["rgb"]   = rgb
                    cnt["hex"]   = rgb2hex(tuple(rgb))
    
                    map_type["contours"].append(cnt)
                
            else:
                
                # Logarithmic

                zmin = tm.lower[0].value
                zmax = tm.upper[0].value

                if scale == "log125":
                    nit = 10
                    zz  = np.zeros(nit*3)
                    k = -1
                    for i in range(nit):
                        k = k + 1
                        if i==0:
                            zz[k] = 1.0e-4
                        else:    
                            zz[k] = zz[k - 1] * 2                        
                        k = k + 1
                        zz[k] = zz[k - 1] * 2
                        k = k + 1
                        zz[k] = zz[k - 1]*2.5
                elif scale == "log16":       
                    nit = 10
                    zz  = np.zeros(nit*5)
                    k = -1
                    for i in range(nit):
                        k = k + 1
                        # 0.1
                        if i==0:
                            zz[k] = 1.0e-4
                        else:    
                            zz[k] = zz[k - 1] * 100 / 65                        
                        k = k + 1
                        # 0.15
                        zz[k] = zz[k - 1] * 3 / 2
                        k = k + 1
                        # 0.25
                        zz[k] = zz[k - 1]*5/3
                        k = k + 1
                        # 0.40
                        zz[k] = zz[k - 1]*8/5
                        k = k + 1
                        # 0.65
                        zz[k] = zz[k - 1]*65/40
                elif scale == "log16":       
                    nit = 10
                    zz  = np.zeros(nit*5)
                    k = -1
                    for i in range(nit):
                        k = k + 1
                        # 0.1
                        if i==0:
                            zz[k] = 1.0e-4
                        else:    
                            zz[k] = zz[k - 1] * 100 / 65                        
                        k = k + 1
                        # 0.15
                        zz[k] = zz[k - 1] * 3 / 2
                        k = k + 1
                        # 0.25
                        zz[k] = zz[k - 1]*5/3
                        k = k + 1
                        # 0.40
                        zz[k] = zz[k - 1]*8/5
                        k = k + 1
                        # 0.65
                        zz[k] = zz[k - 1]*65/40
                elif scale == "log121":
                    #1 1.2 1.5 1.8 2.2 2.6 3.2 3.8 4.6 5.5 6.8 8.2 10
                    nit = 10
                    zz  = np.zeros(nit*12)
                    k = -1
                    for i in range(nit):
                        k = k + 1
                        # 0.1
                        if i==0:
                            zz[k] = 1.0e-4
                        else:    
                            zz[k] = zz[k - 1] * 50 / 41                        
                        # 1.2
                        k = k + 1
                        zz[k] = zz[k - 1] * 6 / 5 
                        # 1.5
                        k = k + 1
                        zz[k] = zz[k - 1] * 5 / 4 
                        # 1.8
                        k = k + 1
                        zz[k] = zz[k - 1] * 6 / 5 
                        # 2.2
                        k = k + 1
                        zz[k] = zz[k - 1] * 11 / 9
                        # 2.6
                        k = k + 1
                        zz[k] = zz[k - 1] * 13 / 11
                        # 3.2
                        k = k + 1
                        zz[k] = zz[k - 1] * 16 / 13
                        # 3.8
                        k = k + 1
                        zz[k] = zz[k - 1] * 19 / 16
                        # 4.6
                        k = k + 1
                        zz[k] = zz[k - 1] * 23 / 19
                        # 5.5
                        k = k + 1
                        zz[k] = zz[k - 1] * 55 / 46
                        # 6.8
                        k = k + 1
                        zz[k] = zz[k - 1] * 68 / 55
                        # 8.2
                        k = k + 1
                        zz[k] = zz[k - 1] * 41 / 34

                    
                i0 = np.where(zz>=zmin - 1.0e-6)[0][0]
                i1 = np.where(zz>=zmax - 1.0e-6)[0][0]
                
                nsteps = i1 - i0 + 1
                
                k = -1
                for i in range(i0, i1 + 1):

                    k = k + 1
                    
                    # Interpolate
                    z  = k/((nsteps - 1)*1.0)
                    rr = round(np.interp(z, v, r))
                    gg = round(np.interp(z, v, g))
                    bb = round(np.interp(z, v, b))                
                    rgb = [rr, gg, bb]
    
                    # cnt={}
                    # if k==0:
                    #     cnt["string"] = "< " + str(zmin)
                    #     cnt["lower_value"] = -1.0e6
                    #     cnt["upper_value"] = zz[i]
                    # elif i==nsteps - 1:
                    #     cnt["string"] = "> " + str(zmax)
                    #     cnt["lower_value"] = zz[i]
                    #     cnt["upper_value"] = 1.0e6
                    # else: 
                    #     cnt["string"] = str(zz[i]) + " - " + str(zz[i + 1])                    
                    #     cnt["lower_value"] = zz[i]
                    #     cnt["upper_value"] = zz[i + 1]
                    cnt={}
                    if k==0:
                        cnt["string"] = "< " + f"{zmin:.1f}"
                        cnt["lower_value"] = -1.0e6
                        cnt["upper_value"] = zz[i]
                    elif k==nsteps - 1:
                        cnt["string"] = "> " +  f"{zmax:.1f}"
                        cnt["lower_value"] = zz[i]
                        cnt["upper_value"] = 1.0e6
                    else: 
                        cnt["string"] = f"{zz[i - 1]:.1f}" + " - " + f"{zz[i]:.1f}"                   
                        cnt["lower_value"] = zz[i - 1]
                        cnt["upper_value"] = zz[i]
                    cnt["rgb"]   = rgb
                    cnt["hex"]   = rgb2hex(tuple(rgb))
    
                    map_type["contours"].append(cnt)

            
            map_type["contours"] = map_type["contours"][::-1]
            
        cosmos.config.map_contours.append(map_type)    
