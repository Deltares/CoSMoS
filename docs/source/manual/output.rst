.. _output:

Model output
------------

After running a CoSMoS scenario, output is stored in the ``scenarios`` folder.
For each forecast cycle, a new cycle folder is created. An example of an output
folder structure is shown below for a scenario called *hurricane_irma* with a
cycle starting on 4 September 2017:

.. include:: examples/scenario_folder.txt
       :literal:

- The **job_list** folder tracks which models have completed. When rerunning a
  scenario, models marked as finished will be skipped. Delete the corresponding
  *finished* file to force a rerun.
- The **models** folder contains all model input and output files.
- The **restart** folder contains restart files for all models, used to
  initialize subsequent forecast cycles.
