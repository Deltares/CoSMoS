.. _stations:

Observation stations
--------------------

Observation stations allow model results to be compared with measured water
levels and wave conditions. Station locations are defined in TOML files and
referenced from ``model.toml``; observation data can be provided manually or
downloaded automatically.

Station locations
^^^^^^^^^^^^^^^^^

Station files are located in ``configuration/stations``. Each file defines one
or more stations with their coordinates and metadata.

Example station file:

.. include:: examples/ndbc_buoy.toml
       :literal:

In the :ref:`model TOML file <models>`, reference one or more station files
using the ``station`` keyword. The following attributes can be specified per
station:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Attribute
     - Description

   * - name
     - Station identifier.

   * - longname
     - Descriptive name for display.

   * - longitude, latitude
     - Geographic coordinates.

   * - type
     - Station type: ``wave_buoy`` or ``tide_gauge``.

   * - coops_id
     - NOAA CO-OPS tide gauge identifier (optional).

   * - ndbc_id
     - NDBC wave buoy identifier (optional).

   * - water_level_correction
     - Vertical datum correction applied to observations (optional).

   * - mllw
     - Mean Lower Low Water level in metres (optional).

The default run folder includes station files for NDBC wave buoys and NOAA
CO-OPS water level stations. Additional station locations can be added by
creating new TOML files in the ``configuration/stations`` folder.

Observation data
^^^^^^^^^^^^^^^^

Observation data for defined stations are either downloaded automatically or
provided manually:

- **NOAA CO-OPS water level stations** — data is downloaded automatically from
  the NOAA CO-OPS server during each forecast cycle.
- **NDBC wave buoys** — historical data must be downloaded manually from the
  `NDBC website <https://www.ndbc.noaa.gov/>`_. The following script converts
  NDBC text files to the CSV format used by CoSMoS:

.. include:: examples/ndbc2csv.py
       :literal:

.. note::

   This script requires the Coastal Hazards Toolkit (``cht_observations``).

Observation files must follow this naming convention:

- Water levels: ``observations/<observations_path>/waterlevels/waterlevel.<stationid>.observed.csv``
- Waves: ``observations/<observations_path>/waves/waves.<stationid>.observed.csv``

Example CSV formats:

.. include:: examples/waves.42060.observed.csv.js
       :literal:

.. include:: examples/waterlevel.42060.observed.csv.js
       :literal:

In the :ref:`scenario file <scenario>`, set the ``observations_path`` keyword
to include these observations in the web viewer.
