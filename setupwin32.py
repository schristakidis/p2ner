#!/usr/bin/env python
#   Copyright 2012 Loris Corazza, Sakis Christakidis
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


from setuptools import find_packages
#from distutils.core import setup
#import py2exe
from cx_Freeze import setup, Executable
import os
import sys
import shutil
from optparse import OptionParser
import p2ner
import p2ner.abstract
import p2ner.base
import glob


class Deploy():

    def __init__(self, gtkPath, crtPath, defaultTheme):
        self.gtkPath = gtkPath
        self.crtPath = crtPath
        self.defaultTheme = defaultTheme
        self.setPathVariables()
        self.createDeploymentFolder()
        self.setPath()
        self.checkDependencies()
        self.deploy_eggs()
        self.deployCRT()
        self.deployGTK()
        self.runCx_FreezeSetup()
        self.makeInstaller()
        self.close()

    def deploy_eggs(self):
        from p2ner.core.components import _entry_points
        from sys import executable
        excludes=['vlcoutput', 'gstinput','gstoutput']
        cd =  os.path.dirname( os.path.realpath( __file__ ) )
        COMPONENTS_DIR = os.path.join(cd, "p2ner", "components")
        os.system(executable + " setup.py bdist_egg --exclude-source-files")
        for name in glob.glob(os.path.join(cd, 'dist', '*.egg')):
            shutil.copy (os.path.join(cd, 'dist', name),
                    self.dist_dir)
        for ct in _entry_points:
            d = os.path.join(COMPONENTS_DIR, ct)
            directories = [os.path.join(d, dirname) for dirname in os.listdir(d) if os.path.isdir(os.path.join(d,dirname)) and dirname[0]!="." and dirname.lower() not in excludes]
            for p in directories:
                cpath = os.path.join(d, p)
                c = "cd " + cpath + " && del /F /Q build dist && " + executable + " setup.py bdist_egg  --exclude-source-files"
                os.system(c)
                for name in glob.glob(os.path.join(cpath, 'dist', '*.egg')):
                    shutil.copy (os.path.join(cpath, 'dist', name),
                    self.dist_dir)

    def close(self, message=None):
        if message is not None:
            print 'ERROR: %s' % message
            exit(1)
        else:
            exit(0)

    def setPathVariables(self):
        self.curr_dir = os.getcwd()

        self.root_dir = os.path.abspath(self.curr_dir)
        self.installer_dir = os.path.join (self.root_dir, 'win32')
        self.dist_dir = os.path.join (self.root_dir, 'win32', 'dist')
        self.lib_dir = os.path.join (self.dist_dir, 'lib')
        self.etc_dir = os.path.join (self.dist_dir, 'etc')
        self.share_dir = os.path.join (self.dist_dir, 'share')
        self.defaulttheme_dir = os.path.join (self.share_dir, 'themes', 'Default')
        self.crt_dir = os.path.join (self.dist_dir, 'Microsoft.VC90.CRT')

    def setPath(self):
        # Add root folder to the python path for p2ner
        sys.path.insert(0, self.root_dir)
        # Add site-packages folrder for pygst
        # sys.path.insert(0, os.path.join(self.gstPath, 'lib', 'site-packages'))
        # Add Gtk and GStreamer folder to the system path
        for folder in [self.gtkPath]:
            os.environ['PATH'] = os.environ['PATH']+';'+os.path.join(folder, 'bin')
        sys.path.insert(0, os.path.join(self.curr_dir, 'site-packages'))
        os.environ['PATH'] = os.environ['PATH']+';'+self.dist_dir

    def createDeploymentFolder(self):
        print ('Create deployment directory')
        if os.path.exists(self.dist_dir):
            try:
                shutil.rmtree(self.dist_dir)
            except :
                self.close("ERROR: Can't delete folder %s"%self.dist_dir)
        installer = os.path.join(self.installer_dir, 'setup.exe')
        if os.path.exists(installer):
            try:
                os.remove(installer)
            except:
                self.close("ERROR: Can't delete %s"%installer)

        os.makedirs(self.dist_dir)

    def checkDependencies(self):
        print ('Checking dependencies')

        try:
            import pygtk
            pygtk.require('2.0')
            import gtk
            import gtk.gdk
            import gobject
        except ImportError:
                self.close('IMPORT_ERROR: Could not find the Gtk Python bindings.\n'
                    'You can download the installers at:\n'
                    'http://www.pygtk.org/\n'
                    'http://www.gtk.org/')
        else:
            print ('Gtk... OK')

        try:
            import zope.interface
        except:
            self.close('ERROR: Could not find Zope.Interface')
        else:
            print ('zope.interface... OK')

        if os.path.isfile(os.path.join(self.crtPath, 'msvcr90.dll')):
            print ('MS VC++ 2008 Runtime... OK')
        else:
            print ("could not find msvcr90.dll in %s, please install it or set up the file path properly through command line options" % (self.crtPath))


    def deployCRT(self):
        print ('Deploying MS Visual C++ 2008 Runtime')
        shutil.copytree(self.crtPath, self.crt_dir)
        crtManifest = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n\
<!-- Copyright (c) Microsoft Corporation.  All rights reserved. -->\n\
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">\n\
    <noInheritable></noInheritable>\n\
    <assemblyIdentity type="win32" name="Microsoft.VC90.CRT" version="9.0.21022.8" processorArchitecture="x86" publicKeyToken="1fc8b3b9a1e18e3b"></assemblyIdentity>\n\
    <file name="msvcr90.dll" hashalg="SHA1" hash="e0dcdcbfcb452747da530fae6b000d47c8674671"><asmv2:hash xmlns:asmv2="urn:schemas-microsoft-com:asm.v2" xmlns:dsig="http://www.w3.org/2000/09/xmldsig#"><dsig:Transforms><dsig:Transform Algorithm="urn:schemas-microsoft-com:HashTransforms.Identity"></dsig:Transform></dsig:Transforms><dsig:DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"></dsig:DigestMethod><dsig:DigestValue>KSaO8M0iCtPF6YEr79P1dZsnomY=</dsig:DigestValue></asmv2:hash></file> <file name="msvcp90.dll" hashalg="SHA1" hash="81efe890e4ef2615c0bb4dda7b94bea177c86ebd"><asmv2:hash xmlns:asmv2="urn:schemas-microsoft-com:asm.v2" xmlns:dsig="http://www.w3.org/2000/09/xmldsig#"><dsig:Transforms><dsig:Transform Algorithm="urn:schemas-microsoft-com:HashTransforms.Identity"></dsig:Transform></dsig:Transforms><dsig:DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"></dsig:DigestMethod><dsig:DigestValue>ojDmTgpYMFRKJYkPcM6ckpYkWUU=</dsig:DigestValue></asmv2:hash></file> <file name="msvcm90.dll" hashalg="SHA1" hash="5470081b336abd7b82c6387567a661a729483b04"><asmv2:hash xmlns:asmv2="urn:schemas-microsoft-com:asm.v2" xmlns:dsig="http://www.w3.org/2000/09/xmldsig#"><dsig:Transforms><dsig:Transform Algorithm="urn:schemas-microsoft-com:HashTransforms.Identity"></dsig:Transform></dsig:Transforms><dsig:DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"></dsig:DigestMethod><dsig:DigestValue>tVogb8kezDre2mXShlIqpp8ErIg=</dsig:DigestValue></asmv2:hash></file>\n\
</assembly>\n'
        #ertfile = open(os.path.join(self.crt_dir, 'Microsoft.VC90.CRT.manifest'), 'w')
        #ertfile.write(crtManifest)
        #ertfile.close()

    def deployGTK(self):
        print ('Deploying Gtk dependencies')
        # Copy Gtk files to the dist folder
        for name in ['fonts', 'pango', 'gtk-2.0']:
            shutil.copytree(os.path.join(self.gtkPath, 'etc', name),
                     os.path.join(self.etc_dir, name))
        shutil.copytree(os.path.join(self.gtkPath, 'lib', 'gtk-2.0'),
            os.path.join(self.lib_dir, name))
        shutil.copytree(os.path.join(self.gtkPath, 'share', 'themes', 'MS-Windows'),
            os.path.join(self.share_dir, 'themes', 'MS-Windows'))
        shutil.copytree(os.path.join(self.gtkPath, 'share', 'themes', self.defaultTheme),
            os.path.join(self.defaulttheme_dir))
        gtkrc = open(os.path.join(self.etc_dir, 'gtk-2.0', 'gtkrc'), 'w')
        gtkrc.write("gtk-theme-name = \"Default\"")
        gtkrc.close()

    def get_datafiles(self):
        ret = []
        ret.append((os.path.join("share", "icons", "hicolor", "32x32", "apps", "p2ner.png"), "p2ner.png"))
        return ret

    def runCx_FreezeSetup(self):
        sys.argv.insert(1, 'build')

        P2NER_Target = Executable(
        script = "startClient.py",
        packages = find_packages(),
        initScript = None,
        # base = 'Win32GUI',
        targetDir = self.dist_dir,
        targetName = "p2ner.exe",
        compress = True,
        copyDependentFiles = True,
        appendScriptToExe = False,
        appendScriptToLibrary = True,
        icon = None
        )

        # P2NER_SERVER = Executable(
        # script = "startServer.py",
        # packages = find_packages(),
        # initScript = None,
        # targetDir = self.dist_dir,
        # targetName = "p2nerServer.exe",
        # compress = True,
        # copyDependentFiles = True,
        # appendScriptToExe = False,
        # appendScriptToLibrary = True,
        # icon = None
        # )

        # P2NER_BASICNET = Executable(
        # script = "startBasicNet.py",
        # packages = find_packages(),
        # initScript = None,
        # #base = 'Win32GUI',
        # targetDir = self.dist_dir,
        # targetName = "p2nerBasicNet.exe",
        # compress = True,
        # copyDependentFiles = True,
        # appendScriptToExe = False,
        # appendScriptToLibrary = True,
        # icon = None
        # )

        # P2NER_GUI = Executable(
        # script = "startGui.py",
        # packages = find_packages(),
        # initScript = None,
        # base = 'Win32GUI',
        # targetDir = self.dist_dir,
        # targetName = "p2nerGui.exe",
        # compress = True,
        # copyDependentFiles = True,
        # appendScriptToExe = False,
        # appendScriptToLibrary = True,
        # icon = None
        # )


        setup(
            name = 'P2NER',
            description = 'P2P Client',
            version = '0.1',
            options = {"build_exe": {
                            "build_exe": self.dist_dir,
                            "packages": find_packages(),
                            "includes": ['miniupnpc', 'bora', 'gtk', 'cairo', 'pangocairo', 'pango', 'atk', 'gobject','logging.handlers',
                                        'gio', 'zlib','wmi','matplotlib','matplotlib.backends.backend_gtkagg','code','pylab','xml.dom.minidom','twisted.web.client','miniupnpc','twisted.web.static','twisted.web.resource','twisted.web.server','networkx','sqlite3','twisted.web.xmlrpc'], #'gst', 'pygst'
                            "bin_excludes": ["tcl85.dll", "tk85.dll", "gdiplus.dll", "mfc90.dll", "gst-inspect.exe", "gst-launch.exe", "gst-typefind.exe", "gst-xmlinspect.exe"],
                            "excludes": ["pywin.debugger", "pywin.debugger.dbgcon","bz2",
                                        "pywin.dialogs", "pywin.dialogs.list", "py2exe", "compiler", "email",
                                        "Tkconstants","Tkinter","tcl","tk", "wx", "_tkinter", "_ssl",
                                        "doctest","macpath","ssl","win32ui",
                                        "cookielib","ftplib", "_tkagg", '_agg2', "_cairo", "_cocoaagg",
                                        "_fltkagg", "_qt4", "_qt4agg",'gst', 'pygst'],
                            "namespace_packages": ["distutils.sysconfig"],
                            'include_files': self.get_datafiles(),
                        }
                    },
            executables = [P2NER_Target]#, P2NER_SERVER,P2NER_GUI,P2NER_BASICNET],
        )

    def makeInstaller(self):
        print ("Creating installer..")
        setupscript = 'setupscript.iss'
        innosetup = '"c:\\Program Files\\Inno Setup 5\\ISCC.exe"'
        os.system(innosetup + " " + setupscript)

def main():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    parser.add_option("-k", "--gtk-path", action="store",
            dest="gtkPath",default="C:\\Python27\\Lib\\site-packages\\gtk-2.0\\runtime", type="string",
            help="GTK+ installation path")
    parser.add_option("-c", "--crt-path", action="store",
            dest="crtPath",default="C:\\Program Files\\Microsoft Visual Studio 9.0\\VC\\redist\\x86\\Microsoft.VC90.CRT" ,type="string",
            help="MS Visual C++ 2008 path")
    parser.add_option("-t", "--default-theme", action="store",
            dest="defaulttheme",default="Win2-7", type="string",
            help="Gtk+ theme to use as Default")

    (options, args) = parser.parse_args()
    Deploy(options.gtkPath, options.crtPath, options.defaulttheme)

if __name__ == "__main__":
    main()


