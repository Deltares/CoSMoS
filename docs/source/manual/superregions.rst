.. _super_regions:

Regions and super regions
-------------------------

A large model database can contain dozens or hundreds of models. Rather than
listing each model by name in the :ref:`scenario file <scenario>`, models can
be selected by **region** or by **super region**.

Regions
^^^^^^^

Every model in the database belongs to a region. The region is the name of the
first folder level in the :ref:`model database <models>`:

.. code-block:: text

    model_database
    ├── gulf
    │   ├── hurrywave
    │   │   └── hurrywave_gulf
    │   └── sfincs
    │       └── sfincs_gulf_500m
    └── texas
        └── sfincs
            ├── sfincs_texas_0001
            └── sfincs_texas_0002

To select all models of one or more types in a region, use ``region`` and
``type`` in a ``[[model]]`` section of the scenario file:

.. code-block:: toml

    [[model]]
    region = "texas"
    type   = ["sfincs"]

``region`` takes a single region name. To select models from several regions,
add a ``[[model]]`` section per region, or use a super region.

Super regions
^^^^^^^^^^^^^

A super region is a named list of regions. Each super region is a TOML file in
``configuration/super_regions`` in the run folder. The name of the super
region is the file name without ``.toml``, in lower case. For example,
``configuration/super_regions/gulf.toml``:

.. code-block:: toml

    region = ["gulf", "texas", "louisiana", "mississippi", "alabama", "west_florida"]

To select all models of one or more types in these regions, use
``super_region`` and ``type`` in a ``[[model]]`` section:

.. code-block:: toml

    [[model]]
    super_region = "gulf"
    type         = ["hurrywave", "sfincs"]

``super_region`` takes a single super region name. A super region contains
regions only; it cannot contain other super regions.

Super regions can also be used to define :ref:`model clusters
<scenario_clusters>`.

Notes
^^^^^

- ``type`` is required when selecting by region or super region. Without it,
  no models are selected.
- A model that is selected by more than one ``[[model]]`` section is included
  only once.
- The template run folder contains three super regions: ``gulf``,
  ``north_atlantic``, and ``us_east_coast``.