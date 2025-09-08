@echo off
chcp 65001 >nul
title PDF智能分析助手 - 打包工具

echo ========================================
echo    PDF智能分析助手 - 打包工具
echo ========================================
echo.

echo 正在检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误：未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo.
echo 正在检查PyInstaller...
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo 正在安装PyInstaller...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo 错误：PyInstaller安装失败
        pause
        exit /b 1
    )
)

echo.
echo 开始打包...
python build_exe.py

echo.
echo 打包完成！按任意键退出...
pause >nul