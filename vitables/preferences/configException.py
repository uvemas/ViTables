# -*- coding: utf-8 -*-

########################################################################
#
#       Copyright (C) 2005, 2006, 2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008 Vicent Mas. All rights reserved
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
#
#       $Source$
#       $Id: configException.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the configException module.

Classes:

* ConfigFileIOException(Exception)
* SettingRetrievalException(Exception)

Methods:

* ConfigFileIOException.__init__(self, key)
* ConfigFileIOException.__tr(self, source, comment=None)
* SettingRetrievalException.__init__(self, kind, key=None)
* SettingRetrievalException.__tr(self, source, comment=None)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import qt

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
        return qt.qApp.translate('ConfigFileIOException', source,
            comment).latin1()


class SettingRetrievalException(Exception):
    """Class for color retrieval exceptions."""


    def __init__(self, kind, key=None):
        """
        :Parameters:

        - `kind`: the kind of setting being retrieved
        - `key`: the configuration file key that cannot be formatted
        """

        Exception.__init__(self)
        
        kind2message = {
        'color':  self.__tr("""\nConfiguration warning: the %s color cannot be"""\
            """ retrieved. Its default value will be used.""", 
            'An application setting retrieval error'),
        'geometry':  self.__tr("""\nConfiguration warning: the geometry of the main"""\
            """ window cannot be retrieved. Its default value will be used.""", 
            'An application setting retrieval error'),
        'size':  self.__tr("""\nConfiguration warning: the size of the %s cannot be"""\
            """ retrieved. Its default value will be used.""", 
            'An application setting retrieval error'),
        'font':  self.__tr("""\nConfiguration warning: the logger font cannot be """\
            """retrieved. The default font will be used.""", 
            'An application setting retrieval error'),
        'style':  self.__tr("""\nConfiguration warning: cannot get the application """\
            """style. The default style will be used.""", 
            'An application setting retrieval error'),
        'startup':   self.__tr("""\nConfiguration warning: cannot get the startup """\
            """working directory. I'll start in your home directory.""", 
            'An application setting retrieval error'),
        'session':  self.__tr("""\nConfiguration warning: the last session cannot be """\
            """recovered.""", 
            'An application setting retrieval error')
        }

        if key == 'Logger/text':
            target = 'logger text'
        elif key == 'Logger/paper':
            target = 'logger background'
        elif key == 'Workspace/background':
            target = 'workspace background'
        else:
            target = key
        if target:
            self.error_message = self.__tr(kind2message[kind],
                'A logger error message') % target
        else:
            self.error_message = self.__tr(kind2message[kind],
                'A logger error message')


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('SettingRetrievalException', source,
            comment).latin1()
