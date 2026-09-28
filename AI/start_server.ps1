# MandiProof Backend Startup Script
# Run this on the PC, then connect Flutter app to http://<THIS_PC_IP>:8000

Write-Host "=== Mandi Nyaay Backend Launcher ===" -ForegroundColor Cyan
Write-Host ""

# Show LAN IP so phone can connect
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*"} | Select-Object -First 1).IPAddress
Write-Host ">>> Phone should connect to: http://${ip}:8000" -ForegroundColor Green
Write-Host ""

# Install deps
Write-Host "[1/3] Installing Python dependencies..." -ForegroundColor Yellow
pip install fastapi uvicorn sqlmodel "opencv-python-headless>=4.8" onnxruntime numpy scipy "scikit-learn>=1.3" pillow pytesseract mapie 2>&1 | Tail -5

Write-Host ""
Write-Host "[2/3] Dependencies installed." -ForegroundColor Green
Write-Host ""
Write-Host "[3/3] Starting FastAPI server on 0.0.0.0:8000 ..." -ForegroundColor Yellow
Write-Host ""

uvicorn app.api.app:app --host 0.0.0.0 --port 8000 --reload
