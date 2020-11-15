import sys

from cx_Freeze import Executable, setup

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["os"],
    "excludes": ["tkinter"],
    "include_files": ["resources", "settings.json"],
}

build_dmg_options = {
    "iconfile": "resources/icarus_icon.icns",
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="Icarus",
    version="0.1",
    description="My GUI application!",
    options={"build_exe": build_exe_options, "bdist_mac": build_dmg_options},
    executables=[Executable("main.py", base=base, icon="resources/icarus_icon.png")],
)
