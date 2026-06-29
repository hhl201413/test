#!/bin/bash
# 在 WSL2 (Ubuntu) 中执行，用于打包 APK
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

MIRROR="-i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn"

echo "========================================"
echo "  心遇助手 - Buildozer 打包 APK"
echo "========================================"
echo "工作目录: $SCRIPT_DIR"
echo

echo "[1/4] 安装系统依赖..."
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y -qq \
  git zip unzip openjdk-17-jdk python3-pip python3-venv \
  autoconf libtool pkg-config zlib1g-dev \
  libncurses5-dev libncursesw5-dev libtinfo5 cmake \
  libffi-dev libssl-dev

echo "[2/4] 安装 buildozer..."
python3 -m pip install --user -U pip buildozer cython $MIRROR
export PATH="$HOME/.local/bin:$PATH"

echo "[3/4] 检查中文字体..."
if [ ! -f fonts/msyh.ttc ] && [ ! -f fonts/simhei.ttf ]; then
  echo "未找到 fonts/ 中文字体，从 Windows 复制..."
  WIN_FONT="/mnt/c/Windows/Fonts/msyh.ttc"
  if [ -f "$WIN_FONT" ]; then
    mkdir -p fonts
    cp "$WIN_FONT" fonts/msyh.ttc
  else
    echo "警告: 未找到中文字体，APK 内中文可能乱码"
  fi
fi

echo "[4/4] 开始打包（首次约 30~90 分钟，需下载 Android SDK/NDK）..."
buildozer -v android debug

echo
echo "========================================"
echo "打包完成！APK 位置:"
ls -lh bin/*.apk 2>/dev/null || ls -lh bin/
echo "========================================"
