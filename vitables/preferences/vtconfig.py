# -*- coding: utf-8 -*-
#!/usr/bin/env python


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
#       $Id: vtconfig.py 1071 2008-10-17 16:49:03Z vmas $
#
########################################################################

"""
Here is defined the Config class.

Classes:

* Config(QtCore.QSettings)

Methods:

* __init__(self)
* readStartupWorkingDir(self)
* readStyle(self)
* readValue(self, key)
* writeValue(self, key, value)

Functions:

* getVersion()

Misc variables:

* __docformat__


Every access to the config settings is done via a
`QSettings` instance that, in turn, will access the config file and return the
read setting to the application. Saving settings works in a similar way,
the application passes the setting to the `QSetting` instance and it (the
instance) will write the setting into the config file.

About the config file location
------------------------------
If format is NativeFormat then the default search path will be:

- Unix

  - UserScope

    - ``$HOME/.config/Carabos/ViTables.conf``
    - ``$HOME/.config/Carabos.conf``

  - SystemScope

    - ``/etc/xdg/Carabos/ViTables.conf``
    - ``/etc/xdg/Carabos.conf``

- MacOSX

  - UserScope

    - ``$HOME/Library/Preferences/com.carabos.ViTables.plist``
    - ``$HOME/Library/Preferences/com.carabos.plist``

  - SystemScope

    - ``/Library/Preferences/com.carabos.ViTables.plist``
    - ``/Library/Preferences/com.carabos.plist``

- Windows

  - UserScope

    - ``HKEY_CURRENT_USER/Software/Carabos/ViTables``
    - ``HKEY_CURRENT_USER/Software/Carabos/``

  - SystemScope

    - ``HKEY_LOCAL_MACHINE/Software/Carabos/ViTables``
    - ``HKEY_LOCAL_MACHINE/Software/Carabos/``

If format is NativeFormat and platform is Unix the path can be set via
QtCore.QSettings.setPath static method.

About the config file name
--------------------------
If format is NativeFormat:

- under Unix, Product Name -> Product Name.conf so the product name
  ``ViTables`` will match a configuration file named ``ViTables.conf``
- under MacOSX, Internet Domain and Product Name ->
  reversed Internet Domain.Product Name.plist so the domain
  ``carabos.com`` and the product ``ViTables`` become
  ``com.carabos.ViTables.plist``

Before to read/write a property value we must provide the product
name as the first subkey of the property key.
This can be done in two different ways:

a)  including the product name every time we read/write settings, e.g.
    `readEntry(/ViTables/Logger/Font)`
b)  using `setPath` method once before we read/write settings, so
    the preceding example becomes `readEntry(/Logger/Font)`
"""

__docformat__ = 'restructuredtext'

import os
import sys

import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui

from vitables.preferences import configException
import vitables.vtSite

def getVersion():
    """The application version."""
    return vitables.vtSite.VERSION

class Config(QtCore.QSettings):
    """
    Manages the application configuration dynamically.

    This class defines accessor methods that allow the application (a
    VTApp instance)to read the configuration file.
    The class also provides a method to save the current configuration
    in the configuration file.
    """

    def __init__(self):
        """
        Setup the application configurator.

        Set the following paths to the proper values:

        - translations directory
        - icons directory
        - documentation directory
        - configuration directory
        """

        # The scope is UserScope and the format is NativeFormat
        # System-wide settings will not be searched as a fallback
        QtCore.QSettings.__init__(self, 'Carabos', 'ViTables')
        self.setFallbacksEnabled(False)

        # The full path of the data directory
        self.data_directory = vitables.vtSite.DATADIR

        # Set the translations directory in a system-independent way
        self.translations_dir = os.path.join(self.data_directory,'translations')

        # Set the icons directory in a system-independent way
        self.icons_dir = os.path.join(self.data_directory,'icons')

        # Set the documentation directory in a system-independent way
        self.doc_dir = os.path.join(self.data_directory,'doc')

        # The default style depends on the platform
        if sys.platform.startswith('win'):
            # if VER_PLATFORM_WIN32_NT (i.e WindowsNT/2000/XP)
            if sys.getwindowsversion()[3] == 2:
                self.default_style = 'WindowsXP'
            else:
                self.default_style = 'Windows'
        elif sys.platform.startswith('darwin'):
            self.default_style = 'Macintosh (Aqua)'
        else:
            self.default_style = 'Motif'

        # The settings search path
        if sys.platform.startswith('win'):
            # On windows systems settings will be stored in the registry
            # under the Carabos key
            self.writeEntry('/Carabos/init', '') # Is this required??
            vtversion = vitables.vtSite.VERSION
            pyversion = 'Python%s%s' % (sys.version_info[0], sys.version_info[1])
            self.base_key = 'ViTables/%s/%s' % (vtversion, pyversion)
        elif sys.platform.startswith('darwin'):
            # Mac OS X saves settings in a properties list stored in a
            # standard location, either on a global or user basis (see
            # docstring.for more information)
            # Setting the NativeFormat paths on MacOSX has no effect
            self.base_key = 'ViTables'
        else:
            # On Unix systems settings will be stored in a plain text
            # file (see the module docstring for name conventions)
            self.base_key = 'ViTables'
            config_directory = os.path.join(str(QtCore.QDir.homePath()),
                '.vitables')
            if not os.path.isdir(config_directory):
                os.mkdir(config_directory)
            self.setPath(QtCore.QSettings.NativeFormat,
                QtCore.QSettings.UserScope, config_directory)


    def readStyle(self):
        """Returns the current application style."""

        # the property key and its default value
        key = 'Look/currentStyle'
        prop_value = QtCore.QVariant()

        try:
            # Read the entry from the configuration file/registry
            entry = self.value(key)

            # Check the entry format and value
            if not entry.canConvert(QtCore.QVariant.String):
                raise configException.ConfigFileIOException(key)
            if str(entry.toString()) not in ['default', 'Windows', 'Motif', 
                                            'MotifPlus', 'Platinum', 'SGI', 
                                            'CDE']:
                raise configException.SettingRetrievalException('style')

            prop_value = entry
        except configException.ConfigFileIOException, inst:
            print inst.error_message
        except configException.SettingRetrievalException, inst:
            print inst.error_message

        return prop_value


    def readStartupWorkingDir(self):
        """Returns the startupWorkingDirectory property."""

        # the property key and its default value
        key = 'Startup/startupWorkingDirectory'
        prop_value = QtCore.QVariant()

        try:
            # Read the entry from the configuration file/registry
            entry = self.value(key)

            # Check the entry format and value
            if not entry.canConvert(QtCore.QVariant.String):
                raise configException.ConfigFileIOException(key)
            if str(entry.toString()) not in ['home', 'last']:
                raise configException.SettingRetrievalException('startup')

            prop_value = entry
        except configException.ConfigFileIOException, inst:
            print inst.error_message
        except configException.SettingRetrievalException, inst:
            print inst.error_message

        return prop_value


    def readValue(self, key):
        """
        Returns the stored value of a given application setting.

        The recent files list looks like
        ``[mode#@#filepath1, mode#@#filepath2, ...]``
        The list of bookmarks looks like
        ``[filepath1[#ID], filepath2[#ID], ...]``

        :Parameters:

        - `key`: the setting being retrieved
        """

        types = {'Logger/paper': QtCore.QVariant.Color, 
                 'Logger/text': QtCore.QVariant.Color, 
                 'Logger/font': QtCore.QVariant.Font, 
                 'Workspace/background': QtCore.QVariant.Color, 
                 'Startup/startupWorkingDirectory': QtCore.QVariant.String, 
                 'Startup/restoreLastSession': QtCore.QVariant.Bool, 
                 'Geometry/position': QtCore.QVariant.ByteArray, 
                 'Geometry/state': QtCore.QVariant.ByteArray, 
                 'Geometry/hsplitter': QtCore.QVariant.ByteArray, 
                 'Geometry/vsplitter': QtCore.QVariant.ByteArray, 
                 'Startup/lastWorkingDirectory': QtCore.QVariant.String, 
                 'Recent/files': QtCore.QVariant.StringList, 
                 'Session/files': QtCore.QVariant.StringList, 
                 'HelpBrowser/history': QtCore.QVariant.StringList, 
                 'HelpBrowser/bookmarks': QtCore.QVariant.StringList, }
        # the property default value
        prop_value = QtCore.QVariant()

        try:
            # Read the entry from the configuration file/registry
            entry = self.value(key)
            # Check the entry format
            if not entry.canConvert(types[key]):
                raise configException.ConfigFileIOException(key)

            prop_value = entry
        except configException.ConfigFileIOException, inst:
            print inst.error_message

        return prop_value


    def writeValue(self, key, value):
        """
        Write an entry to the configuration file.

        :Parameters:

        - `key`: the name of the property we want to set.
        - `value`: the value we want to assign to the property
        """

        try:
            self.setValue(key, QtCore.QVariant(value))
            if self.status():
                raise configException.ConfigFileIOException, \
                    '%s=%s' % (key, value)
        except configException.ConfigFileIOException, inst:
            print inst.error_message
