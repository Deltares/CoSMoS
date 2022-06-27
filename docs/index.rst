.. coastal_hazards_toolkit documentation master file, created by
   sphinx-quickstart on Thu Mar 31 13:25:29 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the Coastal Hazards Toolkit's documentation!
========================================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

The Deltares Coastal Hazards Toolkit is a package of open-source Python modules used for modelling and data analysis of coastal environments.
It contains scripts for generating model inputs, importing bathymetry data, creating web tile layers, and much more.

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Installation
============

In order to use the Coastal Hazards Toolkit, you'll first need to install the package using pip:

.. code-block:: console

   pip install deltares-coastalhazardstoolkit

or alternatively, if you have an OpenEarth account and checkout folder, install it as an editable package:

.. code-block:: console

   cd OpenEarthTools/trunk/python/applications/coastalhazardstoolkit/trunk
   pip install -e .

   
.. toctree::
   
   bathymetry  
   meteo  
   tiling  
   tropical_cyclones
   nesting
   delft3dfm
   sfincs
   xbeach
   hurrywave   
