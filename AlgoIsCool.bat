@echo off
setlocal enabledelayedexpansion

title AlgoIsCool Server - Port 2109
color 0A

echo.
echo ========================================
echo  AlgoIsCool Professional Server Starter
echo ========================================
echo.

:: Безопасное определение директории
set "ROOT_DIR=%~dp0"
if "%ROOT_DIR%"=="" set "ROOT_DIR=%CD%"
cd /d "%ROOT_DIR%"

echo [INFO] Working directory: %CD%
echo.

:: Проверка Python
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] Python version:
python --version
echo.

:: Создание виртуального окружения если его нет
if not exist ".venv" (
    echo [INFO] Creating virtual environment in .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        echo.
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created in .venv
) else (
    echo [INFO] Virtual environment .venv exists
)

:: Активация виртуального окружения
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    echo.
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment activated
echo.

:: Проверка server.py
echo [INFO] Checking project files...
if not exist "server.py" (
    echo [ERROR] server.py not found!
    echo.
    echo Directory contents:
    dir /b
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] server.py found

:: Проверка requirements.txt
if not exist "requirements.txt" (
    echo [WARNING] requirements.txt not found, creating default...
    (
        echo Flask
        echo Flask-SQLAlchemy
        echo Flask-Security
        echo sqlalchemy-serializer
        echo Flask-WTF
        echo WTForms
        echo python-igraph
        echo psutil
    ) > requirements.txt
    echo [INFO] Created requirements.txt
)

:: Проверка и установка отсутствующих пакетов
echo [INFO] Checking installed packages...

:: Получаем список установленных пакетов
pip list --format=freeze > installed_temp.txt 2>nul

set "MISSING_PACKAGES="
set "NEEDS_INSTALL=0"

:: Читаем requirements.txt и проверяем каждый пакет
for /f "usebackq tokens=*" %%A in ("requirements.txt") do (
    set "REQ_PACKAGE=%%A"
    set "PACKAGE_FOUND=0"

    :: Извлекаем имя пакета из requirements (до версии)
    for /f "tokens=1 delims==<>" %%B in ("!REQ_PACKAGE!") do set "REQ_NAME=%%B"

    :: Проверяем есть ли пакет в установленных
    findstr /i /c:"!REQ_NAME!" installed_temp.txt >nul
    if !errorlevel! equ 0 (
        echo [OK] !REQ_NAME! already installed
    ) else (
        echo [MISSING] !REQ_PACKAGE! not found
        set "MISSING_PACKAGES=!MISSING_PACKAGES! !REQ_PACKAGE!"
        set "NEEDS_INSTALL=1"
    )
)

del installed_temp.txt 2>nul

:: Устанавливаем только отсутствующие пакеты
if !NEEDS_INSTALL! equ 1 (
    echo.
    echo [INFO] Installing missing packages...

    :: Устанавливаем каждый отсутствующий пакет
    for %%P in (!MISSING_PACKAGES!) do (
        echo [INSTALL] Installing %%P...
        pip install %%P
        if errorlevel 1 (
            echo [ERROR] Failed to install %%P
            echo.
            pause
            exit /b 1
        )
    )
    echo [SUCCESS] All missing packages installed
) else (
    echo [INFO] All packages already installed
)
echo.

:: Освобождение порта 2109 (для Python процессов)
echo [INFO] Checking port 2109...
set "CLEANED_PROCESSES=0"

for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":2109"') do (
    set "PID=%%i"
    if not "!PID!"=="0" (
        tasklist /fi "PID eq !PID!" /fo csv 2>nul | findstr /i "python.exe" >nul
        if !errorlevel! equ 0 (
            echo [INFO] Terminating Python process PID: !PID!
            taskkill /f /pid !PID! >nul 2>&1
            set /a CLEANED_PROCESSES+=1
        ) else (
            tasklist /fi "PID eq !PID!" /fo csv 2>nul | findstr /i "flask.exe" >nul
            if !errorlevel! equ 0 (
                echo [INFO] Terminating Flask process PID: !PID!
                taskkill /f /pid !PID! >nul 2>&1
                set /a CLEANED_PROCESSES+=1
            )
        )
    )
)

if !CLEANED_PROCESSES! gtr 0 (
    echo [INFO] Waiting for processes to terminate...
    timeout /t 2 /nobreak >nul
)

:: Проверка наличия папки static
if not exist "static" (
    echo [WARNING] static folder not found, creating...
    mkdir static
    mkdir static\js
    mkdir static\js\utils
)

:: Проверка базы данных
if not exist "users.db" (
    echo [INFO] Database will be created on first run
)

:: Запуск сервера
echo ========================================
echo  STARTING ALGOISCOOL SERVER
echo ========================================
echo.
echo [INFO] Server URL: http://localhost:2109
echo [INFO] Network URL: http://%COMPUTERNAME%:2109
echo [INFO] Press Ctrl+C to stop the server
echo [INFO] Started at: %date% %time%
echo.

set FLASK_ENV=development
set FLASK_APP=server.py

:: Главный запуск
echo [INFO] Starting Flask server...
python server.py

set EXIT_CODE=%errorlevel%

:: Деактивация виртуального окружения (опционально)
call deactivate >nul 2>&1

echo.
if %EXIT_CODE% equ 0 (
    echo [INFO] Server stopped normally
) else (
    echo [ERROR] Server exited with code: %EXIT_CODE%
    echo.
    echo Troubleshooting:
    echo - Check console for specific error messages
    echo - Verify all file paths in server.py
    echo - Ensure port 2109 is not blocked by firewall
    echo - Check if all dependencies are installed correctly
    echo - Look for Python error messages above
)

echo.
echo [INFO] Server stopped at: %date% %time%
echo Press any key to close...
pause >nul