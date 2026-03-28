param(
    [switch]$WithSandbox
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$backendCmd = "cd `"$repoRoot\backend`"; .\venv\Scripts\activate; uvicorn app.main:app --reload"
$frontendCmd = "cd `"$repoRoot\frontend`"; npm run dev"
$sandboxCmd = "cd `"$repoRoot`"; python sandbox_dsp.py"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

if ($WithSandbox) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $sandboxCmd
}
