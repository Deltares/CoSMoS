.. _quickstart:

Quickstart CoSMoS
------------

To setup CoSMoS for your area of interest, you:

**Step 1: Install CoSMoS**

:ref:`Install CoSMoS <getting_started>` on your device.

**Step 2: Make a local copy of the CoSMoS run folder.**

Copy the default folders *cosmos_run_folder*, *model_database*, and *meteo_database* from your CoSMoS installation folder to the folder where you want to run CoSMoS.

**Step 3: Add models to the model database.**

:ref:`Add wave and/or flow models <models>` for your domain of interest.

**Step 4: Adjust your model executable paths.**

In the *configuration* folder, you can find the file :ref:`*config.toml* <configuration>`. 
Adjust the model executable paths (for the models that you want to be running) to your local installations. 
Also, make sure to link to the correct *model_database* and *meteo_database* folders.

**Step 5: Setup a scenario file.**

:ref:`Setup a scenario file <scenario>` in which you describe which models of your model database you want to run, 
for which period, and with which metereological data. 
For a first CoSMoS run, choose one of the meteoreological data options listed in the default *meteo_subsets* file (see :ref:`Meteo <meteo>`).
You can also add the NOAA-COOPS tide station file (see :ref:`Observation stations <stations>`) to your scenario file to compare observed and computed water levels.

**Step 6: Run CoSMoS.**

Once you have completed Step 1 to 5, you can :ref:`execute a first CoSMoS run <running>`. 
The output is stored in the scenario folder, and you can view the results of your run in the  webviewer (see :ref:`Output <output>`)

Advanced CoSMoS configurations:
^^^^^^^^^^^^

**Step 7: Add observation data.**

In addition to the regular NOAA-COOPS tide stations, for which water level data is downloaded automatically from a server, 
you can :ref:`manually add observation station locations and data <stations>`.

**Step 8: Add meteoreological data.**

There are several options to manually include meteorological data to force your model(s) (see :ref:`Meteo <meteo>`). 
You can generate your own regularly gridded meteorological forcing or include a spiderweb file. 
Alternatively, you can create an ensemble of cyclone tracks to obtain a probabilistic hazard prediction.

**Step 9: Organize your models in a super region file.**

If you have created a large database of models and want to include them efficiently in your scenario file, 
you can organize the models in a *super region* file (see :ref:`Super regions <super_regions>`). Instead of calling all models in the scenario file, you now call this 
*super region* file.  
