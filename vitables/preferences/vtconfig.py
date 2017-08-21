#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2017 Vicent Mas. All rights reserved
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

The module provides methods for reading and writing settings. Whether the
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

import logging
import sys
from vitables.preferences import cfgexception
import vitables.utils

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

import vitables.vttables.datasheet as datasheet


__docformat__ = 'restructuredtext'
__version__ = '3.0.0'

translate = QtWidgets.QApplication.translate


def getVersion():
    """The application version."""
    return __version__


log = logging.getLogger(__name__)


class Config(QtCore.QSettings):
    """
    Manages the application configuration dynamically.

    This class defines accessor methods that allow the application (a
    :meth:`vitables.vtapp.VTApp` instance) to read the configuration in
    file/registry/plist. The class also provides a method to save the current
    configuration in the configuration file/registry/plist.
    """

    def __init__(self):
        """
        Setup the application configurator.

        On Windows systems settings will be stored in the registry
        under the HKCU\Software\ViTables\__version__ key
        Mac OS X saves settings in a properties list stored in a
        standard location, either on a global or user basis (see
        docstring for more information).

        In all platforms QSettings format is NativeFormat and scope
        is UserScope.
        """

        organization = QtWidgets.qApp.organizationName()
        product = QtWidgets.qApp.applicationName()
        version = QtWidgets.qApp.applicationVersion()
        if sys.platform.startswith('win'):
            # organizationName() -> product
            # applicationName() -> version
            super(Config, self).__init__(product, version)
            self.reg_path = 'HKEY_CURRENT_USER\\Software\\{0}\\{1}'.format(
                product, version)
            self.setPath(QtCore.QSettings.NativeFormat,
                         QtCore.QSettings.UserScope, self.reg_path)
        elif sys.platform.startswith('darwin'):
            # organizationName() -> product
            # applicationName() -> version
            super(Config, self).__init__(product, version)
        else:
            # organizationName() -> organization
            # applicationName() -> product-version
            arg1 = organization
            arg2 = '-'.join((product, version))
            super(Config, self).__init__(arg1, arg2)

        # System-wide settings will not be searched as a fallback
        # Setting the NativeFormat paths on MacOSX has no effect
        self.setFallbacksEnabled(False)

        # The application default style depends on the platform
        styles = QtWidgets.QStyleFactory.keys()
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
        default_value = QtWidgets.qApp.font()
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
        setting_value = self.value(key)

        # Check the entry format and value
        styles = QtWidgets.QStyleFactory.keys()
        if not isinstance(setting_value, str):
            return default_value
        elif setting_value not in styles:
            return default_value
        else:
            return setting_value

    def windowPosition(self):
        """
        Returns the main window geometry settings.

        Basically the main window geometry is made of the x and y coordinates
        of the top left corner, width and height. A QByteArray with all this
        information can be created via QMainWindow.saveGeometry() and stored
        in a setting with QSetting.setValue()
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

    def restoreLastSession(self):
        """
        Returns the `Restore last session` setting.

        This is a user preference that can be setup in the Preferences dialog,
        with the 'Restore last session' checkbox.
        """

        key = 'Session/restoreLastSession'
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

        The startup working directory is the directory to be accessed the very
        first time a file opening happens in a working session. The setting can
        have two values:
        - last -> go to the last directory accessed in the previous ViTables
            session
        - current -> go to the current working directory if ViTables started
            from a terminal and go to the home directory otherwise

        This is a user preference that can be setup in the Preferences dialog,
        with the 'Start in last working directory' checkbox.
        """

        key = 'Session/startupWorkingDir'
        default_value = 'home'
        setting_value = self.value(key)
        if setting_value in ['last', 'current']:
            return setting_value
        else:
            return default_value

    def lastWorkingDir(self):
        """
        Returns the `Last working directory` setting.
        """

        key = 'Session/lastWorkingDir'
        default_value = vitables.utils.getHomeDir()
        setting_value = self.value(key)
        if isinstance(setting_value, str):
            # TODO: check if the value is an existing file
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
                raise cfgexception.ConfigFileIOException(
                    '{0}={1}'.format(key, value))
        except cfgexception.ConfigFileIOException as inst:
            log.error(inst.error_message)

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
        config['Session/restoreLastSession'] = self.restoreLastSession()
        config['Session/startupWorkingDir'] = self.startupWorkingDir()
        config['Session/lastWorkingDir'] = self.lastWorkingDir()
        config['Geometry/Position'] = self.windowPosition()
        config['Geometry/Layout'] = self.windowLayout()
        config['Geometry/HSplitter'] = self.hsplitterPosition()
        config['Recent/Files'] = self.recentFiles()
        config['Session/Files'] = self.sessionFiles()
        config['HelpBrowser/History'] = self.helpHistory()
        config['HelpBrowser/Bookmarks'] = self.helpBookmarks()
        config['Look/currentStyle'] = self.readStyle()
        config['Plugins/Enabled'] = self.enabledPlugins()
        return config

    def applyConfiguration(self, config):
        """
        Configure the application with the given settings.

        We call `user settings` to those settings that can be setup via
        Settings dialog and `internal settings` to the rest of settings.

        At startup all settings will be loaded. At any time later the
        `users settings` can be explicitly changed via Settings dialog.

        :Parameter config: a dictionary with the settings to be (re)loaded
        """

        # Load the user settings
        self.applyUserPreferences(config)

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

            key = 'Session/lastWorkingDir'
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

    def applyUserPreferences(self, config):
        """Apply settings that can be setup via Settings dialog.

        :Parameter config: a dictionary with the settings to be (re)loaded
        """

        # Usually after calling the Settings dialog only some user
        # settings will need to be reloaded. So for every user setting
        # we have to check if it needs to be reloaded or not
        key = 'Session/restoreLastSession'
        if key in config:
            self.restore_last_session = config[key]

        key = 'Session/startupWorkingDir'
        if key in config:
            self.initial_working_directory = config[key]

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
            QtWidgets.qApp.setStyle(self.current_style)

        key = 'Plugins/Enabled'
        if key in config:
            self.enabled_plugins = config[key]

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
        self.writeValue('Session/startupWorkingDir',
                        self.initial_working_directory)
        # Startup restore last session
        self.writeValue('Session/restoreLastSession',
                        self.restore_last_session)
        # Startup last working directory
        self.writeValue('Session/lastWorkingDir', self.last_working_directory)
        # Window geometry
        self.writeValue('Geometry/Position', vtgui.saveGeometry())
        # Window layout
        self.writeValue('Geometry/Layout', vtgui.saveState())
        # Horizontal splitter geometry
        self.writeValue('Geometry/HSplitter', vtgui.hsplitter.saveState())
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
        node_views = [window for window in workspace.subWindowList()
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
            if mode == 'w':
                mode = 'a'
            item_path = mode + '#@#' + path
            for view in node_views:
                if view.dbt_leaf.filepath == path:
                    item_path = item_path + '#@#' + view.dbt_leaf.nodepath
            session_files_nodes.append(item_path)

        # Format the list in a handy way to store it on disk
        return session_files_nodes
