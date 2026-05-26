#!/usr/bin/env bash
#
# Entrypoint for the CoSMoS fat image on AWS Batch (run_mode = "batch").
#
# Contract with the CoSMoS orchestrator (src/cosmos/model.py submit_job, batch
# branch). CoSMoS submits the container command as a single STEP token and
# passes everything else as environment variables:
#
#   $1 (command)   one of:  run_all | prepare_and_simulate | merge_and_tile
#   BUCKET         S3 bucket holding the job folder           (required)
#   SUBFOLDER      job key in the bucket: <scenario>/models/<model>   (required)
#   SCENARIO       scenario name
#   CYCLE          cycle string (YYYYMMDD_HHz)
#   MODEL          model name
#   MODEL_TYPE     sfincs | hurrywave | ...
#   WEBVIEWER_FOLDER  S3 key prefix for the web viewer data (tiles land here)
#   TILING_FOLDER     key of the model's topobathy/index tiles (region/type/name)
#   TILING_BUCKET     bucket holding the tiling tgz   (default: cosmos-models)
#   AWS_BATCH_JOB_ARRAY_INDEX   set by Batch for array jobs → ensemble member i
#
# This entrypoint owns ALL S3 staging; the Python runner (run_job_2.py) only
# reads/writes local files under /data. That keeps the runner's batch path
# simple and mirrors how Argo's artifacts used to stage data around the steps.
#
# Steps:
#   1. sync job folder  s3://BUCKET/SUBFOLDER -> /data
#   2. (tile steps) fetch + unpack topobathy/index tiles into /data/tiles_in
#   3. python run_job_2.py <step>   (cwd = /data; uses the conda runner env)
#   4. sync /data -> s3://BUCKET/SUBFOLDER   (job outputs: his/map/restart/...)
#   5. (tile steps) sync generated tiles -> s3://BUCKET/WEBVIEWER_FOLDER/...
#
set -euo pipefail

STEP="${1:?usage: entrypoint_cosmos.sh <run_all|prepare_and_simulate|merge_and_tile>}"
: "${BUCKET:?BUCKET env var required}"
: "${SUBFOLDER:?SUBFOLDER env var required}"
TILING_BUCKET="${TILING_BUCKET:-cosmos-models}"

S3_JOB="s3://${BUCKET}/${SUBFOLDER}"

echo "[entrypoint] step=${STEP} model=${MODEL:-?} job=${S3_JOB}"
mkdir -p /data
cd /data

# ── 1. Stage the job folder in ──────────────────────────────────────────────
echo "[entrypoint] sync in: ${S3_JOB} -> /data"
aws s3 sync "${S3_JOB}" /data --no-progress

# For ensemble array elements, expose the member index to the runner. The
# runner resolves it to a member name via ensemble_members.txt.
if [[ -n "${AWS_BATCH_JOB_ARRAY_INDEX:-}" ]]; then
    export COSMOS_MEMBER_INDEX="${AWS_BATCH_JOB_ARRAY_INDEX}"
    echo "[entrypoint] array member index = ${COSMOS_MEMBER_INDEX}"
fi

# ── 2. Tile steps need the model's topobathy + index tiles ──────────────────
needs_tiles() { [[ "${STEP}" == "run_all" || "${STEP}" == "merge_and_tile" ]]; }
if needs_tiles && [[ -n "${TILING_FOLDER:-}" ]]; then
    echo "[entrypoint] fetching tiling data: s3://${TILING_BUCKET}/${TILING_FOLDER}/tiles.tgz"
    mkdir -p /data/tiles_in
    if aws s3 cp "s3://${TILING_BUCKET}/${TILING_FOLDER}/tiles.tgz" /tmp/tiles.tgz --no-progress; then
        tar -xzf /tmp/tiles.tgz -C /data/tiles_in
    else
        echo "[entrypoint] WARNING: no tiling tgz found; tile generation may be skipped"
    fi
fi

# ── 3. Run the requested step ───────────────────────────────────────────────
echo "[entrypoint] running: python run_job_2.py ${STEP}"
python run_job_2.py "${STEP}"

# ── 4. Push job outputs back to the job folder ──────────────────────────────
# The runner writes outputs in place under /data; sync everything back. (The
# orchestrator only pulls the files it needs — his/map/restart — afterwards.)
echo "[entrypoint] sync out: /data -> ${S3_JOB}"
aws s3 sync /data "${S3_JOB}" --no-progress --exclude "tiles_in/*"

# ── 5. Publish tiles to the web viewer location ─────────────────────────────
if needs_tiles && [[ -n "${WEBVIEWER_FOLDER:-}" && -d /data/tiles ]]; then
    DEST="s3://${BUCKET}/${WEBVIEWER_FOLDER}/${SCENARIO}/${CYCLE}"
    echo "[entrypoint] publishing tiles -> ${DEST}"
    aws s3 sync /data/tiles "${DEST}" --no-progress
fi

echo "[entrypoint] done."
