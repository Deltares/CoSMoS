.. _models:

Model database
--------------

The model database contains the input files for all available models. The path
to the database is specified in the :ref:`configuration file <configuration>`.

Models are organized by region and model type::

    model_database
    └── <region>
        └── <type>
            └── <model_name>
                ├── model.toml
                ├── model.geojson
                ├── input
                ├── tiling
                └── stations

- The **model name** within CoSMoS is the name of the folder that contains the
  ``model.toml`` file. Model names are not case-sensitive and must be unique
  across the whole database.
- The **model type** is taken from the ``<type>`` folder and must be one of
  ``sfincs``, ``hurrywave``, ``delft3dfm``, ``xbeach``, or ``beware``.
- The **region** is taken from the ``<region>`` folder and is used to select
  models in a scenario (see :ref:`Regions and super regions <super_regions>`).

CoSMoS handles model nesting and meteorological forcing automatically. Each
model folder therefore contains only the grid and input files for that
individual model:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - File or folder
     - Description

   * - ``model.toml``
     - Model settings (see below). Required.

   * - ``input``
     - Model input files. Required.

   * - ``model.geojson``
     - Polygon with the outline of the model, used to select stations, cut out
       meteorological forcing, and select models for ensemble runs. Required
       (see :ref:`Model outline <model_outline>`).

   * - ``tiling``
     - Index and topography tiles, needed to make map tiles for the web viewer.

   * - ``stations``
     - Station files that are only used by this model (optional, see
       :ref:`Observation stations <stations>`).

Example ``model.toml``:

.. include:: examples/model.toml
       :literal:

Model settings
^^^^^^^^^^^^^^

The following settings can be specified in ``model.toml``.

General
"""""""

.. list-table::
   :widths: 30 50 10 10
   :header-rows: 1

   * - Parameter
     - Description
     - Default
     - Unit

   * - long_name
     - Display name, used in the log file and the web viewer. Required.
     -
     -

   * - crs
     - Coordinate reference system (e.g. ``"EPSG:4326"`` or ``"WGS 84"``).
       Required.
     -
     -

   * - runid
     - Run identifier. Required for Delft3D FM and BEWARE models.
     - None
     -

   * - wave
     - Set to ``true`` for a Delft3D FM model that is coupled with a wave
       model. For all other model types, CoSMoS sets ``flow`` and ``wave``
       automatically.
     - false
     -

   * - station
     - List of station TOML files to add as observation points. Files are
       looked up in ``configuration/stations`` and in the ``stations`` folder
       of the model. Only stations inside the model outline are used.
     -
     -

Nesting and timing
""""""""""""""""""

.. list-table::
   :widths: 30 50 10 10
   :header-rows: 1

   * - Parameter
     - Description
     - Default
     - Unit

   * - flow_nested
     - Name of the parent model providing flow boundary conditions.
     - None
     -

   * - wave_nested
     - Name of the parent model providing wave boundary conditions.
     - None
     -

   * - bw_nested
     - Name of the parent BEWARE model.
     - None
     -

   * - flow_spinup_time
     - Flow model spin-up time. Used when no restart file from a previous
       cycle is available.
     - 0
     - hours

   * - wave_spinup_time
     - Wave model spin-up time. Used when no restart file from a previous
       cycle is available.
     - 0
     - hours

   * - include_tide_only
     - Also run a tide-only version of this flow model (without meteorological
       forcing), used to make storm surge maps.
     - false
     -

Water levels
""""""""""""

.. list-table::
   :widths: 30 50 10 10
   :header-rows: 1

   * - Parameter
     - Description
     - Default
     - Unit

   * - vertical_reference_level_difference_with_msl
     - Offset between the vertical reference level of the model and MSL.
     - 0
     - m

   * - boundary_water_level_correction
     - Correction added to the boundary water levels from the parent model.
     - 0
     - m

   * - mhhw
     - Mean Higher High Water level, used for the total water level estimate
       when models are part of a cluster (see
       :ref:`Setting up a scenario <scenario>`).
     - 0
     - m

   * - boundary_twl_treshold
     - Total water level at the boundary above which the model is run when it
       is part of a cluster. With the default value the model is never
       selected, so set this for every model in a cluster.
     - 999
     - m

Output maps
"""""""""""

.. list-table::
   :widths: 30 50 10 10
   :header-rows: 1

   * - Parameter
     - Description
     - Default
     - Unit

   * - role
     - SFINCS only. ``"floodmap"``: make flood maps and always use
       precipitation. ``"large_scale"``: make water level maps and never use
       precipitation. ``"generic"``: use the ``make_*_map`` settings below.
     - "generic"
     -

   * - make_flood_map
     - Generate flood map tiles (SFINCS).
     - false
     -

   * - make_water_level_map
     - Generate maximum water level map tiles (SFINCS).
     - false
     -

   * - make_precipitation_map
     - Generate cumulative precipitation map tiles (SFINCS).
     - false
     -

   * - make_wave_map
     - Generate wave height map tiles (HurryWave).
     - false
     -

   * - make_sedero_map
     - Generate sedimentation/erosion map tiles (XBeach).
     - false
     -

Maps are only made when the corresponding setting in the ``[run]`` section of
the :ref:`configuration file <configuration>` is also enabled.

.. _model_outline:

Model outline
^^^^^^^^^^^^^

Every model needs a polygon with its outline. CoSMoS looks for it in this
order and uses the first file it finds:

1. ``model.geojson`` next to ``model.toml`` (preferred)
2. ``misc/exterior.geojson``
3. ``misc/outline.geojson``
4. ``misc/<model_name>.geojson``
5. ``misc/<model_name>.txt`` — text file with x and y coordinates in the model
   coordinate system

Model-specific input
^^^^^^^^^^^^^^^^^^^^

CoSMoS supports five model types. The required input for each type is described
below.

SFINCS
""""""

`SFINCS <https://sfincs.readthedocs.io/en/latest/>`_ (Super-Fast INundation of
CoastS) is a reduced-complexity flood model. Model input files, including
``sfincs.inp``, are located in the ``input`` folder. To generate flood, water
level, or storm surge map tiles, the ``tiling`` folder must contain ``indices``
and ``topobathy`` sub-folders.

A SFINCS model with ``wave_nested`` set also computes waves (SnapWave), with
wave boundary conditions from the parent wave model.

HurryWave
"""""""""

`HurryWave <https://hurrywave.readthedocs.io/>`_ is a computationally efficient
third-generation spectral wave model with physics similar to SWAN and
WaveWatch III. Model input files, including ``hurrywave.inp``, are located in
the ``input`` folder. To generate wave map tiles, the ``tiling`` folder must
contain an ``indices`` sub-folder.

Delft3D FM
""""""""""

`Delft3D FM <https://www.deltares.nl/en/software-and-data/products/delft3d-flexible-mesh-suite>`_
can be run as a standalone flow model or as a coupled flow-wave model. The
model ``input`` folder must contain:

- A ``flow`` folder with flow model input. The ``.mdu`` file must be named
  ``flow.mdu``.
- For a coupled flow-wave model (``wave = true`` in ``model.toml``):

  - A ``wave`` folder with wave model input. The ``.mdw`` file must be named
    ``wave.mdw``. CoSMoS replaces the following keywords in this file:

    - ``ReferenceDate = REFDATEKEY``
    - ``LocationFile = OBSFILEKEY``

  - A ``dimr_config.xml`` file specifying flow and wave working directories.
    CoSMoS sets the simulation times by replacing the keyword ``TIMEKEY``.

The ``runid`` in ``model.toml`` is used as the name of the observation points
file (``<runid>.xyn``).

XBeach
""""""

`XBeach <https://xbeach.readthedocs.io/en/latest/>`_ is a nearshore
morphodynamic model. Model input files, including ``params.txt``, are located
in the ``input`` folder. To generate sedimentation/erosion and bed level map
tiles, the ``tiling`` folder must contain an ``indices`` sub-folder.

The following additional settings can be specified in ``model.toml``:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Parameter
     - Description

   * - flow_nesting_points
     - List of ``[x, y]`` coordinates of the points where water levels are
       taken from the parent flow model. By default the points are derived
       from the XBeach input.

   * - wave_nesting_point
     - ``[x, y]`` coordinates of the point where wave conditions are taken
       from the parent wave model.

   * - zb_deshoal
     - Bed level to which the wave boundary conditions are de-shoaled.

BEWARE
""""""

`BEWARE <https://oss.deltares.nl/web/beware>`_ is a meta-model based on XBeach
for predicting nearshore wave heights and total water levels at reef-lined
coasts.

The BEWARE executable folder (specified in
:ref:`config.toml <configuration>`) must contain a run script named
``run_bw.bas`` (Windows) or ``run_bw.sh`` (Linux). CoSMoS copies this script to
the job folder and replaces the keyword ``EXEPATHKEY`` with the path of the
executable folder.

The model ``input`` folder must contain:

- ``beware.inp`` — BEWARE input file.
- The file referenced by ``r2matchfile`` in ``beware.inp`` — a ``.mat`` file
  describing matching probabilities for each input profile.
- The file referenced by ``profsfile`` in ``beware.inp`` (default:
  ``beware.profs``) — a profile file with the following columns:

  - ``profid`` — profile ID.
  - ``x_off``, ``y_off`` — offshore coordinates (for wave model nesting).
  - ``x_coast``, ``y_coast`` — coastline intersection coordinates.
  - ``x_flow``, ``y_flow`` — nearshore coordinates (for flow model nesting).
  - ``beachslope`` — beach slope for total water level prediction.

- ``runup.x`` and ``runup.y`` — coordinates for different runup levels, used
  for the runup map in the web viewer, in the format:

.. code-block:: text

      <runup_level1> <runup_level2> <runup_level3>

      <profid> <x_level1> <x_level2> <x_level3>

      e.g.
      0 2 4
      29 163960.98 163961.75 164154.9
      35 163961.98 163962.75 164156.9