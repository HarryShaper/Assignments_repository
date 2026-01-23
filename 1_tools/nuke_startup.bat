@echo off

::Set Nuke version variable
set "NUKE_VERSION=16.0"

::Set Nuke path
set "NUKE_PATH=C:\Program Files\Nuke16.0v1\%NUKE_VERSION%"

::Custom plugin path
set "NUKE_PLUGIN_PATH=C:\Program Files\Nuke16.0v1\plugins;%NUKE_PLUGIN_PATH%"

::Add custom script path overwrite
set "SCRIPT_PATH=D:\VFX\assets_and_courses\courses\Advanced_python_course\course_notes\nuke_test_folder"
set "PYTHON_PATH=%SCRIPT_PATH%;%PYTHON_PATH%"


:: Start Nuke
start "" "C:\Program Files\Nuke16.0v1\Nuke16.0.exe"

exit