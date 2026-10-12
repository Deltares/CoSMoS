.. _stations:

Observation stations
--------------------

Observation stations are locations where CoSMoS writes model time series, so
that model results can be shown in the :ref:`web viewer <webviewer>` and
compared with measured water levels and wave conditions. Station locations are
defined in TOML files; observation data is either fetched by the web viewer or
provided manually.

Station locations
^^^^^^^^^^^^^^^^^

Station files are located in ``configuration/stations``. Each file defines one
or more stations with their coordinates and metadata.

Example station file:

.. code-block:: toml

    [[station]]
    name = "42060"
    ndbc_id = "42060"
    longname = "Caribbean Valley - 63 NM WSW of Montserrat"
    longitude = -63.331
    latitude = 16.433
    type = "wave_buoy"

    [[station]]
    name = "9755371"
    coops_id = "9755371"
    longname = "San Juan, La Puntilla, San Juan Bay"
    longitude = -66.1164
    latitude = 18.4592
    type = "tide_gauge"
    MLLW = -0.232

The following attributes can be specified per station:

.. list-table::
   :widths: 25 60 15
   :header-rows: 1

   * - Attribute
     - Description
     - Required

   * - name
     - Station identifier, used in the names of the time series files. Must be
       unique.
     - yes

   * - longname
     - Descriptive name shown in the web viewer (``long_name`` is also
       accepted). Defaults to ``name``.
     - no

   * - longitude, latitude
     - Geographic coordinates (WGS 84).
     - yes

   * - type
     - Station type: ``wave_buoy`` (wave height and period), ``tide_gauge``
       (water level), or ``twl_gauge`` (total water level, SFINCS only).
     - yes

   * - coops_id
     - NOAA CO-OPS tide gauge identifier.
     - no

   * - ndbc_id
     - NDBC wave buoy identifier.
     - no

   * - iho_id
     - IHO tide station identifier. For these stations CoSMoS adds a tidal
       prediction to the web viewer.
     - no

   * - id
     - Identifier for stations from other sources. This (or one of the three
       identifiers above) is used to find manually provided observation files.
     - no

   * - MLLW
     - Mean Lower Low Water level relative to MSL, in metres, passed on to the
       web viewer. Note the capitals.
     - no

   * - hat
     - Highest Astronomical Tide, in metres. Required for ``twl_gauge``
       stations: these are only shown in the web viewer when the computed
       total water level exceeds this value.
     - no

The template run folder includes station files for NDBC wave buoys and NOAA
CO-OPS water level stations. Additional station locations can be added by
creating new TOML files in the ``configuration/stations`` folder.

Adding stations to models
^^^^^^^^^^^^^^^^^^^^^^^^^

There are two ways to add stations to a model:

- In the :ref:`model TOML file <models>`, list one or more station files with
  the ``station`` keyword::

      station = ["ndbc_buoys_all.toml", "coops_stations_all.toml"]

  Station files that are only relevant for one model can also be placed in a
  ``stations`` folder inside the model folder.

- In the :ref:`scenario file <scenario>`, add a ``[[station]]`` block to add a
  station file to all models of a type, or to specific models, for that
  scenario only::

      [[station]]
      name = "usgs_fev_waterlevels_hurricane_michael.toml"
      model_type = ["sfincs"]

      [[station]]
      name = "ndbc_buoys_local.toml"
      model_name = ["hurrywave_gulf"]

Only stations that lie inside the model outline are used. When a station lies
inside several nested models, the web viewer shows the result of the most
detailed model.

Observation data
^^^^^^^^^^^^^^^^

Observations are shown together with the model results in the web viewer:

- **NOAA CO-OPS water level stations** — for stations with a ``coops_id``, the
  web viewer retrieves observed and predicted water levels directly from the
  NOAA CO-OPS server when a station is opened. Nothing needs to be downloaded
  beforehand, but the browser needs internet access.
- **Other stations** (e.g. NDBC wave buoys) — observation data must be provided
  manually, as described below.

Providing observation files
"""""""""""""""""""""""""""

Observation files are stored in the ``observations`` folder of the run folder,
in a sub-folder per event:

- Water levels: ``observations/<observations_path>/wl/wl.<station_id>.observed.csv.js``
- Waves: ``observations/<observations_path>/waves/waves.<station_id>.observed.csv.js``

Here ``<station_id>`` is the identifier of the station (``coops_id``,
``ndbc_id``, ``iho_id``, or ``id``). In the :ref:`scenario file <scenario>`,
set the ``observations_path`` keyword to the name of the sub-folder to include
these observations in the web viewer.

The files contain comma-separated values, wrapped in one line of JavaScript at
the start and one at the end. Example wave file (significant wave height in
metres and peak period in seconds):

.. code-block:: text

    var csv_obs = `date_time,hm0,tp
    2022-09-17T00:40:00,1.800,7.690
    2022-09-17T01:40:00,1.950,8.330
    2022-09-17T02:40:00,2.100,8.330
    `;

Example water level file (water level in metres):

.. code-block:: text

    var csv_obs = `date_time,wl
    2022-09-17T00:00:00,0.150
    2022-09-17T00:30:00,0.149
    2022-09-17T01:00:00,0.147
    `;

NDBC wave buoys
"""""""""""""""

Historical data for NDBC wave buoys can be downloaded from the
`NDBC website <https://www.ndbc.noaa.gov/>`_. The following script converts
the NDBC text files to the format used by CoSMoS:

.. include:: examples/ndbc2csv.py
       :literal:

.. note::

   The current web viewer template (``version06``) does not yet plot observed
   waves. The files are already copied to the web viewer data folder.