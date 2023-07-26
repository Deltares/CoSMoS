import cht.misc.prob_maps as pm
import os

def find_subfolders(root_folder):
    subfolders = []
    for root, dirs, files in os.walk(root_folder):
        for dir_name in dirs:
            subfolder_path = os.path.join(root, dir_name)
            subfolders.append(subfolder_path)
    return subfolders

folder_path = '/data'

subfolders_list = find_subfolders(folder_path)

file_list = []

for subfolder in subfolders_list:
    file_list.append(os.path.join(folder_path, subfolder, "sfincs_his.nc"))

prcs= [0.05, 0.5, 0.95]
vars= ["point_zs"]
output_file_name = os.path.join("/output", "sfincs_his_ensemble.nc")
pm.prob_floodmaps(file_list=file_list, variables=vars, prcs=prcs, delete = False, output_file_name=output_file_name)
