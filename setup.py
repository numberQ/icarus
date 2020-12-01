import sys

from cx_Freeze import Executable, setup

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["os"],
    "excludes": ["tkinter"],
    "include_files": ["resources", "settings.json"],
    "include_msvcr": True,
}

bdist_msi_options = {
    "upgrade_code": "{91f52be7-4647-406e-b7f0-345827db5969}",
    "install_icon": "resources/icarus_icon.ico",
}

build_dmg_options = {
    "iconfile": "resources/icarus_icon.icns",
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
icon = None
if sys.platform == "win32":
    base = "Win32GUI"
    icon = "resources/icarus_icon.ico"

setup(
    name="Icarus",
    version="1.0",
    description="Shoot for the moon",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
        "bdist_mac": build_dmg_options,
    },
    executables=[
        Executable(
            "main.py",
            base=base,
            shortcutName="Icarus",
            shortcutDir="DesktopFolder",
            icon=icon,
        )
    ],
)
