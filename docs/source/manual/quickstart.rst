.. _quickstart:

Getting started
---------------

This section walks you through installing CoSMoS and running your first scenario.

Step 1: Install CoSMoS
^^^^^^^^^^^^^^^^^^^^^^

CoSMoS depends on a set of Deltares packages (``cht_*``, ``hydromt_sfincs``,
``hydromt-hurrywave``) that are installed from source alongside CoSMoS itself.
Two PowerShell scripts in the repository do this for you. Both assume the
repositories live in ``c:\github``; edit the paths in the scripts if you use a
different folder.

1. Clone CoSMoS and its dependencies. Download
   :repo:`clone_repos_cosmos.ps1` and run it from a conda PowerShell prompt::

       ./clone_repos_cosmos.ps1

2. Create the ``cosmos`` conda environment (Python 3.11) and install all
   packages in editable mode with :repo:`mkenv_cosmos.ps1`::

       cd c:\github\cosmos
       ./mkenv_cosmos.ps1

3. Activate the environment and check that CoSMoS can be imported::

       conda activate cosmos
       python -c "from cosmos import cosmos"

.. note::

   Running ``pip install -e .`` in the CoSMoS folder alone installs CoSMoS
   but none of its dependencies.

The model executables (SFINCS, HurryWave, Delft3D FM, XBeach, BEWARE) are not
part of this installation. Install the ones you need separately and point to
them in the configuration file (Step 4).

Step 2: Set up a run folder
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Copy the template folder :repo:`cosmos_run_folder` from your local CoSMoS
repository to the location where you want to run CoSMoS (feel free to rename
it). The folder contains templates for the ``run_folder`` and the
``meteo_database``, together with the example script ``run_cosmos.py``. Also create
an empty ``model_database`` folder (path to specify in Step 4); you will fill it in Step 3.

Step 3: Add models to the model database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:ref:`Add wave and/or flow models <models>` for your domain of interest to the
``model_database`` folder.

Step 4: Configure paths
^^^^^^^^^^^^^^^^^^^^^^^

Edit ``configuration/config.toml`` (see :ref:`Configuration <configuration>`):

- Set the model executable paths for the models you want to run.
- Set the ``model_database`` and ``meteo_database`` paths.

Step 5: Set up a scenario
^^^^^^^^^^^^^^^^^^^^^^^^^

Create a :ref:`scenario file <scenario>` (``scenarios/<name>/scenario.toml``)
describing which models to run, for which period, and with which meteorological
data. For a first run, choose one of the meteorological data options listed in
the meteo database (see :ref:`Meteo <meteo>`).

You can also add observation stations (see :ref:`Observation stations <stations>`)
to compare model results with measurements.

Step 6: Run CoSMoS
^^^^^^^^^^^^^^^^^^^

Once you have completed steps 1 to 5, you can :ref:`execute your first CoSMoS run <running>`.
Output is stored in the scenario folder and can be viewed in the
:ref:`web viewer <webviewer>`.

Advanced configuration
^^^^^^^^^^^^^^^^^^^^^^

**Step 7: Add observation data.**
In addition to NOAA CO-OPS tide stations (fetched automatically), you can
:ref:`manually add observation station locations and data <stations>`.

**Step 8: Add meteorological data.**
There are several options to manually include meteorological data
(see :ref:`Meteo <meteo>`): regularly gridded forcing, spiderweb files, or
cyclone track ensembles for probabilistic predictions.

**Step 9: Organize models in super regions.**
For large model databases, you can group models into
:ref:`super region files <super_regions>` and reference them efficiently in your
scenario file.
