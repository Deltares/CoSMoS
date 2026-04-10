# CoSMoS — Coastal Storm Modelling System

CoSMoS is an operational flood forecasting framework that orchestrates
hydrodynamic, wave, and morphodynamic models for coastal storm impact
assessment. It automates the full forecast cycle: meteorological data
download, model nesting, parallel execution (local or cloud), tiled map
generation, and web viewer publication.

## Supported models

| Model | Library |
|-------|---------|
| SFINCS | hydromt-sfincs |
| HurryWave | hydromt-hurrywave |
| Delft3D FM | cht-delft3dfm |
| XBeach | cht-xbeach |
| BEWARE | cht-beware |

## Installation

1. Clone the repository:

       git clone https://github.com/Deltares/CoSMoS.git
       cd CoSMoS

2. Install as an editable package:

       pip install -e .

## Quick start

```python
from cosmos.cosmos import cosmos

cosmos.initialize("path/to/run_folder", config_file="config.toml")
cosmos.run("scenario_name")
```

## Building and publishing

Build the package:

    pip install --upgrade build
    python -m build

Upload to PyPI:

    pip install --upgrade twine
    python -m twine upload dist/*

## License

CoSMoS is licensed under the [GNU General Public License v3.0](LICENSE).
This means you may use, modify, and redistribute the code, but any
derivative work must also be distributed under the GPL v3. Incorporating
CoSMoS code into proprietary software is not permitted.

## Documentation

See the `docs/` folder for the full manual.
