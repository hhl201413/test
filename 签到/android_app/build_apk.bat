@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   心遇助手 - 打包 APK
echo ========================================
echo.

REM 检查 WSL
wsl --status >nul 2>&1
if errorlevel 1 (
    echo [提示] 本机未安装 WSL，Windows 无法直接打 APK。
    echo.
    echo 请先安装 WSL2 + Ubuntu（管理员 PowerShell 执行一次）:
    echo   wsl --install -d Ubuntu
    echo.
    echo 安装后重启电脑，再双击本脚本。
    echo.
    echo 或手动在 Ubuntu 终端执行:
    echo   cd /mnt/c/Users/MY/PyCharmMiscProject/test/签到/android_app
    echo   bash build_apk.sh
    pause
    exit /b 1
)

echo 正在通过 WSL2 打包，请耐心等待...
echo 首次打包会下载 Android SDK/NDK，可能需要 30~90 分钟。
echo.

REM 转换 Windows 路径为 WSL 路径并执行
for /f "delims=" %%i in ('wsl wslpath -a "%CD%"') do set WSL_DIR=%%i

wsl bash -lc "cd '%WSL_DIR%' && sed -i 's/\r$//' build_apk.sh && chmod +x build_apk.sh && bash build_apk.sh"

if errorlevel 1 (
    echo.
    echo [错误] 打包失败，请查看上方日志
    pause
    exit /b 1
)

echo.
if exist "bin\*.apk" (
    echo APK 已生成:
    dir /b bin\*.apk
    echo.
    echo 完整路径: %CD%\bin\
) else (
    echo 请在 WSL 中查看 bin 目录下的 apk 文件
)
echo.
pause
