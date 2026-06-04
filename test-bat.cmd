@echo off
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
cd /d "%ROOT%"
set "PYTHON=python"
set "FAIL=0"

if not exist "%ROOT%logs" mkdir "%ROOT%logs"
if not exist "%ROOT%output" mkdir "%ROOT%output"

echo === Edge TTS BAT 自动化测试 ===
echo.

echo [1/6] 读取端口
for /f "delims=" %%i in ('%PYTHON% manage.py get-port') do set "PORT=%%i"
echo 端口=!PORT!

echo [2/6] 读取音色
for /f "delims=" %%i in ('%PYTHON% manage.py get-voice') do set "VOICE=%%i"
echo 音色=!VOICE!

echo [3/6] 启动服务
start "" /MIN cmd /c "cd /d ""%ROOT%"" && ""%PYTHON%"" -m app.main >> ""%ROOT%logs\server.log"" 2>&1"
set "WAIT=0"
:wait_up
ping -n 2 127.0.0.1 >nul
%PYTHON% manage.py is-running >nul 2>&1
if not errorlevel 1 goto started
set /a WAIT+=1
if !WAIT! geq 20 set FAIL=1 & goto fail_start
goto wait_up
:started
echo 服务已启动

echo [4/6] 健康检查
%PYTHON% manage.py health
if errorlevel 1 set FAIL=1

echo [5/6] 测试合成
%PYTHON% manage.py test-tts "bat自动化测试" "%ROOT%output\smoke-test.mp3"
if errorlevel 1 set FAIL=1

echo [6/6] 停止服务
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":!PORT!" ^| findstr "LISTENING"') do taskkill /PID %%a /F >nul 2>&1
ping -n 2 127.0.0.1 >nul
%PYTHON% manage.py is-running >nul 2>&1
if not errorlevel 1 (
    echo 停止失败
    set FAIL=1
) else (
    echo 服务已停止
)

if "!FAIL!"=="1" goto fail_end
echo.
echo 全部测试通过
exit /b 0

:fail_start
echo 启动失败
:fail_end
echo.
echo 测试失败
exit /b 1
