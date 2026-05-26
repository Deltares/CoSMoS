# Build a CoSMoS fat Batch image (model binary + runner Python env) and push to
# ECR. One Dockerfile builds the whole matrix: -Model {sfincs|hurrywave} and
# -Arch {cpu|gpu}. The lean model base (which supplies the binary) is produced
# by the aws_batch repo and must exist locally or in ECR; this only adds the
# Python layer + entrypoint on top.
#
#   .\build.ps1 -Model sfincs -Arch gpu
#   .\build.ps1 -Model sfincs -Arch cpu -SkipPush
#   .\build.ps1 -Model hurrywave -Arch gpu -BaseImage my/custom:base
#
# cht_* are git-pinned; bump the refs below (or pass -ChtUtilsRef etc.) for a
# reproducible build instead of tracking main.
param(
    [Parameter(Mandatory = $true)][ValidateSet("sfincs", "hurrywave")]$Model,
    [Parameter(Mandatory = $true)][ValidateSet("cpu", "gpu")]$Arch,
    [string]$BaseImage,
    [string]$ChtUtilsRef   = "main",
    [string]$ChtTilingRef  = "main",
    [string]$ChtNestingRef = "main",
    [switch]$SkipLogin,
    [switch]$SkipPush
)

$ErrorActionPreference = "Stop"
$env:AWS_PROFILE = "sfincs"

$Region    = "eu-west-1"
$AccountId = "012053003218"
$Registry  = "$AccountId.dkr.ecr.$Region.amazonaws.com"

# Default lean base image per model+arch (override with -BaseImage). These are
# the images the aws_batch repo builds; adjust there if the tags change.
$defaultBase = @{
    "sfincs-gpu"    = "sfincs-gpu:local"
    "sfincs-cpu"    = "sfincs-cpu:local"
    "hurrywave-gpu" = "$Registry/hurrywave:gpu-st6_gse"
    "hurrywave-cpu" = "mvanormondt/hurrywave-cpu-ifx"
}
if (-not $BaseImage) { $BaseImage = $defaultBase["$Model-$Arch"] }

# hydromt plugin per model (pin the version for reproducibility).
$hydromt = @{ "sfincs" = "hydromt_sfincs==1.2.2"; "hurrywave" = "hydromt-hurrywave" }[$Model]

$ImageUri = "$Registry/${Model}:${Arch}-fat-batch"

Set-Location $PSScriptRoot

Write-Host "==> Building $ImageUri" -ForegroundColor Cyan
Write-Host "      base=$BaseImage  hydromt=$hydromt"
Write-Host "      cht_utils@$ChtUtilsRef  cht_tiling@$ChtTilingRef  cht_nesting@$ChtNestingRef"
docker build -f Dockerfile `
    --build-arg BASE_IMAGE=$BaseImage `
    --build-arg HYDROMT_SPEC=$hydromt `
    --build-arg CHT_UTILS_REF=$ChtUtilsRef `
    --build-arg CHT_TILING_REF=$ChtTilingRef `
    --build-arg CHT_NESTING_REF=$ChtNestingRef `
    -t $ImageUri .
if ($LASTEXITCODE -ne 0) { throw "fat image build failed." }

if ($SkipPush) {
    Write-Host "==> -SkipPush: built $ImageUri locally, not pushing." -ForegroundColor DarkGray
} else {
    if (-not $SkipLogin) {
        Write-Host "==> Logging Docker into ECR ..." -ForegroundColor Cyan
        $pw = aws ecr get-login-password --region $Region
        if ($LASTEXITCODE -ne 0) { throw "ecr get-login-password failed." }
        docker login --username AWS --password $pw $Registry
        if ($LASTEXITCODE -ne 0) { throw "docker login failed." }
    }
    Write-Host "==> Pushing $ImageUri ..." -ForegroundColor Cyan
    docker push $ImageUri
    if ($LASTEXITCODE -ne 0) { throw "push failed." }
}

Write-Host ""
Write-Host "Done. Image URI:" -ForegroundColor Green
Write-Host "    $ImageUri"
