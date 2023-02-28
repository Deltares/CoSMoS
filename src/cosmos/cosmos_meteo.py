# -*- coding: utf-8 -*-
"""
Created on Tue May 25 14:28:58 2021

@author: ormondt
"""
import os
from pyproj import CRS
import numpy as np
import datetime

from .cosmos import cosmos
from cht.meteo.meteo import MeteoSource
from cht.meteo.meteo import MeteoGrid
import cht.misc.xmlkit as xml
import cht.misc.fileops as fo

def read_meteo_sources():
    
    # Read meteo sources
    cosmos.meteo_source = []
    cosmos.meteo_subset = []

    # These are hard-coded for now !
    src = MeteoSource("gfs_forecast_0p25",
                      "gfs_forecast_0p25",
                      "forecast",
                      crs=CRS.from_epsg(4326),
                      delay=6)
    cosmos.meteo_source.append(src)

    src = MeteoSource("gfs_anl_0p50",
                      "gfs_anl_0p50_04",
                      "analysis",
                      crs=CRS.from_epsg(4326))
    cosmos.meteo_source.append(src)

    src = MeteoSource("coamps_analysis",
                      "coamps_analysis",
                      "analysis",
                      crs=CRS.from_epsg(4326))
    cosmos.meteo_source.append(src)

    src = MeteoSource("coamps_tc_ufl_d01",
                      "coamps_tc_ufl_d01",
                      "forecast",
                      crs=CRS.from_epsg(4326),
                      delay=6,
                      cycle_interval=12,
                      time_interval=1)
    cosmos.meteo_source.append(src)

    src = MeteoSource("coamps_tc_hindcast",
                      "coamps_tc_hindcast",
                      "analysis",
                      crs=CRS.from_epsg(4326))
    cosmos.meteo_source.append(src)

    src = MeteoSource("coamps_tc_forecast",
                      "coamps_tc_forecast",
                      "forecast",
                      crs=CRS.from_epsg(4326),
                      delay=6,
                      time_interval=1)
    cosmos.meteo_source.append(src)

    src = MeteoSource("coamps_tc_retro_forecast",
                      "coamps_tc_retro_forecast",
                      "forecast",
                      crs=CRS.from_epsg(4326),
                      delay=6)
    cosmos.meteo_source.append(src)

    # Meteo subsets
    # Read from xml file
    xml_file = os.path.join(cosmos.config.path.main,
                            "meteo",
                            "meteo_subsets.xml")
    xml_obj = xml.xml2obj(xml_file)
    
    meteo_path = os.path.join(cosmos.config.path.main, "meteo")
    parameters = ["wind","barometric_pressure","precipitation"]
    
    has_source_list = []
    for xml_subset in xml_obj.meteo_subset:

        name       = xml_subset.name[0].value
        path       = os.path.join(meteo_path, name)
        srcname    = xml_subset.source[0].value
        # Look for matching source
        for src in cosmos.meteo_source:
            if srcname.lower() == src.name.lower():
                x_range = None
                y_range = None
                if hasattr(xml_subset,"x_range"):
                    x_range = xml_subset.x_range[0].value
                    y_range = xml_subset.y_range[0].value
                xystride = 1    
                tstride  = 1    
                if hasattr(xml_subset, "xystride"):
                    xystride = int(xml_subset.xystride[0].value)
                if hasattr(xml_subset, "tstride"):
                    tstride = int(xml_subset.tstride[0].value)
                subset = MeteoGrid(name=name,
                                   source=src,
                                   parameters=parameters,
                                   path=path,
                                   x_range=x_range,
                                   y_range=y_range,
                                   crs=src.crs,
                                   xystride=xystride,
                                   tstride=tstride)
                cosmos.meteo_subset.append(subset)
                break

    #  # Now get the other datasets (not mentioned in the subset xml file) 
    # data_names = []
    # data_list = fo.list_folders(os.path.join(meteo_path,"*"))
    # for data_path in data_list:
    #     data_names.append(os.path.basename(data_path))
     
def download_and_collect_meteo():
    # Loop through all available meteo subsets
    # Determine if the need to be downloaded
    # Get start and stop times for meteo data
    for meteo_subset in cosmos.meteo_subset:
        download = False
        t0      = datetime.datetime(2100,1,1,0,0,0)
        t1      = datetime.datetime(1970,1,1,0,0,0)
        for model in cosmos.scenario.model:
            if model.meteo_subset:
                if model.meteo_subset.name == meteo_subset.name:
                     download = True
#                         if model.flow:
                     t0 = min(t0, model.flow_start_time)
                     t1 = max(t1, model.flow_stop_time)
        if download:
            # Download the data
            if cosmos.config.cycle.get_meteo:
                cosmos.log("Downloading meteo data : " + meteo_subset.name)
                meteo_subset.download([t0, t1])
            # Collect the data from netcdf files    
            cosmos.log("Collecting meteo data : " + meteo_subset.name)
            meteo_subset.collect([t0, t1],
                                 xystride=meteo_subset.xystride,
                                 tstride=meteo_subset.tstride)
            if meteo_subset.last_analysis_time:
                cosmos.log("Last analysis time : " + meteo_subset.last_analysis_time.strftime("%Y%m%d_%H%M%S"))
                file_name = os.path.join(meteo_subset.path, meteo_subset.last_analysis_time.strftime("%Y%m%d_%Hz"), "coamps_used.txt")
                if os.path.exists(file_name):
                    cosmos.storm_flag = True
                    keepfile_name = os.path.join(cosmos.scenario.cycle_path, "keep.txt")
                    fid = open(keepfile_name, "w")  # Why is there no path here?
                    fid.write("Coamps data was used in this cycle so we want to keep it \n")
                    fid.close()
                else:
                    cosmos.storm_flag = False

def write_meteo_input_files(model, prefix, tref, path=None):
    
    if not path:
        path = model.job_path

    time_range = [model.flow_start_time, model.flow_stop_time]
    
    header_comments = False
    if model.type.lower() == "delft3dfm":
        header_comments = True
        
    # Check if the model uses 2d meteo forcing from weather model
    
    if model.meteo_subset:

        if model.crs.is_geographic:
        
            # Make a new subset that covers the domain of the model
            subset = model.meteo_subset.subset(xlim=model.xlim,
                                               ylim=model.ylim,
                                               time_range=time_range,
                                               crs=model.crs)
        
        else:
            dxy      = 5000.0
            x        = np.arange(model.xlim[0] - dxy, model.xlim[1] + dxy, dxy)
            y        = np.arange(model.ylim[0] - dxy, model.ylim[1] + dxy, dxy)
            subset   = model.meteo_subset.subset(x=x, y=y,
                                                 time_range=time_range,
                                                 crs=model.crs)
        
        # Check if meteo subset has data
        if subset:    
            if model.meteo_wind:                
                subset.write_to_delft3d(prefix,
                                        parameters=["wind"],
                                        path=path,
                                        refdate=tref,
                                        time_range=time_range,
                                        header_comments=header_comments)            
    
            if model.meteo_atmospheric_pressure:
                subset.write_to_delft3d(prefix,
                                        parameters=["barometric_pressure"],
                                        path=path,
                                        refdate=tref,
                                        time_range=time_range,
                                        header_comments=header_comments)
                            
            if model.meteo_precipitation:                
                subset.write_to_delft3d(prefix,
                                        parameters=["precipitation"],
                                        path=path,
                                        refdate=tref,
                                        time_range=time_range,
                                        header_comments=header_comments)
        
#     if model.meteo_spiderweb:
# #        model.domain.input.spwfile = model.meteo_spiderweb
# #        model.domain.input.baro    = 1
#         meteo_path = os.path.join(cosmos.config.main_path, "meteo", "spiderwebs")
#         src = os.path.join(meteo_path, model.meteo_spiderweb)
#         fo.copy_file(src, model.job_path)
    