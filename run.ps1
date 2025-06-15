# run.ps1
$Root   = Split-Path $MyInvocation.MyCommand.Path -Parent
$ApiDir = Join-Path $Root "VetClinic\API\vetclinic_api"
$GuiDir = Join-Path $Root "VetClinic\GUI\vetclinic_gui"

# 1) Genchee (Ganache)
Start-Process powershell -ArgumentList @(
    '-NoExit',
    '-Command',
    "[Console]::Title = 'Genchee'; `
     Set-Location '$ApiDir'; `
     ganache --port 8545 --deterministic"
) -WindowStyle Normal

# 2) Api (uvicorn)
Start-Process powershell -ArgumentList @(
    '-NoExit',
    '-Command',
    "[Console]::Title = 'Api'; `
     Set-Location '$ApiDir'; `
     uvicorn vetclinic_api.main:app --reload"
) -WindowStyle Normal

# 3) Gui
Start-Process powershell -ArgumentList @(
    '-NoExit',
    '-Command',
    "[Console]::Title = 'Gui'; `
     Set-Location '$GuiDir'; `
     python -m vetclinic_gui.main"
) -WindowStyle Normal
