.. _super_regions:

Regions and super regions
-------------------------

For large-scale forecasting systems, the model database may contain dozens or
hundreds of models across multiple geographic regions. Rather than listing each
model individually in the scenario file, CoSMoS allows models to be referenced
by **region** or grouped into **super regions**.

Each model in the database belongs to a region (determined by its folder
structure: ``model_database/<region>/<type>/<name>``). In the scenario file,
you can select all models of a given type within a region::

    [[model]]
    region = "gulf_of_mexico"
    type = ["sfincs", "hurrywave"]

A **super region** combines multiple regions into a single reference. Super
region files are stored in ``configuration/super_regions`` and can be
referenced in the scenario file using the ``super_region`` keyword, simplifying
scenario files for large domains.

Example super region file:

.. include:: examples/super_region.toml
       :literal:

Usage in a scenario file::

    [[model]]
    super_region = "us_east_coast"
    type = ["sfincs"]
