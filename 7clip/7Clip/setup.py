from distutils.core import setup
from py2exe.build_exe import py2exe as build_exe

import os

includes = []
packages = []
excludes = ["pywin",
    "pywin.debugger",
    "pywin.debugger.dbgcon",
    "pywin.dialogs",
    "pywin.dialogs.list",
    "win32com.server",]
dll_excludes = ["w9xpopen.exe"]

mfcfiles = [os.path.join("C:\\Python27\\Lib\\site-packages\\pythonwin", i) for i in ["mfc90.dll", "mfc90u.dll", "mfcm90.dll", "mfcm90u.dll", "Microsoft.VC90.MFC.manifest"]]
data_files = [("Microsoft.VC90.MFC", mfcfiles),]

options = {
    "bundle_files": 1,
    "compressed": 1,
    "optimize": 2,
    "includes": includes,
    "packages": packages,
    "excludes": excludes,
    "dll_excludes": dll_excludes
}
 
setup(
    console = ["7Clip.py"],
    options = {"py2exe" : options},
    #data_files = data_files,
    zipfile = None
)
