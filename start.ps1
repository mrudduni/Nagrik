$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root "nagrik-agent-backend"
$frontendDir = Join-Path $root "frontend"

$backendCmd = "Set-Location '$backendDir'; py -m uvicorn app.main:app --reload --port 8000"
$frontendCmd = "Set-Location '$frontendDir'; npm run dev"

Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $backendCmd
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Frontend: http://localhost:3000"
