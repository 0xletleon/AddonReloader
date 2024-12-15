@echo off
setlocal enabledelayedexpansion

:: 遍历当前目录下所有.zip文件
for %%f in (*.zip) do (
    echo Found zip file: %%f
    "D:\Apps\Blender\Blender 4.2.3\blender.exe" --command extension validate "%%f"
)

pause