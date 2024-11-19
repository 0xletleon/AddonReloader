@echo off
setlocal enabledelayedexpansion

:: 设置插件的基本名称，不包含版本号
set BASENAME=addon_reloader

:: 遍历当前目录下所有匹配的文件
for %%f in (%BASENAME%-*.zip) do (
    echo Found addon: %%f
    "D:\Apps\Blender\Blender 4.2.3\blender.exe" --command extension validate "%%f"
)

pause