.. _models:

Model database
--------------

The model database contains the input files for all available models. The path
to the database is specified in the :ref:`configuration file <configuration>`.

CoSMoS handles model nesting and meteorological forcing automatically. Each
model folder therefore contains only the grid and input files for that
individual model. A ``model.toml`` file describes model metadata such as the
model type, nesting relationships, and which observation stations to include.

Example ``model.toml``:

.. include:: examples/model.toml
       :literal:

The model name within CoSMoS corresponds to the folder name containing the
``model.toml`` file (see :ref:`Folder structure <folder_structure>`).

Model settings
^^^^^^^^^^^^^^

The following settings can be specified in ``model.toml``:

.. list-table::
   :widths: 30 50 10 10
   :header-rows: 1

   * - Parameter
     - Description
     - Default
     - Unit

   * - longname
     - Display name shown in the web viewer.
     - name
     -

   * - runid
     - Model identifier used internally by CoSMoS.
     - None
     -

   * - type
     - Model type: ``beware``, ``delft3dfm``, ``hurrywave``, ``sfincs``, or ``xbeach``.
     -
     -

   * - crs
     - Coordinate reference system (e.g. ``"EPSG:4326"``).
     -
     -

   * - flow
     - Enable flow simulation.
     - false
     -

   * - wave
     - Enable wave simulation.
     - false
     -

   * - priority
     - Execution priority (lower values run first).
     - 10
     -

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
     - Flow model spin-up time.
     - 0
     - hours

   * - wave_spinup_time
     - Wave model spin-up time.
     - 0
     - hours

   * - vertical_reference_level_name
     - Name of the vertical reference level.
     - MSL
     -

   * - vertical_reference_level_difference_with_msl
     - Offset between the vertical reference level and MSL.
     - 0
     - m

   * - boundary_water_level_correction
     - Datum correction applied to boundary water levels.
     - 0
     - m

   * - station
     - List of station TOML files (from ``configuration/stations``) to add as
       observation points.
     -
     -

   * - make_wave_map
     - Generate wave height map tiles.
     - false
     -

   * - make_flood_map
     - Generate flood map tiles.
     - false
     -

   * - make_sedero_map
     - Generate sedimentation/erosion map tiles.
     - false
     -

   * - mhhw
     - Mean Higher High Water level, used for total water level estimation
       when clustering models.
     - 0
     - m

Model-specific input
^^^^^^^^^^^^^^^^^^^^

CoSMoS supports five model types. The required input for each type is described
below.

BEWARE
""""""

`BEWARE <https://oss.deltares.nl/web/beware>`_ is a meta-model based on XBeach
for predicting nearshore wave heights and total water levels at reef-lined
coasts.

The BEWARE executable folder (specified in
:ref:`config.toml <configuration>`) must contain:

- ``XBeach_BEWARE_database.nc`` — the XBeach runup and wave condition database.
- ``run_bw.bas`` — batch file to execute ``run_beware.py``.
- ``run_beware.py`` — BEWARE execution script.

The model ``input`` folder must contain:

- ``beware.inp`` — BEWARE input file.
- The file referenced by ``r2matchfile`` in ``beware.inp`` — a ``.mat`` file
  describing matching probabilities for each input profile.
- The file referenced by ``profsfile`` in ``beware.inp`` — a profile file with
  the following columns:

  - ``profid`` — profile ID.
  - ``x_off``, ``y_off`` — offshore coordinates (for wave model nesting).
  - ``x_coast``, ``y_coast`` — coastline intersection coordinates.
  - ``x_flow``, ``y_flow`` — nearshore coordinates (for flow model nesting).
  - ``beachslope`` — beach slope for total water level prediction.

- ``runup.x`` and ``runup.y`` — coordinates for different runup levels, in the
  format:

.. code-block:: text

      <runup_level1> <runup_level2> <runup_level3>

      <profid> <x_level1> <x_level2> <x_level3>

      e.g.
      0 2 4
      29 163960.98 163961.75 164154.9
      35 163961.98 163962.75 164156.9

Delft3D FM
""""""""""

`Delft3D FM <https://www.deltares.nl/en/software-and-data/products/delft3d-flexible-mesh-suite>`_
can be run as a standalone flow model or as a coupled flow-wave model. The
model ``input`` folder must contain:

- A ``flow`` folder with flow model input. The ``.mdu`` file name must match
  the ``runid`` specified in ``model.toml``.
- A ``wave`` folder (optional) with wave model input. The ``.mdw`` file must be
  named ``wave.mdw``. The output grid must be named ``wave.grd``; an optional
  nested grid can be named ``nest.grd``. CoSMoS adjusts the following settings
  in the ``.mdw`` file automatically:

  - ``ReferenceDate = REFDATEKEY``
  - ``LocationFile = OBSFILEKEY``

- A ``dimr_config.xml`` file specifying flow and wave working directories.
  CoSMoS sets the simulation start time by replacing the keyword ``TIMEKEY``.

The ``misc`` folder must contain a text file (named after the model) with
the coordinates of the model outline.

HurryWave
"""""""""

`HurryWave <https://hurrywave.readthedocs.io/>`_ is a computationally efficient
third-generation spectral wave model with physics similar to SWAN and
WaveWatch III.

Model input files are located in the ``input`` folder. To generate wave map
tiles, the ``tiling`` folder must contain ``indices`` and ``topobathy``
sub-folders.

The ``misc`` folder must contain a text file (named after the model) with
the coordinates of the model outline.

SFINCS
""""""

`SFINCS <https://sfincs.readthedocs.io/en/latest/>`_ (Super-Fast INundation of
CoastS) is a reduced-complexity flood model. Model input files are located in
the ``input`` folder. To generate flood map tiles, the ``tiling`` folder must
contain ``indices`` and ``topobathy`` sub-folders.

The ``misc`` folder must contain a text file (named after the model) with
the coordinates of the model outline.

XBeach
""""""

`XBeach <https://xbeach.readthedocs.io/en/latest/>`_ is a nearshore
morphodynamic model. Model input files are located in the ``input`` folder. To
generate bed level map tiles, the ``tiling`` folder must contain an ``indices``
sub-folder.

The ``misc`` folder must contain a text file (named after the model) with
the coordinates of the model outline.
