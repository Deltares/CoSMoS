.. _quickstart:

Quickstart CoSMoS
------------

To setup CoSMoS for your area of interest, you can broadly follow these steps:

**Step 1: Install CoSMoS**

Install CoSMoS on your device (:ref:`Getting started <getting_started>`).

**Step 2: Make a local copy the CoSMoS run folder.**

Copy the default CoSMoS run folder (*cosmos_run_folder* in your CoSMoS installation folder) to the folder where you intend to run CoSMoS.

**Step 3: Add models to the model database.**

Add wave and/or flow models for your domain of interest (:ref:`Adding models <adding_models>`).

**Step 4: Adjust your model executable paths.**

In the *configurations* folder, you can find the file *default.xml*. 
Adjust the model executable paths (for the models that you want to be running) to your local installations.

**Step 5: Setup a scenario file.**

Setup a scenario file (see :ref:`Scenario <scenario>`), in which you describe which models of your model database you want to run, 
for which period, and with which metereological data. 
For a first CoSMoS run, choose one of the meteoreological data options listed in the default *meteo_subsets* file (see :ref:`Meteo <meteo>`).
You can also add the NOAA-COOPS tide station file (see :ref:`Observation stations <stations>`) to your scenario file to compare observed and computed water levels.

**Step 6: Run CoSMoS.**

Once you have completed Step 1 to 5, you can execute a first CoSMoS run (see :ref:`Running CoSMoS <running>`). 
The output is stored in the scenario file, and you can view the results of your run in the  webviewer (see :ref:`Output <output>`)

Advanced CoSMoS configurations:
^^^^^^^^^^^^

**Step 7: Add observation data.**

In addition to the regular NOAA-COOPS tide stations, for which water level data is downloaded automatically from a server, 
you can manually add observation station locations and data (see :ref:`Observation stations <stations>`).

**Step 8: Add meteoreological data.**

There are several options to manually include meteorological data to force your model(s) (see :ref:`Meteo <meteo>`). 
You can generate your own evenly gridded meteorological forcing or include a spiderweb file. 
Alternatively, you can create an ensemble of cyclone tracks to obtain a probabilistic hazard prediction.

**Step 9: Organize your models in a super region file.**

If you have created a large database of models and want to include them efficiently in your scenario file, 
you can organize the models in a *super region* file (see :ref:`Super regions <super_regions>`). Instead of calling all models in the scenario file, you now call this 
*super region* file.  


