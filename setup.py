import sys
import subprocess
from cx_Freeze import setup, Executable
#stuff if using pystray
#force pysystray without a desktop
#pystray_path = subprocess.check_output(
#    [sys.executable, '-c', 
#     'import importlib.util; import os; '
#     'spec = importlib.util.find_spec("pystray"); '
#     'print(os.path.dirname(spec.origin))'],
#    text=True
#).strip()

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {
    'packages': [],
    'include_files': [],
    'zip_exclude_packages': [],
    'excludes': [],
}

base = 'gui'

directory_table = [
    ("ProgramMenuFolder", "TARGETDIR", "."),
    ("MyProgramMenu", "ProgramMenuFolder", "MYPROG~1|My Program"),
]

msi_data = {
    "Directory": directory_table,
    "ProgId": [
        ("Prog.Id", "2026.05.26.1", None, "Scale your avatar over OSC", "IconId", None),
    ],
    "Icon": [
        ("IconId", "open_vrc_scaler_icon.ico"),
    ],
    "Shortcut": [
        ("DesktopShortcut", "DesktopFolder", "OpenVRCScaler",
         "TARGETDIR", "[TARGETDIR]open_vrc_scaler.exe",
         None, None, None, None, None, None, "TARGETDIR"),
        ("StartMenuShortcut", "MyProgramMenu", "OpenVRCScaler",
         "TARGETDIR", "[TARGETDIR]open_vrc_scaler.exe",
         None, None, None, None, None, None, "TARGETDIR"),
    ],
}

bdist_msi_options = {
    "add_to_path": True,
    "data": msi_data,
    "upgrade_code": "{ae44905e-0759-43b3-813c-a31f3483d407}",
    "output_name": "OpenVRCScaler.msi",
}
bdist_appimage_options = {
    "target_name": "OpenVRCScaler.AppImage",
}

# Pick the right icon per platform
if sys.platform == "win32":
    icon = 'open_vrc_scaler_icon.ico'
else:
    icon = 'open_vrc_scaler_icon.svg'

executables = [
    Executable(
        'open_vrc_scaler.py',
        base=base,
        icon=icon,
    ),
]

setup(name='OpenVRCScaler',
      version = '2026.05.26.1',
      description = "Change your avatar's scale over osc",
      license = "MIT License",
      options = {
      'build_exe': build_options,
      'bdist_msi': bdist_msi_options,
      'bdist_appimage': bdist_appimage_options,
      },
      executables = executables)
