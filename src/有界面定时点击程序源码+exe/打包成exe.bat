@echo off
echo ========================================
echo   串口定时控制器 打包工具
echo ========================================
echo.

REM 检查必要文件是否存在
if not exist "main.py" (
    echo 错误: 找不到主程序文件 main.py
    pause
    exit /b 1
)

if not exist "timetool.py" (
    echo 警告: 找不到 timetool.py，程序可能无法正常运行
)

echo 正在清理旧文件...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "SerialTimer.spec" del SerialTimer.spec

echo.
echo 开始打包程序...
echo.

REM 执行打包命令
pyinstaller --onefile --windowed --name="SerialTimer" --add-data="timetool.py;." --add-data="timer.txt;." --add-data="config.txt;." --icon=icon.ico --hidden-import=serial --hidden-import=timetool main.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   打包成功！
    echo   生成的exe文件：dist\串口定时控制器.exe
    echo ========================================
) else (
    echo.
    echo ========================================
    echo   打包失败！
    echo ========================================
)

echo.
pause