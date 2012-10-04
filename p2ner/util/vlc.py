#! /usr/bin/python
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


# Python ctypes bindings for VLC
#
# Copyright (C) 2009-2010 the VideoLAN team
# $Id: $
#
# Authors: Olivier Aubert <olivier.aubert at liris.cnrs.fr>
#          Jean Brouwers <MrJean1 at gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.

"""This module provides bindings for the LibVLC public API, see
U{http://wiki.videolan.org/LibVLC}.

You can find the documentation and a README file with some examples
at U{http://www.advene.org/download/python-ctypes/}.

Basically, the most important class is L{Instance}, which is used
to create a libvlc instance.  From this instance, you then create
L{MediaPlayer} and L{MediaListPlayer} instances.

Alternatively, you may create instances of the L{MediaPlayer} and
L{MediaListPlayer} class directly and an instance of L{Instance}
will be implicitly created.  The latter can be obtained using the
C{get_instance} method of L{MediaPlayer} and L{MediaListPlayer}.
"""

import ctypes
import os
import sys

# Used by EventManager in override.py
from inspect import getargspec

__version__ = "N/A"
build_date  = "Thu Apr 14 18:33:30 2011"

 # Used on win32 and MacOS in override.py
plugin_path = None

if sys.platform.startswith('linux'):
    try:
        dll = ctypes.CDLL('libvlc.so')
    except OSError:  # may fail
        dll = ctypes.CDLL('libvlc.so.5')

elif sys.platform.startswith('win'):
    import ctypes.util as u
    p = u.find_library('libvlc.dll')
    if p is None:
        try:  # some registry settings
            import _winreg as w  # leaner than win32api, win32con
            for r in w.HKEY_LOCAL_MACHINE, w.HKEY_CURRENT_USER:
                try:
                    r = w.OpenKey(r, 'Software\\VideoLAN\\VLC')
                    plugin_path, _ = w.QueryValueEx(r, 'InstallDir')
                    w.CloseKey(r)
                    break
                except w.error:
                    pass
            del r, w
        except ImportError:  # no PyWin32
            pass
        if plugin_path is None:
             # try some standard locations.
            for p in ('Program Files\\VideoLan\\', 'VideoLan\\',
                      'Program Files\\',           ''):
                p = 'C:\\' + p + 'VLC\\libvlc.dll'
                if os.path.exists(p):
                    plugin_path = os.path.dirname(p)
                    break
        if plugin_path is not None:  # try loading
            p = os.getcwd()
            os.chdir(plugin_path)
             # if chdir failed, this will raise an exception
            dll = ctypes.CDLL('libvlc.dll')
             # restore cwd after dll has been loaded
            os.chdir(p)
        else:  # may fail
            dll = ctypes.CDLL('libvlc.dll')
    else:
        plugin_path = os.path.dirname(p)
        dll = ctypes.CDLL(p)
    del p, u

elif sys.platform.startswith('darwin'):
    # FIXME: should find a means to configure path
    d = '/Applications/VLC.app/Contents/MacOS/'
    p = d + 'lib/libvlc.dylib'
    if os.path.exists(p):
        dll = ctypes.CDLL(p)
        d += 'modules'
        if os.path.isdir(d):
            plugin_path = d
    else:  # hope, some PATH is set...
        dll = ctypes.CDLL('libvlc.dylib')
    del d, p

else:
    raise NotImplementedError('%s: %s not supported' % (sys.argv[0], sys.platform))

class VLCException(Exception):
    """Exception raised by libvlc methods.
    """
    pass

try:
    _Ints = (int, long)
except NameError:  # no long in Python 3+
    _Ints =  int

_Seqs = (list, tuple)

_Cfunctions = {}  # from LibVLC __version__

def _Cfunction(name, flags, *types):
    """(INTERNAL) New ctypes function binding.
    """
    if hasattr(dll, name):
        p = ctypes.CFUNCTYPE(*types)
        f = p((name, dll), flags)
        _Cfunctions[name] = f
        return f
    raise NameError('no function %r' % (name,))


def libvlc_get_version():
    '''Retrieve libvlc version.
    Example: "1.1.0-git The Luggage".
    @return: a string containing the libvlc version.
    '''
    f = _Cfunctions.get('libvlc_get_version', None) or \
        _Cfunction('libvlc_get_version', (),
                    ctypes.c_char_p)
    if not __debug__:  # i.e. python -O or -OO
        global libvlc_get_version
        libvlc_get_version = f
    return f()


  