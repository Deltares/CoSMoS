.. _getting_started:

Getting started
=====

The page desribes the first steps to get started with CoSMoS. It includes the installation of the software and the running of a simulation.

Installation
------------

Git repositories
^^^^^^^^^^^^^^^^^

To use CoSMoS, first, a checkout/clone of two repositories is needed. First, the CoSMoS repository itself and secondly the CoastalHazardstoolkit repository.
This can be done using the following commands in Git Bash:

.. code-block:: none

    git clone https://github.com/Deltares/CoSMoS

.. code-block:: none

    git clone https://github.com/Deltares-research/CoastalHazardsToolkit.git


.. note:: 
    The CoastalHazardsToolkit repository is needed for the CoastalHazardsToolbox, which is used in CoSMoS. Access to Deltares-research is needed for both repositories.

Python environment
^^^^^^^^^^^^^^^^^

Secondly, make an Python environment in, for example, Anaconda such that the Python interpreter, libraries and scripts installed into it are isolated from the rest. Use the provided YAML file, ``environment_cosmos.yml``, to let Python install all the relevant libaries. 

.. code-block:: none

    conda env create -f d:\checkouts\Python\OpenEarthTools\cosmos\environment_cosmos.yml

Install CoSMoS and CoastalHazardsToolkit 
^^^^^^^^^^^^^^^^

After the Python environment is created, the CoSMoS and CoastalHazardsToolkit repositories can be installed in the python environment. This can be done by navigating to your local clones and running the following commands in the command prompt:

CoSMoS:
.. code-block:: none

    cd c:\git\cosmos​
    pip install -e 

CHT:
.. code-block:: none

    cd c:\git\coastalhazardstoolkit​
    pip install -e.


Running CoSMoS
------------
Before you can run CoSmoS, you will have to add it your path. You can alter the ``cosmos_add_paths()`` function. See also an example code below:

>>> # Import relevant libraries
>>> import sys
>>> import os
>>> 
>>> # Paths needs from cosmos
>>> mainpath    = r'd:\\checkouts\\Python\\OpenEarthTools\\cosmos\\'     # change this one
>>> variations  = ["cosmos", "delftdashboard", "bathymetry_database","gui_toolbox", "misc", "meteo", "delft3dfm", "hurrywave", "tiling", "sfincs"]
>>> sys.path.append(mainpath)
>>> for variation in variations:
>>>     path_file = os.sep.join([mainpath, variation])
>>>     #print(os.stat(path_file))
>>>     if os.path.isdir(path_file):
>>>         sys.path.append(path_file)
>>>     else:
>>>         print('path not found - ' + path_file) 
>>> # Other (extra) paths needed
>>> path_file = r'd:\\checkouts\\Python\\OpenEarthTools\\deltashell\\applications\\CoDeS\\CoDeS_2.0\\Tide\\pytides\\'
>>> if os.path.isdir(path_file):
>>>     sys.path.append(path_file)
>>> else:
>>>     print('path not found - ' + path_file) 


Running a simulation
----------------

Once CoSMoS is installed and added to your path, you can start a simulation! You can alter the ``run_cosmos()`` function. See also an example code below:

>>> from cosmos import cosmos
>>> # Run cosmos_addpaths.py before executing run_cosmos.py
>>> main_path       = "d:\\cosmos"
>>> scenario_name   = "hurricane_michael_gfs_spw"
>>> cosmos.initialize(main_path, scenario_name)
>>> # Run cosmos
>>> cosmos.run(mode="single_shot",
>>>           run_models=True,
>>>           make_flood_maps=True,
>>>           make_wave_maps=True,
>>>           get_meteo=True,
>>>           upload_data=False,
>>>           make_figures=True,
>>>           hurrywave_exe_path=r'd:\checkouts\Hurrywave\trunk\hurrywave\x64\Release',
>>>           sfincs_exe_path=r'd:\checkouts\SFINCS\branches\subgrid_openacc_11\sfincs\x64\Release',
>>>           ensemble=False)