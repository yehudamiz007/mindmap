# deebot_service.ps1
# Runs at Windows startup: starts ecovacs server + cloudflare tunnel,
# then updates GitHub Pages with the new tunnel URL automatically.

$PYTHON     = "C:\Users\YEHUDA\AppData\Local\Programs\Python\Python311\python.exe"
$WORKSPACE  = "C:\Users\YEHUDA\.openclaw\workspace"
$SERVER     = "$WORKSPACE\scripts\ecovacs_server.py"
$CLOUDFLARED= "$WORKSPACE\scripts\cloudflared.exe"
$HTML       = "$WORKSPACE\ecovacs-joystick\index.html"
$LOG        = "$WORKSPACE\scripts\deebot_service.log"

function Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts $msg" | Tee-Object -FilePath $LOG -Append
}

Log "=== DEEBOT Service Starting ==="

# Kill any old instances
Get-Process python,cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Start Python server
Log "Starting ecovacs server..."
$serverJob = Start-Process -FilePath $PYTHON -ArgumentList $SERVER -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 3

# Start cloudflared and capture output
Log "Starting Cloudflare tunnel..."
$cfOut = "$env:TEMP\cloudflared_out.txt"
$cfProc = Start-Process -FilePath $CLOUDFLARED -ArgumentList "tunnel","--url","http://localhost:8765" `
    -RedirectStandardOutput $cfOut -RedirectStandardError $cfOut `
    -PassThru -WindowStyle Hidden

# Wait for tunnel URL (up to 30s)
$tunnelUrl = $null
$deadline = (Get-Date).AddSeconds(30)
while ((Get-Date) -lt $deadline -and -not $tunnelUrl) {
    Start-Sleep -Seconds 1
    if (Test-Path $cfOut) {
        $content = Get-Content $cfOut -Raw -ErrorAction SilentlyContinue
        if ($content -match 'https://([a-z0-9\-]+\.trycloudflare\.com)') {
            $tunnelUrl = "https://$($Matches[1])"
        }
    }
}

if (-not $tunnelUrl) {
    Log "ERROR: Could not get tunnel URL"
    exit 1
}

Log "Tunnel URL: $tunnelUrl"
$tunnelUrl | Set-Content "$WORKSPACE\scripts\tunnel_url.txt"

# Update HTML via Python to preserve UTF-8 encoding
$updateScript = @"
import re, sys
f = sys.argv[1]; url = sys.argv[2]
txt = open(f, encoding='utf-8').read()
txt = re.sub(r'https://[a-z0-9-]+\.trycloudflare\.com', url, txt)
open(f, 'w', encoding='utf-8', newline='\n').write(txt)
print('Updated')
"@
& $PYTHON -c $updateScript $HTML $tunnelUrl
Log "Updated HTML"

# Git push
Set-Location $WORKSPACE
git add "ecovacs-joystick/index.html" 2>&1 | Out-Null
git commit -m "auto: tunnel $tunnelUrl" 2>&1 | Out-Null
git push origin main 2>&1 | Out-Null
Log "Pushed to GitHub Pages"

Log "All done! App: https://yehudamiz007.github.io/mindmap/ecovacs-joystick/"
Log "Processes: server=$($serverJob.Id) tunnel=$($cfProc.Id)"

# Keep script alive (so Task Scheduler sees it as running)
Wait-Process -Id $serverJob.Id -ErrorAction SilentlyContinue
