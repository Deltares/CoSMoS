# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 15:29:34 2023

@author: maartenvanormondt
"""
import os
import toml
import cht.misc.xmlkit as xml

name = "hurricane_laura_03"
path = os.path.join("c:\\work\\cosmos\\run_folder\\scenarios\\", name)
xml_file = os.path.join(path, name + ".xml")
tml_file = os.path.join(path, "scenario.toml")
xml_obj = xml.xml2obj(xml_file)

scenario = {}
scenario["model"] = []

dct = xml_obj.__dict__
for key in dct:
    valobj = getattr(xml_obj, key)
    if key == "model":
        for model in valobj:
            mdl = {}
            dct2 = model.__dict__
            for key2 in dct2:
                valobj2 = getattr(model, key2)
                val2 = valobj2[0].value
                mdl[key2] = val2
            scenario["model"].append(mdl)    
    else:
        val = valobj[0].value
    
        if key == "name":
            key = None
    
        if key == "longname":
            key = "long_name"
    
        if key == "type" or key == "cluster":
            val = val.lower()
    
        if val == "no":
            val = False
        elif val == "yes":   
            val = True    
    
        if key == "priority":
            key = None
    
        if key == "flowspinup":
            if val != "none":
                key = "flow_spinup_time"
            else:
                key = None
    
        if key == "wavespinup":
            if val != "none":
                key = "wave_spinup_time"
            else:
                key = None
    
        if key == "flownested":
            if val != "none":
                key = "flow_nested"
            else:
                key = None
    
        if key == "wavenested":
            if val != "none":
                key = "wave_nested"
            else:
                key = None
        if key == "coordsys":
            key = "crs"
        if key == "coordsystype":
            key = None
                
            
                
        # # Read polygon around model
        # polygon_file  = os.path.join(self.path, "misc", self.name + ".txt")
        # if os.path.exists(polygon_file):
        #     df = pd.read_csv(polygon_file, index_col=False, header=None,
        #          delim_whitespace=True, names=['x', 'y'])
        #     xy = df.to_numpy()
        #     self.polygon = path.Path(xy)
        #     if not self.xlim:
        #         self.xlim = [self.polygon.vertices.min(axis=0)[0],
        #                      self.polygon.vertices.max(axis=0)[0]]
        #         self.ylim = [self.polygon.vertices.min(axis=0)[1],
        #                      self.polygon.vertices.max(axis=0)[1]]
           
        # # Stations
        # if hasattr(xml_obj, "station"):
    
        #     for istat in range(len(xml_obj.station)):
                
        #         # Find matching stations from complete stations list
    
        #         name = xml_obj.station[istat].value
        #         self.add_stations(name)
    
    
        if key:
            scenario[key] = val

ccc = {}
ccc["scenario"] = scenario
with open(tml_file, "w") as f:
    new_toml_string = toml.dump(scenario, f)
    
    
    
xxx = toml.load(tml_file)
pass    