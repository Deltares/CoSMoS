.. _meteo:

Meteorological forcing
----------------------

CoSMoS automatically downloads, collects, and writes meteorological forcing
data for each model based on the settings in the
:ref:`scenario file <scenario>`. The path to the meteorological database is
specified in the :ref:`configuration file <configuration>`.

An example of the meteo database folder structure:

.. include:: examples/meteo_folder.txt
       :literal:

Three types of meteorological forcing are supported:

- **Gridded meteorological data** (scenario keyword: ``meteo_dataset``).
  Regularly spaced wind, pressure, and precipitation fields stored as NetCDF
  files.
- **Spiderweb forcing** (scenario keyword: ``meteo_spiderweb``). Cyclone-centred
  wind and pressure fields on a polar grid.
- **Track ensemble** (scenario keyword: ``meteo_track``). A cyclone track file
  from which CoSMoS generates an ensemble of synthetic tracks for probabilistic
  predictions.

Metadata for all data sources is stored in ``meteo_database.toml``:

.. include:: examples/meteo_database.toml
       :literal:

Dataset attributes
^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 25 55 10 10
   :header-rows: 1

   * - Attribute
     - Description
     - Default
     - Unit

   * - name
     - Dataset identifier.
     -
     -

   * - source
     - Data source. Options: ``gfs_anl_0p50``, ``gfs_forecast_0p25``,
       ``coamps_analysis``, ``coamps_tc_hindcast``, ``coamps_tc_forecast``,
       ``alternative``.
     -
     -

   * - x_range, y_range
     - Geographic extent for download and collection (EPSG 4326).
     - None
     - degrees

   * - xystride
     - Sub-sampling factor to reduce dataset resolution.
     - 1
     -

Gridded meteorological data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Gridded datasets consist of NetCDF files containing the following variables:

.. list-table::
   :widths: 25 45 15 15
   :header-rows: 1

   * - Variable
     - Description
     - Dimensions
     - Unit

   * - lat
     - Latitude.
     - lat
     - degrees

   * - lon
     - Longitude.
     - lon
     - degrees

   * - wind_u
     - Eastward wind component.
     - [lon, lat]
     - m/s

   * - wind_v
     - Northward wind component.
     - [lon, lat]
     - m/s

   * - barometric_pressure
     - Sea-level pressure.
     - [lon, lat]
     - Pa

   * - precipitation
     - Precipitation rate.
     - [lon, lat]
     - mm/hr

NetCDF files must follow the naming convention:
``<dataset_name>.<yyyymmdd_hhmm>.nc``. For forecast datasets, the files are
organised in sub-folders named by cycle time.

CoSMoS processes meteorological data in two stages:

1. **Download** — if ``download_meteo`` is enabled in the
   :ref:`configuration <configuration>`, data is fetched from a remote server.
   The following datasets can be downloaded automatically:

   .. list-table::
      :widths: 30 70
      :header-rows: 1

      * - Dataset
        - Description

      * - gfs_anl_0p50
        - Global Forecast System (GFS) analysis (0.50° resolution).

      * - gfs_forecast_0p25
        - Global Forecast System (GFS) forecast (0.25° resolution).

      * - coamps_analysis
        - COAMPS analysis fields.

      * - coamps_tc_hindcast
        - COAMPS tropical cyclone hindcast.

      * - coamps_tc_forecast
        - COAMPS tropical cyclone forecast.

2. **Collect** — CoSMoS reads the downloaded NetCDF files for each dataset
   referenced in the scenario and passes the data to the model-specific classes,
   which write the forcing files in the format required by each model.

Spiderweb forcing
^^^^^^^^^^^^^^^^^

Spiderweb files provide cyclone wind and pressure fields on a moving polar grid
centred on the storm eye. They are commonly used for tropical cyclone
forecasting. For details on the file format, see the
`Tropical Cyclone Toolbox documentation
<https://publicwiki.deltares.nl/display/DDB/Tropical+Cyclone>`_.

To use a spiderweb file, set the ``meteo_spiderweb`` keyword in the scenario
file to the file name (without extension) located in the ``spiderwebs`` folder
of the meteo database.

Track ensemble
^^^^^^^^^^^^^^

CoSMoS can generate an ensemble of synthetic tropical cyclone tracks to produce
probabilistic estimates of storm surge, waves, and inundation. Track
perturbations follow the methodology of DeMaria et al. (2009), accounting for
along-track, cross-track, and maximum wind speed errors. Error statistics can
be configured in the :ref:`[track_ensemble] <configuration>` section of the
configuration file.

To enable ensemble mode:

- Set ``track_ensemble_nr_realizations`` in the scenario file to the desired
  number of realisations. CoSMoS enables ensemble mode automatically when this
  keyword is present.
- Provide the meteorological source:

  - ``meteo_dataset`` — CoSMoS extracts a cyclone track from the gridded wind
    fields and generates an ensemble from it.
  - ``meteo_track`` — CoSMoS generates an ensemble directly from the provided
    best-track file.

CoSMoS determines which models to run in ensemble mode based on the geographic
extent of the generated track cone. Only models whose domain intersects the
cone are included in the ensemble.
