from distutils.core import setup
from py2exe.build_exe import py2exe as build_exe

import os, babelfish, guessit

class AutoMoverCollector(build_exe):
    def copy_extensions(self, extensions):
        build_exe.copy_extensions(self, extensions)

        # Define the data path where the files reside.
        data_path = os.path.join(babelfish.__path__[0], 'data')
        #print data_path

        # Create the subdir where the json files are collected.
        media = os.path.join('babelfish', 'data')
        #print media
        full = os.path.join(self.collect_dir, media)
        #print full
        self.mkpath(full)

        # Copy the json files to the collection dir. Also add the copied file
        # to the list of compiled files so it will be included in the zipfile.
        for name in os.listdir(data_path):
            file_name = os.path.join(data_path, name)
            self.copy_file(file_name, os.path.join(full, name))
            #print "copy_file", file_name, os.path.join(full, name)
            self.compiled_files.append(os.path.join(media, name))
            #print "compiled_files.append", os.path.join(media, name)

        data_path = os.path.join(guessit.__path__[0], '')
        media = os.path.join('guessit')
        full = os.path.join(self.collect_dir, media)
        self.mkpath(full)

        for name in os.listdir(data_path):
            if 'tlds-alpha-by-domain.txt' == name:
                file_name = os.path.join(data_path, name)
                self.copy_file(file_name, os.path.join(full, name))
                self.compiled_files.append(os.path.join(media, name))

includes = ["babelfish.converters.*"]
packages = []
excludes = [
    "pywin",
    "pywin.debugger",
    "pywin.debugger.dbgcon",
    "pywin.dialogs",
    "pywin.dialogs.list",
    "win32com.server",
]
dll_excludes = ["w9xpopen.exe"]

options = {"bundle_files": 1,    # Bundle ALL files inside the EXE
           "compressed": 2,      # compress the library archive
           "optimize": 2,        # like python -OO
           "includes": includes,
           "packages": packages, # Packages needed by lxml.
           "excludes": excludes, # COM stuff we don't want
           "dll_excludes": dll_excludes} # Exclude unused DLLs

setup(
    cmdclass={"py2exe": AutoMoverCollector},
    options={"py2exe": options},
    zipfile=None,
    console=['AutoMover.py'])