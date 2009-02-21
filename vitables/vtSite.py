#!/usr/bin/env python
# -*- coding: utf-8 -*-


#       Copyright (C) 2005, 2006, 2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008, 2009 Vicent Mas. All rights reserved
#
#       This program is free software: you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation, either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#       Author:  Vicent Mas - vmas@vitables.org

"""
Site configuration module.

This module allows for testing ViTables IN the source tree.
In Linux and Windows boxes the module is rewritten at installing time.
Mac OS X boxes use the module as is.

Misc variables:

* __docformat__
* INSTALLDIR
* DATADIR
* VERSION

"""

__docformat__ = 'restructuredtext'

INSTALLDIR = '.'

import sys as _sys
if (_sys.platform == 'darwin'
    and getattr(_sys, 'frozen', None) == 'macosx_app'):
    import __main__
    import os.path as _path
    INSTALLDIR = _path.dirname(_path.abspath(__main__.__file__))
