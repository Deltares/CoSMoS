# To create the cosmos environment, do the following:
#
# open conda powershell
# cd c:\work\cosmos\run_folder
# ./mkenv.ps1

conda create -n cosmos python=3.11 pip
conda activate cosmos
pip install -e c:\github\cosmos
pip install -e c:\github\hydromt_sfincs
pip install -e c:\github\hydromt-hurrywave
pip install -e c:\github\cht_utils
pip install -e c:\github\cht_physics
pip install -e c:\github\cht_bathymetry
pip install -e c:\github\cht_tsunami
pip install -e c:\github\cht_tide
pip install -e c:\github\cht_cyclones
pip install -e c:\github\cht_meteo
pip install -e c:\github\cht_sfincs
pip install -e c:\github\cht_hurrywave
pip install -e c:\github\cht_delft3dfm
pip install -e c:\github\cht_beware
pip install -e c:\github\cht_xbeach
pip install -e c:\github\cht_nesting
pip install -e c:\github\cht_tiling
pip install boto3
