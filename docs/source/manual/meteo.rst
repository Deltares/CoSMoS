.. _meteo:

Meteorological forcing
----------------------

CoSMoS automatically downloads, collects, and writes meteorological forcing
for each model. Two types of forcing are supported, and they can be combined:

- **Gridded meteorological data** — regularly spaced wind, pressure, and
  precipitation fields, stored as NetCDF files in the meteo database (see
  :ref:`Gridded data <meteo_gridded>`).
- **Tropical cyclone tracks** — from a cyclone track, CoSMoS generates a
  spiderweb file with cyclone-centred wind and pressure fields (see
  :ref:`Tropical cyclones <meteo_cyclones>`).

For probabilistic predictions, CoSMoS can also run an ensemble of cyclone
tracks. The ensemble can be provided in the meteo database, or CoSMoS
generates it from the cyclone track (see
:ref:`Track ensemble <meteo_ensemble>`).

Which forcing is used is set in the :ref:`scenario file <scenario>`. The
location of the meteo database is set in the
:ref:`configuration file <configuration>`.

Overview of settings
^^^^^^^^^^^^^^^^^^^^

The table below lists all settings related to meteorological forcing. Most are
set in the :ref:`scenario file <scenario>` (``scenarios/<scenario_name>/scenario.toml``),
so they apply to one scenario only. The others are set in the ``[run]`` and
``[track_ensemble]`` sections of the :ref:`configuration file <configuration>`
(``configuration/config.toml``) and apply to all scenarios. The datasets
themselves are defined in the meteo database (see
:ref:`below <meteo_database>`).

.. list-table::
   :widths: 35 15 50
   :header-rows: 1

   * - Keyword
     - File
     - Description

   * - ``meteo_dataset``
     - scenario
     - Name of a gridded dataset in the meteo database. Can also be set per
       model in a ``[[model]]`` section.

   * - ``meteo_track``
     - scenario
     - Name (without extension) of a track file in ``tracks``.

   * - ``cyclone_track_forecast_source``, ``cyclone_track_forecast_area_file``
     - scenario
     - Use a JTWC forecast track.

   * - ``meteo_wind``, ``meteo_atmospheric_pressure``, ``meteo_precipitation``
     - scenario
     - Switch individual meteo variables off (default: ``true``).

   * - ``run_ensemble``, ``track_ensemble_nr_realizations``
     - scenario
     - Run a track ensemble, and the number of synthetic tracks.

   * - ``download_meteo``
     - configuration
     - Download gridded data before each cycle (default: ``true``).

   * - ``collect_meteo_up_to_cycle``
     - configuration
     - Only use forecast cycles up to the cycle being run (default:
       ``false``).

   * - ``spw_wind_field``
     - configuration
     - How the spiderweb wind field is computed (default:
       ``"parametric"``).

   * - ``[track_ensemble]``, ``ensemble_models``
     - configuration
     - Error statistics for synthetic tracks, and the model types that are
       run as an ensemble.

.. _meteo_database:

The meteo database
^^^^^^^^^^^^^^^^^^

Example of a meteo database:

.. code-block:: text

    meteo_database
    ├── meteo_database.toml
    ├── gfs_forecast_0p25_north_atlantic
    │   ├── 20260928_00z
    │   │   ├── gfs_forecast_0p25_north_atlantic.20260928_0000.nc
    │   │   └── gfs_forecast_0p25_north_atlantic.20260928_0300.nc
    │   └── 20260928_06z
    ├── gfs_analysis_0p50_north_atlantic
    │   ├── gfs_analysis_0p50_north_atlantic.20170904_0000.nc
    │   └── gfs_analysis_0p50_north_atlantic.20170904_0300.nc
    └── tracks
        └── irma.cyc

Each gridded dataset is stored in its own folder, named after the dataset.
Cyclone track files are stored in the ``tracks`` folder.

The gridded datasets are defined in ``meteo_database.toml``:

.. code-block:: toml

    [[meteo_dataset]]
    name = "gfs_forecast_0p25_north_atlantic"
    source = "gfs_forecast_0p25"
    x_range = [-100.0, -1.0]
    y_range = [-8.0, 80.0]

    [[meteo_dataset]]
    name = "gfs_analysis_0p50_north_atlantic"
    source = "gfs_analysis_0p50"
    x_range = [-100.0, -1.0]
    y_range = [-8.0, 80.0]

    [[meteo_dataset]]
    name = "coamps_tc_forecast"
    source = "coamps_tc_forecast"

Each ``[[meteo_dataset]]`` entry has the following attributes:

.. list-table::
   :widths: 25 60 15
   :header-rows: 1

   * - Attribute
     - Description
     - Default

   * - name
     - Dataset name. This is the name used for ``meteo_dataset`` in the
       scenario file, for the dataset folder, and for the NetCDF files.
       Required.
     -

   * - source
     - Data source, see the table below. Required.
     -

   * - x_range, y_range
     - Longitude and latitude range to download (degrees, WGS 84).
     - None

   * - tau
     - Number of hours at the start of each forecast cycle to skip when
       several cycles are combined.
     - 0

The following sources are available:

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Source
     - Description

   * - gfs_forecast_0p25
     - Global Forecast System (GFS) forecast, 0.25° (UCAR THREDDS server).

   * - gfs_forecast_0p25_ncar_archive
     - Archived GFS forecasts, 0.25° (NCAR Research Data Archive).

   * - gfs_analysis_0p50
     - GFS analysis, 0.50° (NCEI THREDDS server). For hindcasts.

   * - ecmwf_forecast_0p25
     - ECMWF IFS open-data forecast, 0.25°.

   * - era5_reanalysis_0p25
     - ERA5 reanalysis, 0.25°. Requires a CDS API account and the ``cdsapi``
       package.

   * - coamps_tc_forecast
     - COAMPS-TC tropical cyclone forecast, including the storm track.

   * - matroos
     - KNMI Harmonie forecast from the Deltares Matroos server.

   * - custom
     - Data that is produced or downloaded by another process. Requires the
       attribute ``filepath``, pointing to a Python file that converts the
       data to the CoSMoS NetCDF format (see ``custom_forecast.py`` in the
       ``cht_meteo`` package for a template).

.. _meteo_gridded:

Gridded data
^^^^^^^^^^^^

File format
"""""""""""

Gridded datasets consist of one NetCDF file per time step, named
``<dataset_name>.<yyyymmdd_hhmm>.nc``. For forecast datasets, the files are
organised in sub-folders per forecast cycle (``yyyymmdd_hhz``). For analysis
datasets, all files are stored directly in the dataset folder.

Each file contains the following variables:

.. list-table::
   :widths: 25 45 15 15
   :header-rows: 1

   * - Variable
     - Description
     - Dimensions
     - Unit

   * - time
     - Time.
     - time
     -

   * - lat
     - Latitude (south to north).
     - lat
     - degrees

   * - lon
     - Longitude.
     - lon
     - degrees

   * - wind_u
     - Eastward wind component.
     - time, lat, lon
     - m/s

   * - wind_v
     - Northward wind component.
     - time, lat, lon
     - m/s

   * - barometric_pressure
     - Sea-level pressure.
     - time, lat, lon
     - Pa

   * - precipitation
     - Precipitation rate.
     - time, lat, lon
     - mm/hr

How gridded data is used
""""""""""""""""""""""""

Set ``meteo_dataset`` in the scenario file to the name of a dataset. This
applies to all models in the scenario; a different dataset can be set for
individual models in their ``[[model]]`` section. Wind, atmospheric pressure,
and precipitation can each be switched off with ``meteo_wind``,
``meteo_atmospheric_pressure``, and ``meteo_precipitation``.

CoSMoS then processes the data in two stages:

1. **Download** — if ``download_meteo`` is enabled in the configuration file,
   the data for the simulation period is downloaded for every dataset used in
   the scenario. Set ``download_meteo = false`` to use data that is already in
   the meteo database.
2. **Collect** — CoSMoS reads the NetCDF files and passes the data to the
   models, which write the forcing files in their own format. For forecast
   datasets, the most recent cycle is used for each moment in time. In a
   hindcast, set ``collect_meteo_up_to_cycle = true`` to only use forecast
   cycles up to the cycle that is being run.

.. _meteo_cyclones:

Tropical cyclones
^^^^^^^^^^^^^^^^^

For tropical cyclones, CoSMoS generates a spiderweb file: wind and pressure
fields on a polar grid that moves with the storm eye. The models use the
spiderweb on top of the gridded data (if any).

Cyclone track
"""""""""""""

CoSMoS looks for a cyclone track in this order:

1. **Track file** — ``meteo_track`` in the scenario file is the name, without
   extension, of a ``.cyc`` track file in the ``tracks`` folder of the meteo
   database (e.g. ``meteo_track = "irma"``). For details on the file format,
   see the `Tropical Cyclone Toolbox documentation
   <https://publicwiki.deltares.nl/display/DDB/Tropical+Cyclone>`_.
2. **JTWC forecast** — with ``cyclone_track_forecast_source = "jtwc"`` in the
   scenario file, CoSMoS downloads the JTWC forecast tracks to
   ``tracks/jtwc``. The track to use is selected with
   ``cyclone_track_forecast_area_file``, the name of a GeoJSON file with a
   polygon in ``configuration/areas``.
3. **Track from the gridded dataset** — a ``.cyc`` file in the cycle folders
   of the gridded dataset. This is the case for COAMPS-TC, which comes with a
   track.

Spiderweb wind field
""""""""""""""""""""

The wind field of the spiderweb is set with ``spw_wind_field`` in the
configuration file:

- ``"parametric"`` (default) — a parametric wind field (Holland, 2010)
  computed from the track.
- ``"meteo_data"`` — the wind field is taken from the gridded dataset around
  the storm eye.

The track and the spiderweb for a cycle are stored in the ``track`` folder of
the :ref:`cycle output folder <output>` as ``storm.cyc`` and ``storm.spw``.

.. _meteo_ensemble:

Track ensemble
^^^^^^^^^^^^^^

CoSMoS can run an ensemble of cyclone tracks to produce probabilistic
estimates of storm surge, waves, and inundation. To enable ensemble mode, set
``run_ensemble = true`` in the scenario file. An ensemble is only made when a
cyclone track is available (see :ref:`Tropical cyclones <meteo_cyclones>`).

Ensemble tracks
"""""""""""""""

The ensemble tracks come from one of the following, in this order:

1. **Ensemble members in the gridded dataset** — the cycle folder contains
   one sub-folder per member, each with its own track (``<member>.cyc``) and
   NetCDF files. CoSMoS runs one simulation per member, with the spiderweb and
   the gridded forcing of that member. The last member (in alphabetical
   order) is used as the best track. This data is not downloaded; it must
   already be in the meteo database.

   .. code-block:: text

       <dataset_name>
       └── 20260928_00z
           ├── member_01
           │   ├── member_01.cyc
           │   ├── member_01.20260928_0000.nc
           │   └── member_01.20260928_0300.nc
           └── member_02
               └── ...

2. **Ensemble tracks in the gridded dataset** — when the best track comes from
   the gridded dataset (as for COAMPS-TC), the cycle folder can contain a
   ``track_ensemble`` sub-folder with one ``.cyc`` file per member. CoSMoS
   computes a parametric spiderweb for each track.

   .. code-block:: text

       <dataset_name>
       └── 20260928_00z
           ├── <dataset_name>.20260928_0000.nc
           ├── storm.cyc
           └── track_ensemble
               ├── member_01.cyc
               └── member_02.cyc

3. **Synthetic tracks** — otherwise, CoSMoS generates synthetic tracks from
   the best track. Track perturbations follow the methodology of DeMaria et
   al. (2009), accounting for along-track, cross-track, and maximum wind speed
   errors. The number of tracks is set with
   ``track_ensemble_nr_realizations`` in the scenario file (default:
   ``nr_realizations`` in the configuration file). Error statistics can be
   configured in the :ref:`[track_ensemble] <configuration>` section of the
   configuration file.

Models in the ensemble
""""""""""""""""""""""

CoSMoS selects the models to run as an ensemble based on the area covered by
the ensemble tracks. Only models whose outline intersects the cone around the
ensemble tracks, and whose type is listed in ``ensemble_models`` in the
configuration file, are run as an ensemble. These models are run twice: once
with the best track and once as an ensemble.