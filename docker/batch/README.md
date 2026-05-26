# CoSMoS Batch image (`run_mode = "batch"`)

The **fat** image for running CoSMoS model jobs on AWS Batch. It carries the
model **binary** *and* the CoSMoS/cht/hydromt **Python runner environment**, so
one container runs a whole per-model step sequence driven by `run_job_2.py`.

It lives here (not in the `aws_batch` repo) because it bakes the **CoSMoS
contract** — the entrypoint's env-var convention and the three step tokens —
and the runner's Python dependencies. The `aws_batch` repo owns the generic,
model-only **lean** images (just the binary + S3 sync); this image is built
`FROM` one of those lean bases.

## Layering

```
aws_batch repo   →  lean binary images   (sfincs-gpu:local, hurrywave:gpu-st6_gse, …)
CoSMoS/docker/batch (here)  →  FROM <lean base> + Python runner env + entrypoint
```

## Files

| file | purpose |
|---|---|
| `Dockerfile` | `ARG BASE_IMAGE`; conda geo core + pip runner deps; one recipe for all model×arch |
| `entrypoint.sh` | S3 sync in → `python run_job_2.py <step>` → sync out (+ tiles); resolves the array member index |
| `build.ps1` | `-Model {sfincs\|hurrywave} -Arch {cpu\|gpu}`; builds + pushes `<model>:<arch>-fat-batch` |
| `register_jobdef.py` | registers `cosmos-<model>-fat` (CPU/MEMORY defaults, no GPU; CoSMoS adds GPU for sim steps) |

## Dependencies

`run_job_2.py` itself is **not** baked in — it's synced from S3 with the job
input. The image only provides the libraries it imports:

- `hydromt_sfincs` (or `hydromt-hurrywave`) + `boto3` — PyPI, version-pinned.
- `cht_utils`, `cht_tiling`, `cht_nesting` — **git-pinned** (`cht_nesting` isn't
  on PyPI, and all three are actively developed, so every build pins an explicit
  ref). Bump the refs with `-ChtUtilsRef` / `-ChtTilingRef` / `-ChtNestingRef`
  (default `main` — set real tags/commits for reproducible builds).
- model binary — inherited from `BASE_IMAGE`.
- gdal/rasterio/geopandas — via conda-forge (reliable geo stack).

## Build + register

```powershell
# 1. ensure the lean base exists (built by the aws_batch repo)
#    e.g. aws_batch\sfincs\build_gpu_image.ps1  →  sfincs-gpu:local
# 2. build + push the fat image (PowerUser)
.\build.ps1 -Model sfincs -Arch gpu
# 3. register the job definition (ADMIN — PassRole)
aws sso login --profile sfincs-admin
python register_jobdef.py --model sfincs --arch gpu
```

CPU and GPU are **two images** (different binary + base), but the same recipe —
just `-Arch cpu` vs `-Arch gpu`.

## ⚠️ Remaining work before end-to-end

The image infra + the CoSMoS submit/poll path (`src/cosmos/batch.py`,
`model.py` batch branch) are in place. **Not yet done:** the runner's per-step
S3 staging for `run_mode == "batch"`. In `run_sfincs.py`, `prepare_single` /
`map_tiles` / `clean_up` still branch on `cloud` (Argo mount paths) vs local
(orchestrator paths). Batch needs its own staging so that, inside the container,
per-member spiderwebs and cross-model boundary files are fetched from S3, tiles
are written to `./tiles`, and `write_config_yml` emits container-relative paths.
The composite tokens (`run_all`, `prepare_and_simulate`, `merge_and_tile`)
already exist in `run_sfincs.py`; the other runners need them mirrored.
