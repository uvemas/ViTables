# -*- coding: utf-8 -*-
#!/usr/bin/env python

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
Here is defined the configException module.

Classes:

* ConfigFileIOException(Exception)

Methods:

* ConfigFileIOException.__init__(self, key)
* ConfigFileIOException.__tr(self, source, comment=None)

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'
_context = 'ConfigFileIOException'

from PyQt4.QtGui import *

class ConfigFileIOException(Exception):
    """Exception class for IO errors in the configuration file."""

    def __init__(self, key):
        """
        :Parameter key:
            the configuration file key that cannot be read/written
        """

        Exception.__init__(self)
        # If key looks like /path/to/property=value a write exception is
        # raised. If not a read exception is raised
        if '=' in key:
            self.error_message = self.__tr(\
                """\nConfiguration error: the application setting """\
                """%s cannot be saved.""",
                'A logger error message')  % key
        else:
            self.error_message = self.__tr(\
                """\nConfiguration warning: the application setting """\
                """%s cannot be read. Its default value will be used.""",
                'A logger error message')  % key


    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(qApp.translate(_context, source, comment))
