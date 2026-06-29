@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   使用国内镜像安装 Kivy
echo ========================================
echo.

REM 清除可能失效的代理
set HTTP_PROXY=
set HTTPS_PROXY=
set ALL_PROXY=
set http_proxy=
set https_proxy=
set all_proxy=
set NO_PROXY=*
set no_proxy=*

set "MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple"
set "HOST=pypi.tuna.tsinghua.edu.cn"
set "PIP_ARGS=-i %MIRROR% --trusted-host %HOST%"

if exist "..\..\.venv\Scripts\python.exe" (
    set "PYTHON=..\..\.venv\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    echo 未找到 .venv，使用系统 python
    set "PYTHON=python"
)

set "PIP=%PYTHON% -m pip"

echo 使用 Python: %PYTHON%
echo 镜像源: %MIRROR%
echo.

echo [1/3] 升级 pip...
%PIP% install --upgrade pip %PIP_ARGS% -q

echo [2/3] 安装 Kivy（清华镜像）...
%PIP% install "kivy[base]" %PIP_ARGS%
if errorlevel 1 (
    echo 清华镜像失败，尝试阿里云镜像...
    %PIP% install "kivy[base]" -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
    if errorlevel 1 (
        echo [错误] Kivy 安装失败
        pause
        exit /b 1
    )
)

echo [3/3] 安装 requests...
%PIP% install requests certifi %PIP_ARGS%

echo.
echo 验证安装...
%PYTHON% -c "import kivy; print('Kivy 版本:', kivy.__version__)"
if errorlevel 1 (
    echo [错误] Kivy 导入失败
    pause
    exit /b 1
)

echo.
echo 安装完成！运行 Android 界面预览：
echo   %PYTHON% main.py
echo.
pause
