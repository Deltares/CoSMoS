# To create the cosmos environment, do the following:
#
# set $gitpath below to the folder that contains your git repositories
# open conda powershell
# cd to the folder that contains this script
# ./mkenv_cosmos.ps1

$gitpath = "c:\github"

conda create -n cosmos python=3.11 pip
conda activate cosmos
pip install -e $gitpath\cosmos
pip install -e $gitpath\hydromt_sfincs
pip install -e $gitpath\hydromt-hurrywave
pip install -e $gitpath\cht_utils
pip install -e $gitpath\cht_physics
pip install -e $gitpath\cht_bathymetry
pip install -e $gitpath\cht_tsunami
pip install -e $gitpath\cht_tide
pip install -e $gitpath\cht_cyclones
pip install -e $gitpath\cht_meteo
pip install -e $gitpath\cht_sfincs
pip install -e $gitpath\cht_hurrywave
pip install -e $gitpath\cht_delft3dfm
pip install -e $gitpath\cht_beware
pip install -e $gitpath\cht_xbeach
pip install -e $gitpath\cht_nesting
pip install -e $gitpath\cht_tiling
pip install boto3