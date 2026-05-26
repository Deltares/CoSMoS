# CoSMoS "fat" image for run_mode = "batch" (Option B).
#
# Built FROM a lean model-binary base (produced by the aws_batch repo, which
# owns the generic "run the binary on Batch" images). This image adds the
# CoSMoS Python runner environment + the batch entrypoint, so one container can
# run a whole per-model step sequence (prepare → simulate → tile, or per-member
# → merge+tile) driven by run_job_2.py.
#
# This recipe is model- and arch-agnostic: pass the lean base via BASE_IMAGE.
# build.ps1 builds the 2×2 matrix (sfincs|hurrywave × cpu|gpu) from this one
# Dockerfile. The model binary (sfincs / hurrywave) is inherited from
# BASE_IMAGE and must already be on PATH there.

ARG BASE_IMAGE
FROM ${BASE_IMAGE}

# --- Python runner dependencies (overridable at build time) ------------------
# hydromt plugin + boto3 come from PyPI (pin the version for reproducibility);
# the cht_* packages are git-pinned (cht_nesting isn't on PyPI, and we develop
# all three, so pin every build to an explicit ref/tag/commit).
ARG HYDROMT_SPEC=hydromt_sfincs==1.2.2
ARG CHT_UTILS_REF=main
ARG CHT_TILING_REF=main
ARG CHT_NESTING_REF=main

ENV DEBIAN_FRONTEND=noninteractive
ENV CONDA_DIR=/opt/conda
# Put conda's python ahead of the system python so `python run_job_2.py` uses
# the runner env. The model binary stays on PATH from BASE_IMAGE.
ENV PATH=${CONDA_DIR}/bin:${PATH}

RUN apt-get update && apt-get install -y --no-install-recommends \
        awscli ca-certificates curl git bzip2 \
    && rm -rf /var/lib/apt/lists/*

# Miniforge → clean Python 3.11 + the geospatial core (gdal/rasterio/geopandas
# are painful via pip; let conda-forge provide them, then pip the rest).
RUN curl -fsSL -o /tmp/mf.sh \
        "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh" \
    && bash /tmp/mf.sh -b -p ${CONDA_DIR} \
    && rm /tmp/mf.sh \
    && conda install -y -n base -c conda-forge \
        python=3.11 gdal rasterio geopandas netcdf4 xarray xugrid \
    && conda clean -afy

# CoSMoS runner stack. NOTE: run_job_2.py itself is NOT baked in — it is synced
# from S3 with the job input. We only install the libraries it imports.
RUN pip install --no-cache-dir boto3 "${HYDROMT_SPEC}" \
    && pip install --no-cache-dir \
        "git+https://github.com/Deltares-research/cht_utils@${CHT_UTILS_REF}" \
        "git+https://github.com/Deltares-research/cht_tiling@${CHT_TILING_REF}" \
        "git+https://github.com/Deltares-research/cht_nesting@${CHT_NESTING_REF}"

COPY entrypoint.sh /usr/local/bin/entrypoint_cosmos.sh
RUN chmod +x /usr/local/bin/entrypoint_cosmos.sh

WORKDIR /data
ENTRYPOINT ["/usr/local/bin/entrypoint_cosmos.sh"]
