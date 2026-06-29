@echo off
chcp 65001 >nul

echo ========================================
echo   WSL 离线安装助手（需管理员权限）
echo ========================================
echo.
echo 本脚本只启用 Windows 功能，不联网下载 Ubuntu。
echo Ubuntu 需按 WSL安装说明.txt 手动下载 rootfs 导入。
echo.

net session >nul 2>&1
if errorlevel 1 (
    echo [错误] 请右键「以管理员身份运行」本脚本
    pause
    exit /b 1
)

echo [1/3] 启用「适用于 Linux 的 Windows 子系统」...
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

echo [2/3] 启用「虚拟机平台」...
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

echo [3/3] 重置 WinHTTP 代理（避免下载失败）...
netsh winhttp reset proxy

echo.
echo ========================================
echo 完成！请重启电脑。
echo.
echo 重启后：
echo   1. 浏览器安装 https://aka.ms/wsl2kernel
echo   2. 执行: wsl --set-default-version 2
echo   3. 按 WSL安装说明.txt 导入 Ubuntu rootfs
echo ========================================
pause
