@echo off
chcp 65001 >nul

REM 获取批处理文件所在的目录并切换到该目录
cd /d "%~dp0"
echo 当前工作目录: %CD%
echo.
echo 启动 Minecraft 区块重置器 GUI...
echo.

echo 检查Conda环境...
where conda >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Conda，请先安装Anaconda或Miniconda
    echo 或者手动激活Python环境后运行: python ChunkResetterGUI.py
    pause
    exit
)

echo 激活amulet环境...
call conda activate amulet
if errorlevel 1 (
    echo 警告: 无法激活amulet环境，尝试使用默认环境
    echo 如果遇到依赖问题，请手动创建环境: conda create -n amulet python=3.9
)

echo.
echo 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请检查conda环境
    pause
    exit
)

echo.
echo 检查依赖包...
python -c "import tkinter; print('tkinter: OK')" 2>nul
if errorlevel 1 (
    echo 警告: tkinter不可用，GUI可能无法启动
)

python -c "import amulet; print('amulet-core: OK')" 2>nul
if errorlevel 1 (
    echo 警告: amulet-core未安装，尝试自动安装...
    pip install amulet-core
    if errorlevel 1 (
        echo 错误: amulet-core安装失败
        echo 请手动安装: conda install -c conda-forge amulet-core
        echo 或者: pip install amulet-core
        pause
        exit
    )
)

echo.
echo 检查项目文件...
if not exist "ChunkResetterGUI.py" (
    echo ❌ 错误: 找不到 ChunkResetterGUI.py 文件
    echo 请确保批处理文件在正确的项目目录中
    echo 当前目录: %CD%
    pause
    exit
)

if not exist "ChunkAutoResetter.py" (
    echo ❌ 错误: 找不到 ChunkAutoResetter.py 文件
    echo 请确保所有项目文件都在当前目录中
    pause
    exit
)

if not exist "land_data_reader.py" (
    echo ❌ 错误: 找不到 land_data_reader.py 文件
    echo 请确保所有项目文件都在当前目录中
    pause
    exit
)

echo ✅ 项目文件检查完成
echo.
echo 启动GUI界面...
python ChunkResetterGUI.py

echo.
echo GUI已关闭
pause
