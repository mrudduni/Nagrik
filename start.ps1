$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$agentBackendDir = Join-Path $root "nagrik-agent-backend"
$complaintBackendDir = Join-Path (Join-Path $root "backend") "complaint_service"
$frontendDir = Join-Path $root "frontend"

$agentCmd = "Set-Location '$agentBackendDir'; `$env:PYTHONIOENCODING='utf-8'; `$env:PYTHONUTF8='1'; py -m uvicorn app.main:app --reload --port 8000"
$complaintCmd = "Set-Location '$complaintBackendDir'; `$env:PYTHONIOENCODING='utf-8'; `$env:PYTHONUTF8='1'; py -m uvicorn app.main:app --reload --port 8002"
$frontendCmd = "Set-Location '$frontendDir'; npm run dev"

if (Test-Path $agentBackendDir) {
    Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $agentCmd
}
if (Test-Path $complaintBackendDir) {
    Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $complaintCmd
}
if (Test-Path $frontendDir) {
    Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $frontendCmd
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "         NAGRIK Integrated Platform Launching            " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  1. Citizen & Gov Portal  : http://localhost:3000" -ForegroundColor White
Write-Host "  2. AI Voice Agent Backend: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  3. Complaint Microservice: http://localhost:8002" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
