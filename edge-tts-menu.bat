@echo off
setlocal EnableDelayedExpansion

set "ROOT=%~dp0"
cd /d "%ROOT%"

set "PYTHON=python"
set "LOG_DIR=%ROOT%logs"
set "LOG_FILE=%LOG_DIR%\server.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%ROOT%output" mkdir "%ROOT%output"
if not exist "%ROOT%config" mkdir "%ROOT%config"

where %PYTHON% >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+ 并加入 PATH
    pause
    exit /b 1
)

:menu
cls
call :refresh_status
echo ========================================
echo   Edge TTS API 控制面板
echo ========================================
echo.
echo  服务地址: http://127.0.0.1:!SERVER_PORT!
echo  当前音色: !CURRENT_VOICE!
if "!RUNNING!"=="1" (
    echo  服务状态: [运行中]
) else (
    echo  服务状态: [已停止]
)
echo.
echo  [1] 安装依赖
echo  [2] 启动服务
echo  [3] 停止服务
echo  [4] 重启服务
echo  [5] 切换音色
echo  [6] 测试合成
echo  [7] 查看状态
echo  [8] 查看配置
echo  [9] 修改端口
echo  [0] 切换鉴权开关
echo  [Q] 退出
echo.
set "CHOICE="
set /p "CHOICE=请选择: "
if /i "!CHOICE!"=="1" goto install_deps
if /i "!CHOICE!"=="2" goto start_server
if /i "!CHOICE!"=="3" goto stop_server
if /i "!CHOICE!"=="4" goto restart_server
if /i "!CHOICE!"=="5" goto switch_voice
if /i "!CHOICE!"=="6" goto test_tts
if /i "!CHOICE!"=="7" goto show_status
if /i "!CHOICE!"=="8" goto show_config
if /i "!CHOICE!"=="Q" goto end
if /i "!CHOICE!"=="9" goto change_port
if /i "!CHOICE!"=="0" goto toggle_auth
echo 无效选项，请重试。
ping -n 3 127.0.0.1 >nul
goto menu

:refresh_status
set "SERVER_PORT=9880"
set "CURRENT_VOICE=zh-CN-XiaoxiaoNeural"
set "RUNNING=0"
for /f "delims=" %%i in ('%PYTHON% manage.py get-port 2^>nul') do set "SERVER_PORT=%%i"
for /f "delims=" %%i in ('%PYTHON% manage.py get-voice 2^>nul') do set "CURRENT_VOICE=%%i"
%PYTHON% manage.py is-running >nul 2>&1
if not errorlevel 1 set "RUNNING=1"
exit /b 0

:install_deps
cls
echo 正在安装依赖...
%PYTHON% -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo.
    echo [警告] 清华源安装失败，尝试默认源...
    %PYTHON% -m pip install -r requirements.txt
)
echo.
echo 依赖安装完成。
pause
goto menu

:start_server
call :refresh_status
if "!RUNNING!"=="1" (
    echo 服务已在运行中，无需重复启动。
    pause
    goto menu
)
cls
echo 正在启动 Edge TTS API 服务...
echo 日志文件: %LOG_FILE%
start "" /MIN cmd /c "cd /d ""%ROOT%"" && ""%PYTHON%"" -m app.main >> ""%LOG_FILE%"" 2>&1"
echo 等待服务就绪...
set "WAIT_COUNT=0"
:wait_start
ping -n 2 127.0.0.1 >nul
%PYTHON% manage.py is-running >nul 2>&1
if not errorlevel 1 goto start_ok
set /a WAIT_COUNT+=1
if !WAIT_COUNT! geq 15 (
    echo [错误] 服务启动超时，请查看日志: %LOG_FILE%
    pause
    goto menu
)
goto wait_start
:start_ok
echo.
echo 服务已启动: http://127.0.0.1:!SERVER_PORT!
echo API 文档: http://127.0.0.1:!SERVER_PORT!/docs
pause
goto menu

:stop_server
call :refresh_status
if not "!RUNNING!"=="1" (
    echo 服务当前未运行。
    if not defined NO_PAUSE pause
    if not defined INTERNAL_CALL goto menu
    exit /b 0
)
cls
echo 正在停止服务，端口 !SERVER_PORT! ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":!SERVER_PORT!" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)
ping -n 2 127.0.0.1 >nul
call :refresh_status
if "!RUNNING!"=="1" (
    echo [警告] 停止可能未完全成功，请手动检查进程。
) else (
    echo 服务已停止。
)
if not defined NO_PAUSE pause
if not defined INTERNAL_CALL goto menu
exit /b 0

:restart_server
set "INTERNAL_CALL=1"
set "NO_PAUSE=1"
call :stop_server
set "INTERNAL_CALL="
set "NO_PAUSE="
call :start_server
goto menu

:switch_voice
cls
echo 可选音色列表，星号表示当前默认音色:
echo.
%PYTHON% manage.py list-presets
echo.
set "VOICE_ID="
set /p "VOICE_ID=请输入音色编号: "
if "!VOICE_ID!"=="" (
    echo 已取消。
    pause
    goto menu
)
%PYTHON% manage.py set-voice-id !VOICE_ID!
if errorlevel 1 (
    pause
    goto menu
)
echo.
echo 默认音色已更新，无需重启服务。
pause
goto menu

:test_tts
call :refresh_status
if not "!RUNNING!"=="1" (
    echo 请先启动服务再测试。
    pause
    goto menu
)
cls
set "TEST_TEXT=你好，这是 Edge TTS 测试。"
set /p "TEST_TEXT=请输入测试文本，直接回车使用默认: "
echo.
echo 正在合成...
%PYTHON% manage.py test-tts "!TEST_TEXT!" "%ROOT%output\test.mp3"
echo.
if exist "%ROOT%output\test.mp3" (
    echo 是否播放测试音频? [Y/N]
    set "PLAY="
    set /p "PLAY="
    if /i "!PLAY!"=="Y" start "" "%ROOT%output\test.mp3"
)
pause
goto menu

:show_status
cls
echo === 服务状态 ===
%PYTHON% manage.py health
echo.
echo === 最近日志，末尾 20 行 ===
if exist "%LOG_FILE%" (
    powershell -NoProfile -Command "Get-Content -Path '%LOG_FILE%' -Tail 20 -ErrorAction SilentlyContinue"
) else (
    echo 暂无日志
)
pause
goto menu

:show_config
cls
%PYTHON% manage.py show-config
pause
goto menu

:change_port
cls
call :refresh_status
echo 当前端口: !SERVER_PORT!
set "NEW_PORT="
set /p "NEW_PORT=请输入新端口: "
if "!NEW_PORT!"=="" (
    echo 已取消。
    pause
    goto menu
)
if not "!RUNNING!"=="1" goto apply_port
echo.
echo 检测到服务正在运行，修改端口需要先停止服务。
set "CONFIRM="
set /p "CONFIRM=是否停止服务并修改端口? [Y/N]: "
if /i not "!CONFIRM!"=="Y" goto menu
set "INTERNAL_CALL=1"
set "NO_PAUSE=1"
call :stop_server
set "INTERNAL_CALL="
set "NO_PAUSE="
:apply_port
%PYTHON% manage.py set-port !NEW_PORT!
pause
goto menu

:toggle_auth
cls
echo 当前配置:
%PYTHON% manage.py show-config
echo.
echo 是否开启 API 鉴权? 开启后请求需带 Authorization Bearer 密钥
echo  [1] 开启鉴权
echo  [2] 关闭鉴权
set "AUTH_CHOICE="
set /p "AUTH_CHOICE=请选择: "
if "!AUTH_CHOICE!"=="1" (
    %PYTHON% manage.py toggle-auth on
) else if "!AUTH_CHOICE!"=="2" (
    %PYTHON% manage.py toggle-auth off
) else (
    echo 已取消。
)
pause
goto menu

:end
echo 再见。
exit /b 0
