# CoSMoS package

Welcome to the GitHub repository of the Coastal Storm Modelling System

To export the cosmos environment to a yml file:

conda activate cosmos
conda env export --no-builds -f cosmos_environment.yml

To create the cosmos_environment.yml somewhere else: 

conda env create -f cosmos_environment.yml

To build the CoSMoS package, open Anaconda Powershell.

To make sure you have the latest version of build:

py -m pip install --upgrade build

and to build the package, e.g.: 

cd d:\checkouts\github\CoSMoS
py -m build

Upload to Pypi with:

cd d:\checkouts\github\CoSMoS
py -m pip install --upgrade twine
py -m twine upload dist/*

For an editable package, make the package with e.g.:

cd d:\checkouts\github\CoSMoS
pip install -e .

or something like:

pip install -e d:\checkouts\github\CoSMoS
