$baseDir = Join-Path $PSScriptRoot "drehbert-pi-py"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$destinationZip = Join-Path $PSScriptRoot "drehbert-pi-py-for-chatgpt_$timestamp.zip"

$targets = @("src", "tests", ".python-version", "pyproject.toml")
$existingTargets = $targets | ForEach-Object { Join-Path $baseDir $_ } | Where-Object { Test-Path $_ }

Compress-Archive -Path $existingTargets -DestinationPath $destinationZip -Force
Write-Host "Successfully created archive at $destinationZip"
