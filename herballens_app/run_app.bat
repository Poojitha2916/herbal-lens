@echo off
echo Starting Herbal Lens Application...

:: Start Backend in a new window
echo Starting Backend (Flask on port 5000)...
start "Herbal Lens Backend" cmd /k "cd backend && python app.py"

:: Wait a few seconds for backend to initialize
timeout /t 5 /nobreak > nul

:: Start Frontend in a new window
echo Starting Frontend (Static Server on port 8080)...
start "Herbal Lens Frontend" cmd /k "cd frontend && python -m http.server 8080"

echo.
echo Application is starting! 
echo Access the app at: http://localhost:8080
echo.
pause
