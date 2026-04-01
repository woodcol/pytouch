@echo off
chcp 65001 >nul
title 串口调试工具打包器

:: 隐藏命令行窗口
if not "%1"=="hide" (
    start /b "" cmd /c "%~f0" hide
    exit
)

:: 设置变量
set APP_NAME=串口控制工具
set PYTHON_FILE=main.py
set ICON_FILE=icon.ico

echo ========================================
echo    正在打包，请稍候...
echo ========================================
echo.

:: 检查并安装pyinstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 正在安装pyinstaller...
    pip install pyinstaller -q
    echo.
)

:: 检查图标文件
if exist "%ICON_FILE%" (
    set ICON_OPTION=--icon=%ICON_FILE%
    echo 使用图标: %ICON_FILE%
) else (
    set ICON_OPTION=
    echo 警告: 未找到图标文件
)
echo.

:: 清理旧文件
if exist "build" rmdir /s /q build >nul 2>&1
if exist "dist" rmdir /s /q dist >nul 2>&1
if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec" >nul 2>&1

:: 开始打包
echo 正在打包程序...
pyinstaller --onefile --windowed %ICON_OPTION% --name="%APP_NAME%" --hidden-import=serial --hidden-import=serial.tools.list_ports --noconfirm %PYTHON_FILE% >nul 2>&1

if errorlevel 1 (
    echo.
    echo 打包失败！请检查Python环境
    pause
    exit
)

echo.
echo ========================================
echo    打包完成！
echo    文件位置: dist\%APP_NAME%.exe
echo ========================================

:: 自动打开输出目录
start explorer dist

:: 3秒后自动关闭
timeout /t 3 /nobreak >nul
exit