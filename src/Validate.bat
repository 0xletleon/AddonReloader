@echo off
setlocal enabledelayedexpansion

:: Verify extension file
for %%f in (*.zip) do (
    echo Found zip file: %%f
    "D:\Apps\Blender\4.5.0\blender.exe" --command extension validate "%%f"
)

pause