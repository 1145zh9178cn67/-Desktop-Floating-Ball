@echo off
chcp 65001 >nul
title 悬浮球一键打包
cd /d "%~dp0"

set "PY=%~dp0..\venv_new\Scripts\python.exe"
if not exist "%PY%" (
  echo [!] 未找到 venv_new 虚拟环境，回退到系统 Python
  set "PY=python"
)

echo [1/3] 检查打包依赖（已装则秒过，缺啥装啥）...
"%PY%" -m pip show pyinstaller >nul 2>&1 || "%PY%" -m pip install pyinstaller
"%PY%" -c "import win32clipboard" >nul 2>&1 || "%PY%" -m pip install pywin32
"%PY%" -c "import PIL" >nul 2>&1 || "%PY%" -m pip install pillow
"%PY%" -c "import requests" >nul 2>&1 || "%PY%" -m pip install requests

echo [2/3] 开始打包（约 1-3 分钟，88MB 大文件请耐心）...
"%PY%" -m PyInstaller --onefile --windowed --name "桌面悬浮球" --icon ball.ico --hidden-import win32clipboard --hidden-import PIL.ImageGrab --noconfirm float_ball.pyw
if errorlevel 1 (
  echo.
  echo [X] 打包失败，请把上面的报错信息发给 AI 分析
  pause
  exit /b 1
)

echo [3/3] 把新 EXE 复制回本目录...
copy /y "dist\桌面悬浮球.exe" "桌面悬浮球.exe" >nul
echo.
echo ============================================
echo  完成！桌面悬浮球.exe 已更新到本目录。
echo  使用时与 ball_config.json 放同一目录即可。
echo  （别的电脑首次运行建议先加入杀软白名单）
echo ============================================
pause
