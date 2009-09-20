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
Here is defined the Config class.

Classes:

* Config(QSettings)

Methods:


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

    - ``$HOME/.config/MyCompany/ViTables.conf``
    - ``$HOME/.config/MyCompany.conf``

  - SystemScope

    - ``/etc/xdg/MyCompany/ViTables.conf``
    - ``/etc/xdg/MyCompany.conf``

- MacOSX

  - UserScope

    - ``$HOME/Library/Preferences/org.vitables.ViTables.plist``
    - ``$HOME/Library/Preferences/org.vitables.plist``

  - SystemScope

    - ``/Library/Preferences/org.vitables.ViTables.plist``
    - ``/Library/Preferences/org.vitables.plist``

- Windows

  - UserScope

    - ``HKEY_CURRENT_USER/Software/MyCompany/ViTables``
    - ``HKEY_CURRENT_USER/Software/MyCompany/``

  - SystemScope

    - ``HKEY_LOCAL_MACHINE/Software/MyCompany/ViTables``
    - ``HKEY_LOCAL_MACHINE/Software/MyCompany/``

If format is NativeFormat and platform is Unix the path can be set via
QSettings.setPath static method.

About the config file name
--------------------------
If format is NativeFormat:

- under Unix, Product Name -> Product Name.conf so the product name
  ``ViTables`` will match a configuration file named ``ViTables.conf``
- under MacOSX, Internet Domain and Product Name ->
  reversed Internet Domain.Product Name.plist so the domain
  ``vitables.org`` and the product ``ViTables`` become
  ``org.vitables.ViTables.plist``

Before to read/write a property value we must provide the product
name as the first subkey of the property key.
This can be done in two different ways:

a)  including the product name every time we read/write settings, e.g.
    `readEntry(/ViTables/Logger/Font)`
b)  using `setPath` method once before we read/write settings, so
    the preceding example becomes `readEntry(/Logger/Font)`
"""

__docformat__ = 'restructuredtext'
__version__ = '2.1b'

import os
import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from vitables.preferences import configException
import vitables.utils


def getVersion():
    """The application version."""
    return __version__


class Config(QSettings):
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

        On Windows systems settings will be stored in the registry
        under the HKCU\Software\ViTables\__version__ key
        Mac OS X saves settings in a properties list stored in a
        standard location, either on a global or user basis (see
        docstring.for more information)
        """

        # The scope is UserScope and the format is NativeFormat
        # System-wide settings will not be searched as a fallback
        # Setting the NativeFormat paths on MacOSX has no effect
        QSettings.__init__(self, qApp.applicationName(), 
            qApp.applicationVersion())
        self.setFallbacksEnabled(False)

        # The application default style depends on the platform
        styles = QStyleFactory.keys()
        self.default_style = styles[0]
        vtapp = vitables.utils.getVTApp()
        if not (vtapp is None):
            style_name = vtapp.style().objectName()
            for item in styles:
                if item.toLower() == style_name:
                    self.default_style = item
                    break

        # The settings search path on Unix systems
        if (not sys.platform.startswith('win')) and \
        (not sys.platform.startswith('darwin')):
            # On Unix systems settings will be stored in a plain text
            # file (see the module docstring for name conventions)
            config_directory = os.path.join(unicode(QDir.homePath()),
                '.vitables')
            if not os.path.isdir(config_directory):
                os.mkdir(config_directory)
            self.setPath(QSettings.NativeFormat,
                QSettings.UserScope, config_directory)


    def loggerPaper(self):
        """
        Returns the logger background color.
        """

        key = 'Logger/Paper'
        default_value = QVariant(QColor("#ffffff"))
        setting_value = self.value(key)
        if setting_value.canConvert(QVariant.Color):
            return setting_value
        else:
            return default_value


    def loggerText(self):
        """
        Returns the logger text color.
        """

        key = 'Logger/Text'
        default_value = QVariant(QColor("#000000"))
        setting_value = self.value(key)
        if setting_value.canConvert(QVariant.Color):
            return setting_value
        else:
            return default_value


    def loggerFont(self):
        """
        Returns the logger font.
        """

        key = 'Logger/Font'
        default_value = QVariant(qApp.font())
        setting_value = self.value(key)
        if setting_value.canConvert(QVariant.Font):
            return setting_value
        else:
            return default_value


    def workspaceBackground(self):
        """
        Returns the workspace background color.
        """

        key = 'Workspace/Background'
        default_value = QVariant(QBrush(QColor("#ffffff")))
        setting_value = self.value(key)
        if setting_value.canConvert(QVariant.Brush):
            return setting_value
        else:
            return default_value


    def readStyle(self):
        """Returns the current application style."""

        # The property key and its default value
        key = 'Look/currentStyle'
        default_value = QVariant(self.default_style)

        # Read the entry from the configuration file/registry
        entry = self.value(key)

        # Check the entry format and value
        styles = QStyleFactory.keys()
        if not entry.canConvert(QVariant.String):
            return default_value
        elif not styles.contains(entry.toString()):
            return default_value
        else:
            return entry


    def windowPosition(self):
        """
        Returns the main window geometry setting.
        """

        key = 'Geometry/Position'
        default_value = QVariant()
        setting_value = self.value(key)
        if setting_value.canConvert(QVariant.ByteArray):
            return setting_value
        else:
            return default_value


    def windowLayout(self):
        """
        Returns the main window layout setting.

        This setting stores the position and size of toolbars and
        dockwidgets.
        """

        key = 'Geometry/Layout'
        default_value = QVariant()
        setting_value = self.value(key)
        if setting_value.canConvert(QVariant.ByteArray):
            return setting_value
        else:
            return default_value


    def hsplitterPosition(self):
        """
        Returns the horizontal splitter geometry setting.
        """

        key = 'Geometry/HSplitter'
        default_value = QVariant()
        setting_value = self.value(key)
        if setting_value.canConvert(QVariant.ByteArray):
            return setting_value
        else:
            return default_value


    def vsplitterPosition(self):
        """
        Returns the vertical splitter geometry setting.
        """

        key = 'Geometry/VSplitter'
        default_value = QVariant()
        setting_value = self.value(key)
        if setting_value.canConvert(QVariant.ByteArray):
            return setting_value
        else:
            return default_value


    def startupLastSession(self):
        """
        Returns the restore last session setting.
        """

        key = 'Startup/restoreLastSession'
        default_value = QVariant(False)
        setting_value = self.value(key)
        if setting_value.canConvert(QVariant.Bool):
            return setting_value
        else:
            return default_value


    def startupWorkingDir(self):
        """
        Returns the startup working directory setting.
        """

        key = 'Startup/startupWorkingDir'
        default_value = QVariant('home')
        setting_value = self.value(key)
        if setting_value.canConvert(QVariant.String):
            return setting_value
        else:
            return default_value


    def lastWorkingDir(self):
        """
        Returns the last working directory setting.
        """

        key = 'Startup/lastWorkingDir'
        default_value = QVariant(vitables.utils.getHomeDir())
        setting_value = self.value(key)
        if setting_value.canConvert(QVariant.String):
            return setting_value
        else:
            return default_value


    def recentFiles(self):
        """
        Returns the list of most recently opened files setting.
        """

        key = 'Recent/Files'
        default_value = QVariant([])
        setting_value = self.value(key)
        if setting_value.canConvert(QVariant.StringList):
            return setting_value
        else:
            return default_value


    def sessionFiles(self):
        """
        Returns the list of files and nodes opened when the last session quit.
        """

        key = 'Session/Files'
        default_value = QVariant([])
        setting_value = self.value(key)
        if setting_value.canConvert(QVariant.StringList):
            return setting_value
        else:
            return default_value


    def helpHistory(self):
        """
        Returns the navigation history of the HelpBrowser.
        """

        key = 'HelpBrowser/History'
        default_value = QVariant([])
        setting_value = self.value(key)
        if setting_value.canConvert(QVariant.StringList):
            return setting_value
        else:
            return default_value


    def helpBookmarks(self):
        """
        Returns the bookmarks of the HelpBrowser.
        """

        key = 'HelpBrowser/Bookmarks'
        default_value = QVariant([])
        setting_value = self.value(key)
        if setting_value.canConvert(QVariant.StringList):
            return setting_value
        else:
            return default_value


    def readPluginsPaths(self):
        """Return the list of directories where plugins live.
        """

        key = 'Plugins/Paths'
        default_value = QVariant([])
        setting_value = self.value(key)
        if setting_value.canConvert(QVariant.StringList):
            return setting_value
        else:
            return default_value


    def enabledPlugins(self):
        """Returns the list of enabled plugins.
        """

        key = 'Plugins/Enabled'
        default_value = QVariant([])
        setting_value = self.value(key)
        if setting_value.canConvert(QVariant.StringList):
            return setting_value
        else:
            return default_value


    def writeValue(self, key, value):
        """
        Write an entry to the configuration file.

        :Parameters:

        - `key`: the name of the property we want to set.
        - `value`: the value we want to assign to the property
        """

        try:
            self.setValue(key, QVariant(value))
            if self.status():
                raise configException.ConfigFileIOException, \
                    '%s=%s' % (key, value)
        except configException.ConfigFileIOException, inst:
            print inst.error_message
