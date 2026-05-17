# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What CoSMoS is

CoSMoS (Coastal Storm Modelling System) is an **operational forecasting orchestrator**, not a hydrodynamic model itself. It wraps five external models (SFINCS, HurryWave, Delft3D FM, XBeach, BEWARE) and drives the full forecast cycle: meteo download → nested model setup → parallel execution (local / multi-PC / Kubernetes via Argo) → tile generation → web viewer publication → cleanup.

A "run" iterates over **cycles** (6-hour forecast windows by default). Each cycle reads a `scenario.toml`, instantiates one or more `Model` subclasses, resolves their nesting graph, and submits jobs through the `ModelLoop`.

## Common commands

```powershell
# Install editable (no requirements.txt — dependencies are in pyproject.toml)
pip install -e .

# Run a scenario (needs a run folder with configuration/config.toml)
python -m cosmos run <scenario_name> --path <run_folder> [--config config.toml] [--cycle 20231213_00z]
# COSMOS_PATH env var replaces --path

# Validate without running (also runs automatically before every cosmos.run)
python -m cosmos validate <scenario_name> --path <run_folder>

# Post-process only / rebuild web viewer only
python -m cosmos post-process <scenario_name> --models all
python -m cosmos webviewer <scenario_name>

# Lint (ruff config in ruff.toml — selects E,F,NPY,PD,C4,I; line length unbounded)
ruff check src
ruff check --fix src   # only `I` (imports) is auto-fixable

# Build docs (Sphinx)
cd docs && make html
```

There is **no test suite** in this repo — do not invent `pytest` commands. End-to-end validation happens via `cosmos.validate()` and by running real scenarios.

## Environment setup

`mkenv_cosmos.ps1` is the source of truth for the dev environment: a `cosmos` conda env with Python 3.11, plus a long list of `pip install -e` siblings (`cht_*`, `hydromt_sfincs`, `hydromt-hurrywave`). CoSMoS depends on these sibling repos being checked out and editable — see `clone_repos_cosmos.ps1` for the full list. Do not pin them in `pyproject.toml`; they're intentionally external.

## Architecture: three loops, one singleton

The control flow is non-obvious and worth understanding before editing:

1. **`cosmos` singleton** (`src/cosmos/cosmos.py`) — module-level instance of `CoSMoS`. Holds global state (`cosmos.config`, `cosmos.scenario`, `cosmos.cycle`, `cosmos.webviewer`, `cosmos.cloud`, `cosmos.all_models`). Almost every module does `from .cosmos import cosmos` and mutates it. This is by design; do not try to refactor it into dependency injection.

2. **`MainLoop`** (`main_loop.py`) — one tick per **cycle**. Reads scenario, downloads meteo, generates track ensembles, deep-copies tide-only twin models if `include_tide_only`, resolves nesting, then kicks off the ModelLoop. Uses `sched` to defer the first run until `cycle + delay`.

3. **`ModelLoop`** (`model_loop.py`) — re-runs every 1 s (20 s in cloud mode). On each tick: detect finished simulations → move output → pre-process newly-ready models → submit jobs → post-process in background → when everything is done, build the web viewer.

Lazy imports are deliberate in `__init__.py`: model-specific wrappers (`CoSMoS_SFINCS`, `CoSMoS_HurryWave`, etc.) are **not** re-exported because their `cht_*` / `hydromt_*` dependencies are optional. Import them from the submodule (`from cosmos.sfincs import CoSMoS_SFINCS`).

## Model wrappers

Each external model has a wrapper class extending `cosmos.Model` (e.g. `CoSMoS_SFINCS` in `sfincs.py`) plus a standalone job-runner script (`run_sfincs.py`, etc.) that gets copied into the job folder and run independently — possibly on a different machine or in a container. The wrapper handles `read_model_specific()`, `pre_process()`, `move()`, `post_process()`; the runner handles nesting step-2, simulation, ensemble merging, tiling.

When adding behaviour to a model, decide carefully whether it belongs in the **wrapper** (runs in the orchestrator process, has access to `cosmos.*`) or the **runner** (runs in the job environment, has only its input folder).

## Configuration / scenario layout

Configuration lives **outside** the source tree, in a "run folder". A working layout looks like:

```
run_folder/
  configuration/
    config.toml                          # primary config, but name is arbitrary —
                                         # passed via --config / config_file=
                                         # (e.g. config_local_continuous.toml)
    stations/                            # observation station TOMLs
    super_regions/<name>.toml            # model groupings
    color_maps/                          # map_contours.toml etc.
    areas/<name>.geojson                 # cyclone forecast area filters
    scripts/                             # user pre/post-processing hooks
    webviewer_templates/
  scenarios/<scenario_name>/
    scenario.toml
    restart/<model_name>/{flow,wave}/    # restart files persist ACROSS cycles
                                         # — kept above the cycle folder
    <YYYYMMDD_HHz>/                      # one folder per cycle
      cosmos.log
      job_list/
      models/<model_name>/{input, output, timeseries}/
  jobs/                                  # transient working dirs (run_mode=parallel polls here)
  webviewers/<viewer_name>/              # one subfolder per config.webviewer.name —
                                         # a run folder can host several viewers
  cosmos.log                             # top-level log (cosmos.log())
  run_cosmos.py                          # convention: thin launcher script
```

`configuration/` is searched in `run_folder/` first, then in its parent — this lets multiple run folders share one config. See `Configuration.set()` in `configuration.py`.

The **model database** (`config.model_database.path`) and **meteo database** (`config.meteo_database.path`) sit elsewhere on disk and are shared across run folders. Models are discovered by walking `model_database/<region>/<type>/<name>/`, which contains `model.toml`, optional `model.geojson`, and `input/`, `setup/`, `tiling/` subfolders.

The **restart location matters**: each model's restart files live at `scenarios/<name>/restart/<model_name>/{flow,wave}/` — sibling to the cycle folders, not inside one. This is how cycles chain together in continuous mode.

`cosmos_run_folder/` inside this repo is a **minimal template**, not a working configuration — its paths are placeholders.

## Run modes — two orthogonal settings (don't confuse them)

`[run]` in `config.toml` has two similarly-named keys that control different things:

- **`mode`** — cycle scheduling. `single_shot` (one cycle, exit) or `continuous` (re-fire every `interval` hours; `catch_up = true` jumps the clock forward when wall-clock time has moved past the next scheduled cycle).
- **`run_mode`** — job distribution. `serial` (local PC), `parallel` (worker PCs poll the shared `jobs/` folder via `CosmosRunParallel` in `run_parallel.py` and claim anything marked `ready.txt`), or `cloud` (jobs go to S3 + Argo Workflows on Kubernetes via `cloud.py` / `argo.py`; the `Argo` import is wrapped in try/except because `hera` is optional).

These are independent — e.g. `mode = "continuous", run_mode = "cloud"` is the production forecasting setup.

Cleanup of old cycles is governed by `clean_up = true` + `clean_up_mode` + `prune_after_hours` (see `clean_up.py`), separate from both modes above.

SFINCS and HurryWave can additionally be executed in a Docker container (e.g. for GPU builds) by setting `sfincs_docker = true` / `hurrywave_docker = true` and providing `sfincs_docker_image` / `hurrywave_docker_image` under `[executables]`.

## Custom hooks

`config.run.pre_processing_script` / `post_processing_script` point at user Python files exposing `main(cycle_info_file)`. The path to a generated `cycle_info.yml` (scenario summary + active models) is passed in. See `custom_processing.py`.

## Web viewer

The Python side (`cosmos.webviewer.WebViewer`) builds a static, browser-only viewer per scenario cycle. It copies a **template** from `webviewer_templates/<version>/` into `run_folder/webviewers/<viewer_name>/` (one viewer per `config.webviewer.name`) and emits data files into that viewer's `data/<scenario>/<cycle>/` subtree. The version to copy is selected by `config.webviewer.version` (e.g. `"version06"`).

**Data contract is JSONP-style, not JSON.** Every data file is a `.js` that begins with `var <name> = ...` and is loaded by the JS side via a dynamically-injected `<script>` tag — the loader then reads `window[<name>]`. The known globals are documented at the top of [version06/js/loaders.js](webviewer_templates/version06/js/loaders.js) (`scenario`, `map_variables`, `stations`, `buoys`, `track_data`, `wind`, `runup`, etc., plus `csv` / `csv_obs` for timeseries). When changing a data filename or the global it assigns to, update both the Python emitter AND that loaders.js comment block.

**Versioned templates.** Each `webviewer_templates/version0X/` is a complete, self-contained viewer:
- **v02–v05** are legacy. Many files were copy-paste duplicates (seven near-identical `<plot>_timeseries.html` files, a `wil-layers.js` grab-bag, ~17 loose globals).
- **v06** is a structural rewrite. Same JSONP contract with Python — no Python changes were needed. Architecture:
  - **Classic `<script>` tags**, NOT ES modules, so it works from `file://` for local previewing. Loaded in dependency order in `index.html` and `html/timeseries.html`.
  - **Single `window.cosmos` namespace** populated by IIFE-wrapped modules (`cosmos.config`, `cosmos.state`, `cosmos.loaders`, `cosmos.layers.{tile,geojson,wind,stations,cyclone}`, `cosmos.ui.{panel,legend,iconLegend}`, `cosmos.timeseries.{core,plotTypes}`). Replaces v05's ~17 loose globals.
  - **Table-driven GeoJSON layers**: new variable types are added by appending one entry to `GEOJSON_SPECS` in `layers/geojson.js`, not by writing a new `make*Layer` function.
  - **One unified `html/timeseries.html`** replaces v05's seven timeseries pages; dispatches on `?type=<plot type>&...` to a function in `timeseries/plot-types.js`. The popup URL is constructed JS-side (in `layers/geojson.js` / `layers/stations.js`), so Python doesn't know or care about the URL scheme.
  - **Map library is Leaflet 1.7.1.** A MapLibre swap was discussed but deferred to a future v07. The modular structure isolates the swap-points (`layers/*`, parts of `main.js`); the `state`, `loaders`, `panel`, and `timeseries/` modules are framework-agnostic.

**Local preview.** Just open `webviewer_templates/version06/index.html` in a browser — classic scripts mean `file://` works. The page needs a `data/` folder next to `index.html`; junction one in from a real deployment to test (`New-Item -ItemType Junction -Path data -Target <run_folder>\webviewers\<name>\data`).

**Production deployment** is handled by `WebViewer.upload()` (SFTP via `webserver.*` config) or by AWS S3 sync in cloud mode. The Python side never serves the viewer itself.

## Conventions worth knowing

- **Cycle strings** are formatted `YYYYMMDD_HHz` (lowercase z), but parsed with `%Y%m%d_%HZ` (uppercase) — this asymmetry is deliberate and present throughout the codebase.
- **Errors are fatal via `cosmos.stop(msg)`**, which logs and raises a generic `Exception`. Validation collects errors into a list and returns `False` instead — prefer the validation pattern for new checks that should be reportable.
- **Logging** is plain text appended to `<main_path>/cosmos.log` via `cosmos.log(message)`. No `logging` module.
- **`cht_utils.fileops` (`fo`)** is used everywhere instead of `os`/`shutil` for filesystem ops (`fo.mkdir`, `fo.rmdir`, `fo.list_folders`, `fo.list_files`).
- Ruff ignores include `E501` (line length), `F841` (unused locals), `F821` (undefined names) — don't waste effort fixing these.
