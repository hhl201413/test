@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   心遇助手 - 打包为 EXE
echo ========================================
echo.

if not exist "..\.venv\Scripts\python.exe" (
    if not exist ".venv\Scripts\python.exe" (
        echo [错误] 未找到虚拟环境，请在 test 目录或本目录创建 .venv
        pause
        exit /b 1
    )
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=..\.venv\Scripts\python.exe"
)
set "PIP=%PYTHON% -m pip"

REM 清除可能失效的 pip 代理，避免 ProxyError
set HTTP_PROXY=
set HTTPS_PROXY=
set ALL_PROXY=
set http_proxy=
set https_proxy=
set all_proxy=
set NO_PROXY=*
set no_proxy=*

echo [1/3] 检查并安装打包依赖...

%PYTHON% -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo 正在安装 pyinstaller（清华镜像）...
    %PIP% install pyinstaller requests schedule certifi --proxy "" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
    if errorlevel 1 (
        echo 镜像失败，尝试官方源...
        %PIP% install pyinstaller requests schedule certifi --proxy ""
        if errorlevel 1 (
            echo.
            echo [错误] 依赖安装失败，常见原因：
            echo   1. 网络/代理不可用
            echo   2. pip 配置了无效代理
            echo.
            echo 可手动执行（在 CMD 中）：
            echo   set HTTP_PROXY=^& set HTTPS_PROXY=
            echo   .venv\Scripts\pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
            pause
            exit /b 1
        )
    )
) else (
    echo pyinstaller 已安装，跳过下载。
)

%PYTHON% -c "import requests, schedule" >nul 2>&1
if errorlevel 1 (
    echo 正在安装 requests / schedule...
    %PIP% install requests schedule --proxy "" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
)

%PYTHON% -c "import certifi" >nul 2>&1
if errorlevel 1 (
    echo 正在安装 certifi...
    %PIP% install certifi --proxy "" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
)

set "PYI_ARGS=--onefile --windowed --name 心遇助手 --clean --collect-data certifi --collect-data requests --hidden-import certifi"

echo [2/3] 开始打包...
if exist "%~dp0..\.venv\Scripts\pyinstaller.exe" (
    set "PYINSTALLER=%~dp0..\.venv\Scripts\pyinstaller.exe"
) else if exist "%~dp0.venv\Scripts\pyinstaller.exe" (
    set "PYINSTALLER=%~dp0.venv\Scripts\pyinstaller.exe"
) else (
    set "PYINSTALLER=%PYTHON% -m PyInstaller"
)

%PYINSTALLER% %PYI_ARGS% 签到.py
if errorlevel 1 (
    echo.
    echo [提示] 中文文件名打包失败，尝试使用 app.py...
    copy /Y 签到.py app.py >nul
    %PYINSTALLER% %PYI_ARGS% app.py
    if errorlevel 1 (
        echo [错误] 打包失败
        pause
        exit /b 1
    )
)

echo.
echo [3/3] 打包完成！
echo.
echo EXE 位置: %~dp0dist\心遇助手.exe
echo.
echo 请将 dist\心遇助手.exe 复制到固定文件夹后使用。
echo 账号等配置会保存在 data 目录（exe 旁）或运行目录。
echo.
pause
