.. _introduction:

What is CoSMoS?
---------------

The Coastal Storm Modelling System (**CoSMoS**) is a Python-based operational
forecasting framework for predicting storm-induced coastal hazards over large
geographic scales. It automates the full workflow from meteorological data
collection through to web-based visualization, covering storm surge, waves,
coastal compound flooding, and erosion.

CoSMoS orchestrates multiple hydrodynamic and wave models in a nested
configuration. A coarse offshore wave model (HurryWave) provides boundary
conditions to regional flow models (SFINCS, Delft3D FM), which in turn drive
local overland flood models and nearshore morphodynamic models (XBeach, BEWARE).
The system handles all the nesting, forcing, and data transfer between these
models automatically.

CoSMoS supports both **forecast** and **hindcast** modes. In forecast mode it
runs continuously, downloading new meteorological data each cycle and producing
updated predictions. In hindcast mode it runs a single simulation for a
historical event. For tropical cyclone events, CoSMoS can generate ensembles of
synthetic tracks to produce probabilistic hazard estimates. Results are
automatically post-processed into map tiles and time series, and published to an
interactive web viewer.
