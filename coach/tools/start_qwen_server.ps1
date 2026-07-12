param(
    [int]$Port = 8001,
    [switch]$Watch
)

$ErrorActionPreference = "Stop"
$modelPath = "$env:USERPROFILE\.cache\openvino-models\qwen2.5-coder-0.5b-int4"
$scriptDir = Split-Path -Parent $PSCommandPath
$serverScript = Join-Path $scriptDir "..\..\openvino_server.py"

function Start-Server {
    $proc = Get-Process -Name python -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match "openvino_server" }
    if ($proc) {
        Write-Host "Server already running (PID: $($proc.Id))" -ForegroundColor Yellow
        return $proc
    }
    Write-Host "Starting Qwen server on port $Port..." -ForegroundColor Cyan
    $proc = Start-Process -FilePath "py" -ArgumentList "-3", $serverScript, "--model", $modelPath, "--port", $Port -NoNewWindow -PassThru
    Start-Sleep -Seconds 3
    Write-Host "Server started (PID: $($proc.Id))" -ForegroundColor Green
    return $proc
}

if (-not $Watch) {
    Start-Server
    Write-Host "Server running in background. Use -Watch to auto-restart on crash." -ForegroundColor Gray
    exit
}

while ($true) {
    $proc = Start-Server
    if ($proc) {
        $proc.WaitForExit()
        Write-Host "Server crashed! Restarting in 3s..." -ForegroundColor Red
        Start-Sleep -Seconds 3
    } else {
        Start-Sleep -Seconds 10
    }
}
