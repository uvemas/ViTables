#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2013 Vicent Mas. All rights reserved
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
This module manages the ``ViTables`` configuration.

The module provides methods for reading and writting settings. Whether the 
settings are stored in a plain text file or in a Windows registry is
transparent for this module because it deals with settings via 
`QtCore.QSettings`.

Every access to the config settings is done via a `QSettings` instance that, 
in turn, will access the config file and return the read setting to the 
application. Saving settings works in a similar way, the application passes 
the setting to the `QSetting` instance and it (the instance) will write the 
setting into the config file.

.. Note:: *About the config file location*.
  If format is NativeFormat then the default search path will be:

  - Unix

    - UserScope

      - ``$HOME/.config/MyCompany/ViTables-version.conf``
      - ``$HOME/.config/MyCompany.conf``

    - SystemScope

      - ``/etc/xdg/MyCompany/ViTables-version.conf``
      - ``/etc/xdg/MyCompany.conf``

  - MacOSX

    - UserScope

      - ``$HOME/Library/Preferences/org.vitables.ViTables-version.plist``
      - ``$HOME/Library/Preferences/org.vitables.plist``

    - SystemScope

      - ``/Library/Preferences/org.vitables.ViTables-version.plist``
      - ``/Library/Preferences/org.vitables.plist``

  - Windows

    - UserScope

      - ``HKEY_CURRENT_USER/Software/MyCompany/ViTables/version``
      - ``HKEY_CURRENT_USER/Software/MyCompany/``

    - SystemScope

      - ``HKEY_LOCAL_MACHINE/Software/MyCompany/ViTables/version``
      - ``HKEY_LOCAL_MACHINE/Software/MyCompany/``

  If format is NativeFormat and platform is Unix the path can be set via
  QSettings.setPath static method.

.. Note:: *About the config file name*.
  If format is NativeFormat:

  - under Unix, Product Name -> Product Name.conf so the product name
    ``ViTables`` will match a configuration file named ``ViTables.conf``
  - under MacOSX, Internet Domain and Product Name ->
    reversed Internet Domain.Product Name.plist so the domain
    ``vitables.org`` and the product ``ViTables`` become
    ``org.vitables.ViTables.plist``

"""

__docformat__ = 'restructuredtext'
__version__ = '2.1'

import sys

from PyQt4 import QtCore
from PyQt4 import QtGui

from vitables.preferences import cfgexception
import vitables.utils
import vitables.vttables.datasheet as datasheet

translate = QtGui.QApplication.translate

def getVersion():
    """The application version."""
    return __version__


class Config(QtCore.QSettings):
    """
    Manages the application configuration dynamically.

    This class defines accessor methods that allow the application (a
    :meth:`vitables.vtapp.VTApp` instance) to read the configuration file/registry/plist.
    The class also provides a method to save the current configuration
    in the configuration file/registry/plist.
    """

    def __init__(self):
        """
        Setup the application configurator.

        On Windows systems settings will be stored in the registry
        under the HKCU\Software\ViTables\__version__ key
        Mac OS X saves settings in a properties list stored in a
        standard location, either on a global or user basis (see
        docstring.for more information).

        In all platforms QSettings format is NativeFormat and scope
        is UserScope.
        """

        organization = QtGui.qApp.organizationName()
        product = QtGui.qApp.applicationName()
        version = QtGui.qApp.applicationVersion()
        if sys.platform.startswith('win'):
            path = 'HKEY_CURRENT_USER\\Software\\{0}\\{1}'
            rpath = path.format(product, version)
            super(Config, self).__init__(rpath, QtCore.QSettings.NativeFormat)
        elif sys.platform.startswith('darwin'):
            super(Config, self).__init__(product, version)
        else:
            arg1 = organization
            arg2 = '-'.join((product, version))
            super(Config, self).__init__(arg1, arg2)

        # System-wide settings will not be searched as a fallback
        # Setting the NativeFormat paths on MacOSX has no effect
        self.setFallbacksEnabled(False)

        # The application default style depends on the platform
        styles = QtGui.QStyleFactory.keys()
        self.default_style = styles[0]
        self.vtapp = vitables.utils.getVTApp()
        if not (self.vtapp is None):
            style_name = self.vtapp.gui.style().objectName()
            for item in styles:
                if item.lower() == style_name:
                    self.default_style = item
                    break


    def loggerPaper(self):
        """
        Returns the logger background color.
        """

        key = 'Logger/Paper'
        default_value = QtGui.QColor("#ffffff")
        setting_value = self.value(key)
        if isinstance(setting_value, QtGui.QColor):
            return setting_value
        else:
            return default_value


    def loggerText(self):
        """
        Returns the logger text color.
        """

        key = 'Logger/Text'
        default_value = QtGui.QColor("#000000")
        setting_value = self.value(key)
        if isinstance(setting_value, QtGui.QColor):
            return setting_value
        else:
            return default_value


    def loggerFont(self):
        """
        Returns the logger font.
        """

        key = 'Logger/Font'
        default_value = QtGui.qApp.font()
        setting_value = self.value(key)
        if isinstance(setting_value, QtGui.QFont):
            return setting_value
        else:
            return default_value


    def workspaceBackground(self):
        """
        Returns the workspace background color.
        """

        key = 'Workspace/Background'
        default_value = QtGui.QBrush(QtGui.QColor("#ffffff"))
        setting_value = self.value(key)
        if isinstance(setting_value, QtGui.QBrush):
            return setting_value
        else:
            return default_value


    def readStyle(self):
        """Returns the current application style."""

        # The property key and its default value
        key = 'Look/currentStyle'
        default_value = self.default_style

        # Read the entry from the configuration file/registry
        entry = self.value(key)

        # Check the entry format and value
        styles = QtGui.QStyleFactory.keys()
        if not isinstance(entry, unicode):
            return default_value
        elif entry not in styles:
            return default_value
        else:
            return entry


    def windowPosition(self):
        """
        Returns the main window geometry setting.
        """

        key = 'Geometry/Position'
        default_value = None
        setting_value = self.value(key)
        if isinstance(setting_value, QtCore.QByteArray):
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
        default_value = None
        setting_value = self.value(key)
        if isinstance(setting_value, QtCore.QByteArray):
            return setting_value
        else:
            return default_value


    def hsplitterPosition(self):
        """
        Returns the horizontal splitter geometry setting.
        """

        key = 'Geometry/HSplitter'
        default_value = None
        setting_value = self.value(key)
        if isinstance(setting_value, QtCore.QByteArray):
            return setting_value
        else:
            return default_value


    def vsplitterPosition(self):
        """
        Returns the vertical splitter geometry setting.
        """

        key = 'Geometry/VSplitter'
        default_value = None
        setting_value = self.value(key)
        if isinstance(setting_value, QtCore.QByteArray):
            return setting_value
        else:
            return default_value


    def startupLastSession(self):
        """
        Returns the `Restore last session` setting.
        """

        key = 'Startup/restoreLastSession'
        default_value = False
        # Warning!
        # If the application settings have not yet been saved
        # in the registry then self.value(key) returns a Null
        # QVariant (its type is None) and self.value(key, type=bool)
        # raises an exception because None cannot be converted
        # to a boolean value
        try:
            setting_value = self.value(key, type=bool)
        except TypeError:
            setting_value = default_value
        if setting_value in (False, True):
            return setting_value
        else:
            return default_value
    def startupWorkingDir(self):
        """
        Returns the `Startup working directory` setting.
        """

        key = 'Startup/startupWorkingDir'
        default_value = u'home'
        setting_value = self.value(key)
        if isinstance(setting_value, unicode):
            return setting_value
        else:
            return default_value


    def lastWorkingDir(self):
        """
        Returns the `Last working directory` setting.
        """

        key = 'Startup/lastWorkingDir'
        default_value = vitables.utils.getHomeDir()
        setting_value = self.value(key)
        if isinstance(setting_value, unicode):
            return setting_value
        else:
            return default_value


    def recentFiles(self):
        """
        Returns the list of most recently opened files setting.
        """

        key = 'Recent/Files'
        default_value = []
        setting_value = self.value(key)
        if isinstance(setting_value, list):
            return setting_value
        else:
            return default_value


    def sessionFiles(self):
        """
        Returns the list of files and nodes opened when the last session quit.
        """

        key = 'Session/Files'
        default_value = []
        setting_value = self.value(key)
        if isinstance(setting_value, list):
            return setting_value
        else:
            return default_value


    def helpHistory(self):
        """
        Returns the navigation history of the docs browser.
        """

        key = 'HelpBrowser/History'
        default_value = []
        setting_value = self.value(key)
        if isinstance(setting_value, list):
            return setting_value
        else:
            return default_value


    def helpBookmarks(self):
        """
        Returns the bookmarks of the docs browser.
        """

        key = 'HelpBrowser/Bookmarks'
        default_value = []
        setting_value = self.value(key)
        if isinstance(setting_value, list):
            return setting_value
        else:
            return default_value


    def enabledPlugins(self):
        """Returns the list of enabled plugins.
        """

        key = 'Plugins/Enabled'
        default_value = []
        setting_value = self.value(key)
        if isinstance(setting_value, list):
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
            self.setValue(key, value)
            if self.status():
                raise cfgexception.ConfigFileIOException, \
                    u'{0}={1}'.format(key, value)
        except cfgexception.ConfigFileIOException, inst:
            print(inst.error_message)


    def readConfiguration(self):
        """
        Get the application configuration currently stored on disk.

        Read the configuration from the stored settings. If a setting
        cannot be read (as it happens when the package is just
        installed) then its default value is returned.
        Geometry and Recent settings are returned as lists, color
        settings as QColor instances. The rest of settings are returned
        as strings or integers.

        :Returns: a dictionary with the configuration stored on disk
        """

        config = {}
        config['Logger/Paper'] = self.loggerPaper()
        config['Logger/Text'] = self.loggerText()
        config['Logger/Font'] = self.loggerFont()
        config['Workspace/Background'] = self.workspaceBackground()
        config['Startup/restoreLastSession'] = self.startupLastSession()
        config['Startup/startupWorkingDir'] = self.startupWorkingDir()
        config['Startup/lastWorkingDir'] = self.lastWorkingDir()
        config['Geometry/Position'] = self.windowPosition()
        config['Geometry/Layout'] = self.windowLayout()
        config['Geometry/HSplitter'] = self.hsplitterPosition()
        config['Geometry/VSplitter'] = self.vsplitterPosition()
        config['Recent/Files'] = self.recentFiles()
        config['Session/Files'] = self.sessionFiles()
        config['HelpBrowser/History'] = self.helpHistory()
        config['HelpBrowser/Bookmarks'] = self.helpBookmarks()
        config['Look/currentStyle'] = self.readStyle()
        config['Plugins/Enabled'] = self.enabledPlugins()
        return config


    def saveConfiguration(self):
        """
        Store current application settings on disk.

        Note that we are using ``QSettings`` for writing to the config file,
        so we **must** rely on its searching algorithms in order to find
        that file.
        """

        vtgui = self.vtapp.gui
        # Logger paper
        style_sheet = vtgui.logger.styleSheet()
        paper = style_sheet[-7:]
        self.writeValue('Logger/Paper', QtGui.QColor(paper))
        # Logger text color
        self.writeValue('Logger/Text', vtgui.logger.textColor())
        # Logger text font
        self.writeValue('Logger/Font', vtgui.logger.font())
        # Workspace
        self.writeValue('Workspace/Background', vtgui.workspace.background())
        # Style
        self.writeValue('Look/currentStyle', self.current_style)
        # Startup working directory
        self.writeValue('Startup/startupWorkingDir', 
            self.startup_working_directory)
        # Startup restore last session
        self.writeValue('Startup/restoreLastSession', 
            self.restore_last_session)
        # Startup last working directory
        self.writeValue('Startup/lastWorkingDir', self.last_working_directory)
        # Window geometry
        self.writeValue('Geometry/Position', vtgui.saveGeometry())
        # Window layout
        self.writeValue('Geometry/Layout', vtgui.saveState())
        # Horizontal splitter geometry
        self.writeValue('Geometry/HSplitter', vtgui.hsplitter.saveState())
        # Vertical splitter geometry
        self.writeValue('Geometry/VSplitter', vtgui.vsplitter.saveState())
        # The list of recent files
        self.writeValue('Recent/Files', self.recent_files)
        # The list of session files and nodes
        self.session_files_nodes = self.getSessionFilesNodes()
        self.writeValue('Session/Files', self.session_files_nodes)
        # The Help Browser history
        self.writeValue('HelpBrowser/History', self.hb_history)
        # The Help Browser bookmarks
        self.writeValue('HelpBrowser/Bookmarks', self.hb_bookmarks)
        # The list of enabled plugins
        self.writeValue('Plugins/Enabled', 
            self.vtapp.plugins_mgr.enabled_plugins)
        self.sync()


    def getSessionFilesNodes(self):
        """
        The list of files and nodes currently open.

        The list looks like::

            ['mode#@#filepath1#@#nodepath1#@#nodepath2, ...',
            'mode#@#filepath2#@#nodepath1#@#nodepath2, ...', ...]
        """

        # Get the list of views
        workspace = self.vtapp.gui.workspace
        node_views = [window for window in workspace.subWindowList() \
                        if isinstance(window, datasheet.DataSheet)]

        # Get the list of open files (temporary database is not included)
        dbt_model = self.vtapp.gui.dbs_tree_model
        session_files_nodes = []
        filepaths = dbt_model.getDBList()
        for path in filepaths:
            mode = dbt_model.getDBDoc(path).mode
            # If a new file has been created during the current session
            # then write mode must be replaced by append mode or the file
            # will be created from scratch in the next ViTables session
            if mode == u'w':
                mode = u'a'
            item_path = mode + u'#@#' + path
            for view in node_views:
                if view.dbt_leaf.filepath == path:
                    item_path = item_path + u'#@#' + view.dbt_leaf.nodepath
            session_files_nodes.append(item_path)

        # Format the list in a handy way to store it on disk
        return session_files_nodes


    def loadConfiguration(self, config):
        """
        Configure the application with the given settings.

        We call `user settings` to those settings that can be setup via
        Settings dialog and `internal settings` to the rest of settings.

        At startup all settings will be loaded. At any time later the
        `users settings` can be explicitely changed via Settings dialog.

        :Parameter config: a dictionary with the settings to be (re)loaded
        """

        # Load the user settings
        self.userSettings(config)

        # Load the internal settings (if any)
        gui = self.vtapp.gui
        try:
            key = 'Geometry/Position'
            value = config[key]
            if isinstance(value, QtCore.QByteArray):
                # Default position is provided by the underlying window manager
                gui.restoreGeometry(value)

            key = 'Geometry/Layout'
            value = config[key]
            if isinstance(value, QtCore.QByteArray):
                # Default layout is provided by the underlying Qt installation
                gui.restoreState(value)

            key = 'Geometry/HSplitter'
            value = config[key]
            if isinstance(value, QtCore.QByteArray):
                # Default geometry provided by the underlying Qt installation
                gui.hsplitter.restoreState(value)

            key = 'Geometry/VSplitter'
            value = config[key]
            if isinstance(value, QtCore.QByteArray):
                # Default geometry provided by the underlying Qt installation
                gui.vsplitter.restoreState(value)

            key = 'Startup/lastWorkingDir'
            self.last_working_directory = config[key]

            key = 'Recent/Files'
            self.recent_files = config[key]

            key = 'Session/Files'
            self.session_files_nodes = config[key]

            key = 'HelpBrowser/History'
            self.hb_history = config[key]

            key = 'HelpBrowser/Bookmarks'
            self.hb_bookmarks = config[key]
        except KeyError:
            pass


    def userSettings(self, config):
        """Load settings that can be setup via Settings dialog.

        :Parameter config: a dictionary with the settings to be (re)loaded
        """

        # Usually after calling the Settings dialog only some user
        # settings will need to be reloaded. So for every user setting
        # we have to check if it needs to be reloaded or not
        key = 'Startup/restoreLastSession'
        if key in config:
            self.restore_last_session = config[key]

        key = 'Startup/startupWorkingDir'
        if key in config:
            self.startup_working_directory = config[key]

        key = 'Logger/Paper'
        logger = self.vtapp.gui.logger
        if key in config:
            value = config[key]
            paper = value.name()
            stylesheet = logger.styleSheet()
            old_paper = stylesheet[-7:]
            new_stylesheet = stylesheet.replace(old_paper, paper)
            logger.setStyleSheet(new_stylesheet)

        key = 'Logger/Text'
        if key in config:
            logger.moveCursor(QtGui.QTextCursor.End)
            logger.setTextColor(config[key])

        key = 'Logger/Font'
        if key in config:
            logger.setFont(config[key])

        key = 'Workspace/Background'
        workspace = self.vtapp.gui.workspace
        if key in config:
            workspace.setBackground(config[key])
            workspace.viewport().update()

        key = 'Look/currentStyle'
        if key in config:
            self.current_style = config[key]
            # Default style is provided by the underlying window manager
            QtGui.qApp.setStyle(self.current_style)

        key = 'Plugins/Enabled'
        if key in config:
            self.enabled_plugins = config[key]
