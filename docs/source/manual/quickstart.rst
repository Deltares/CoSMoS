.. _quickstart:

Getting started
---------------

This section walks you through installing CoSMoS and running your first scenario.

Step 1: Install CoSMoS
^^^^^^^^^^^^^^^^^^^^^^

Clone the repository and install in editable mode::

    git clone https://github.com/Deltares/CoSMoS.git
    cd CoSMoS
    pip install -e .

Step 2: Set up a run folder
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Copy the default folders ``run_folder``, ``model_database``, and
``meteo_database`` from the CoSMoS installation to the location where you want
to run CoSMoS.

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

.. include:: examples/run_cosmos.py
       :literal:

Once you have completed steps 1 to 5, you can :ref:`execute your first CoSMoS run <running>`.
Output is stored in the scenario folder and can be viewed in the
:ref:`web viewer <webviewer>`.

Advanced configuration
^^^^^^^^^^^^^^^^^^^^^^

**Step 7: Add observation data.**
In addition to NOAA CO-OPS tide stations (downloaded automatically), you can
:ref:`manually add observation station locations and data <stations>`.

**Step 8: Add meteorological data.**
There are several options to manually include meteorological data
(see :ref:`Meteo <meteo>`): regularly gridded forcing, spiderweb files, or
cyclone track ensembles for probabilistic predictions.

**Step 9: Organize models in super regions.**
For large model databases, you can group models into
:ref:`super region files <super_regions>` and reference them efficiently in your
scenario file.
