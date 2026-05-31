$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$source = Resolve-Path (Join-Path $repoRoot "scraper\chroma_data")
$target = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "chroma_data"))

if (-not $source.Path.StartsWith($repoRoot.Path)) {
    throw "Source escaped the workspace."
}

if (-not $target.StartsWith($PSScriptRoot)) {
    throw "Target escaped the deployment directory."
}

if (Test-Path -LiteralPath $target) {
    Remove-Item -LiteralPath $target -Recurse -Force
}

Copy-Item -LiteralPath $source.Path -Destination $target -Recurse
Write-Host "Exported Chroma snapshot to $target"
