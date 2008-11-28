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
#       $Id: vtconfig.py 1045 2008-04-28 14:57:00Z vmas $
#
########################################################################

"""
Here is defined the Config class.

Classes:

* Config(qt.QSettings)

Methods:

* __init__(self)
* readStyle(self)
* readLastWorkingDir(self)
* readStartupWorkingDir(self)
* readRestoreLastSession(self)
* readSessionFiles(self)
* readRecentFiles(self)
* readHelpBrowserHistory(self)
* readHelpBrowserBookmarks(self)
* readFilePaths(self, key)
* readWindowPosition(self, key='Geometry/position')
* readHSplitterSizes(self)
* readVSplitterSizes(self)
* readSplitterSizes(self, key)
* readWorkspaceBackground(self)
* readLoggerPaper(self)
* readLoggerText(self)
* readColor(self, key)
* readLoggerFont(self)
* writeProperty(self, subkey, value)

Functions:

* getVersion()

Misc variables:

* __docformat__

General remarks
---------------

About application configuration.
Provided a configuration file, ``$HOME/.vitables/vitablesrc`` in our case, (at
least) two different approaches can be used to manage the app configuration.
The first reads the config file when the application starts and use some
class as a placeholder that store config settings as attributes. The app is
configured accessing these attributes. Configuration changes modify class
attributes. The configuration is saved by writing the config class
attributes back to the config file when application quits.

The second approach doesn't use intermediates placeholders but the `QSettings`
class (or derive it). Every access to the config settings is done via a
`QSettings` instance that, in turn, will access the config file and return the
read setting to the application. Saving settings works in a similar way,
the application passes the setting to the `QSetting` instance and it (the
instance) will write the setting into the config file.

About the config file location
------------------------------
The default Unix search path is:

- ``$QTDIR/etc/settings``
- ``$HOME/.qt``

We can add new paths in between with `insertSearchPath`, eg.

- ``insertSearchPath( QSettings.Unix, "/opt/MyCompany/share/etc")``
- ``insertSearchPath(QSettings.Unix, "/opt/MyCompany/share/MyApplication/etc")``

Now the search path is:

- ``$QTDIR/etc/settings``
- ``/opt/MyCompany/share/etc``
- ``/opt/MyCompany/share/MyApplication/etc``
- ``$HOME/.qt``

About the config file name
--------------------------
When reading/writing settings under Unix, the name of the configuration
file is determined from the product name as follows::

    Product Name -> product name -> product_name -> product_namerc

so the product name ``ViTables`` will match a configuration file named
``vitablesrc``.

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

import qt

from vitables.preferences import configException
import vitables.vtSite

def getVersion():
    """The application version."""
    return vitables.vtSite.VERSION


class Config(qt.QSettings):
    """
    Manages the application configuration dynamically.

    This class defines accessor methods that allow the application (a
    VTApp instance)to read the configuration file.
    The class also provides a method to save the current configuration
    in the configuration file.
    """


    # Configuration defaults. These values are used when the access to
    # the config file fails (read/write error or file doesn't exist).
    # For a given property the same key is used in the defaults mapping
    # than in the config file
    confDef = {
        # User Interface defaults
        'Geometry/position': [30, 30, 800, 560],
        'Geometry/hsplitter': [120, 670],
        'Geometry/vsplitter': [480, 80],
        'Logger/paper': qt.QTextEdit().palette().active().base(),
        'Logger/text': qt.QTextEdit().palette().active().text(),
        'Logger/font': qt.qApp.font(),
        'Workspace/background': qt.QWorkspace().\
                palette().active().light(),
        'Look/currentStyle': 'default',
        # User space defaults
        'Startup/lastWorkingDirectory': 'home',
        'Startup/startupWorkingDirectory': 'home',
        'Startup/restoreLastSession': 0, 
        # Recent files
        'Recent/files': [], 
        # Last session
        'Session/files': [], 
        # Help browser
        'HelpBrowser/history': [], 
        'HelpBrowser/bookmarks': [], 
    }


    def __init__(self):
        """
        Setup the application configurator.

        Set the following paths to the proper values:

        - translations directory
        - icons directory
        - documentation directory
        - configuration directory
        """

        qt.QSettings.__init__(self, qt.QSettings.Native)

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
            self.writeEntry('/Carabos/init', '')
            self.insertSearchPath(qt.QSettings.Windows, '/Carabos')
            vtversion = vitables.vtSite.VERSION
            pyversion = 'Python%s%s' % (sys.version_info[0], sys.version_info[1])
            self.base_key = 'ViTables/%s/%s' % (vtversion, pyversion)
        elif sys.platform.startswith('darwin'):
            # Mac OS X saves settings in a properties list stored in a
            # standard location (either on a global or user basis).
            # QSettings will create the appropriate plist file com.ViTables.plist
            self.setPath('vitables.org', 'ViTables', qt.QSettings.User)
            self.base_key = 'ViTables'
        else:
            # On Unix systems settings will be stored in a plain text
            # file (see the module docstring for name conventions)
            config_directory = os.path.join(qt.QDir.homeDirPath().latin1(),
                '.vitables')
            if not os.path.isdir(config_directory):
                os.mkdir(config_directory)
            # Warning!!! setPath method doesn't work on Unix, this is a Qt/X11 bug.
            self.insertSearchPath(qt.QSettings.Unix, config_directory)
            self.base_key = 'ViTables'


    def readStyle(self):
        """
        Returns the current application style or its default value.

        Styles are stored as strings.

        :Returns: a string representation of the property
        """

        # the property key and its default value
        key = 'Look/currentStyle'
        full_key = '%s/%s' % (self.base_key, key)
        prop_value = Config.confDef[key]

        try:
            # Read the entry from the configuration file/registry
            entry, is_ok = self.readEntry(full_key, prop_value)
            if not is_ok:
                raise configException.ConfigFileIOException(full_key)

            # Check the entry format
            style = entry.latin1()
            if style not in ['default', 'Windows', 'Motif',  'MotifPlus',
                'Platinum', 'SGI', 'CDE']:
                raise configException.SettingRetrievalException('style')

            # Convert the entry into the required value
            prop_value = style

        except configException.ConfigFileIOException, inst:
            print inst.error_message
        except configException.SettingRetrievalException, inst:
            print inst.error_message

        return prop_value


    def readLastWorkingDir(self):
        """
        Returns the lastWorkingDirectory property.

        This property is stored as a string.

        :Returns: a string representation of the property
        """

        # the property key and its default value
        key = 'Startup/lastWorkingDirectory'
        full_key = '%s/%s' % (self.base_key, key)
        prop_value = Config.confDef[key]

        try:
            # Read the entry from the configuration file/registry
            entry, is_ok = self.readEntry(full_key, prop_value)
            if not is_ok:
                raise configException.ConfigFileIOException(full_key)

            # Convert the entry into the required value
            prop_value = entry.latin1()

        except configException.ConfigFileIOException, inst:
            print inst.error_message

        return prop_value


    def readStartupWorkingDir(self):
        """
        Returns the startupWorkingDirectory property.

        This property is stored as a string.

        :Returns: a string representation of the property
        """

        # the property key and its default value
        key = 'Startup/startupWorkingDirectory'
        full_key = '%s/%s' % (self.base_key, key)
        prop_value = Config.confDef[key]

        try:
            # Read the entry from the configuration file/registry
            entry, is_ok = self.readEntry(full_key, prop_value)
            if not is_ok:
                raise configException.ConfigFileIOException(full_key)

            # Check the entry format
            swd = entry.latin1()
            if swd not in ['home', 'last']:
                raise configException.SettingRetrievalException('startup')

            # Convert the entry into the required value
            prop_value = swd

        except configException.ConfigFileIOException, inst:
            print inst.error_message
        except configException.SettingRetrievalException, inst:
            print inst.error_message

        return prop_value


    def readRestoreLastSession(self):
        """
        Read the restoreLastSession property.

        The property is stored as an integer.

        :Returns: a boolean representation of the property
        """

        # the property key and its default value
        key = 'Startup/restoreLastSession'
        full_key = '%s/%s' % (self.base_key, key)
        prop_value = Config.confDef[key]

        try:
            # Read the entry from the configuration file/registry
            entry, is_ok = self.readNumEntry(full_key, prop_value)
            if not is_ok:
                raise configException.ConfigFileIOException(full_key)

            # Check the entry format
            if entry not in [0, 1]:
                raise configException.SettingRetrievalException('session')

            # Convert the entry into the required value
            prop_value = entry

        except configException.ConfigFileIOException, inst:
            print inst.error_message
        except configException.SettingRetrievalException, inst:
            print inst.error_message

        return prop_value


    def readSessionFiles(self):
        """
        Returns the paths of files and nodes opened when the last session finished.

        :Returns: a list with format 
            ``[filepath1#@#mode#@#nodepath1#@#nodepath2, ...,
            filepath2#@#mode#@#nodepath1#@#nodepath2, ..., ...]``
        """
        return self.readFilePaths('Session/files')


    def readRecentFiles(self):
        """
        Returns the list of most recent files.

        :Returns:
            a list with format ``[mode#@#filepath1, mode#@#filepath2, ...]``
        """
        return self.readFilePaths('Recent/files')


    def readHelpBrowserHistory(self):
        """
        Returns the list of most recent URLs visited with the Help Browser.

        :Returns: a list with format ``[filepath1[#ID], filepath2[#ID], ...]``
        """
        return self.readFilePaths('HelpBrowser/history')


    def readHelpBrowserBookmarks(self):
        """
        Returns the list of bookmarks of the Help Browser.

        :Returns: a list with format ``[filepath1[#ID], filepath2[#ID], ...]``
        """
        return self.readFilePaths('HelpBrowser/bookmarks')


    def readFilePaths(self, key):
        """
        Returns a list filepaths.
        
        Filepaths for Recent files and last session files are retrieved
        with this method.

        :Returns: a list of strings
        """

        # the property key and its default value
        full_key = '%s/%s' % (self.base_key, key)
        prop_value = Config.confDef[key]

        try:
            # Read the entry from the configuration file/registry
            (entry, is_ok) = self.readEntry(full_key)
            if not is_ok:
                raise configException.ConfigFileIOException(full_key)

            # Check the entry format
            if entry.isEmpty():
                prop_value = []
            else:
                # Remove ' and " chars from the QString or you will get
                # a mess later on
                entry.remove('"').remove("'")
                # Separator must be ', '. See comments of writeProperty
                # method about it.
                prop_value = str(entry).split(', ')

        except configException.ConfigFileIOException, inst:
            print inst.error_message

        return prop_value


    def readWindowPosition(self, key='Geometry/position'):
        """
        Returns the geometry of the application window.

        This method allows for keeping the position and size of the
        main window between sessions. The widget position is stored
        in a sequence with format x, y, width, height.

        :Returns: a list with format ``[x, y, width, height]``
        """

        # the property key and its default value
        full_key = '%s/%s' % (self.base_key, key)
        prop_value = Config.confDef[key]

        try:
            # Read the entry from the configuration file/registry
            (entry, is_ok) = self.readEntry(full_key)
            if not is_ok:
                raise configException.ConfigFileIOException(full_key)

            # Check the entry format
            geometry = entry.latin1().split(',')
            if len(geometry) != 4:
                raise configException.SettingRetrievalException('geometry')

            # Convert the entry into the required value
            try:
                prop_value = [float(item) for item in geometry]
            except (TypeError, ValueError):
                raise configException.SettingRetrievalException('geometry')

        except configException.SettingRetrievalException, inst:
            print inst.error_message
        except configException.ConfigFileIOException, inst:
            print inst.error_message

        return prop_value


    def readHSplitterSizes(self):
        """Read the size of the horizontal splitter."""
        return self.readSplitterSizes('Geometry/hsplitter')


    def readVSplitterSizes(self):
        """Read the size of the vertical splitter."""
        return self.readSplitterSizes('Geometry/vsplitter')


    def readSplitterSizes(self, key):
        """
        Returns the sizes of the main window horizontal/vertical splitter.

        This method allows for keeping the sizes of the splitters
        (both horizontal and vertical) children between sessions.

        :Parameter key: the key being read

        :Returns: a list with format ``[width, height]``
        """

        # The property key and its default value
        full_key = '%s/%s' % (self.base_key, key)
        prop_value = Config.confDef[key]

        if key == 'Geometry/hsplitter':
            widget = 'tree pane'
        elif key == 'Geometry/vsplitter':
            widget = 'logger pane'

        try:
            # Read the entry from the configuration file/registry
            (entry, is_ok) = self.readEntry(full_key)
            if not is_ok:
                raise configException.ConfigFileIOException(full_key)

            # Check the entry format
            size = entry.latin1().split(',')
            if len(size) != 2:
                raise configException.SettingRetrievalException('size', widget)

            # Convert the entry into the required value
            try:
                prop_value = [float(item) for item in size]
            except (TypeError, ValueError):
                raise configException.SettingRetrievalException('size', widget)

        except configException.SettingRetrievalException, inst:
            print inst.error_message
        except configException.ConfigFileIOException, inst:
            print inst.error_message

        return prop_value


    def readWorkspaceBackground(self):
        """Returns Workspace/background or its default value."""
        return self.readColor('Workspace/background')


    def readLoggerPaper(self):
        """Returns Logger/Color/paper or its default value."""
        return self.readColor('Logger/paper')


    def readLoggerText(self):
        """Returns Logger/Color/text or its default value."""
        return self.readColor('Logger/text')


    def readColor(self, key):
        """
        Reads a color property from the config file.

        Colors are stored as lists of strings. This method takes such lists
        and, after some processing convert them into a qt.QColor instance.
        If the conversion cannot be done a None object is returned.

        :Parameter: key the key being read

        :Returns: a `qt.QColor` instance
        """

        # the property and its default value
        full_key = '%s/%s' % (self.base_key, key)
        prop_value = Config.confDef[key]

        try:
            # Read the entry from the configuration file/registry
            (entry, is_ok) = self.readEntry(full_key)
            if not is_ok:
                raise configException.ConfigFileIOException(full_key)

            # Check the entry format
            rgb_string = entry.latin1().split(',')
            if len(rgb_string) != 3:
                raise configException.SettingRetrievalException('color', key)

            # Convert the entry into the required value
            try:
                rgb = [int(channel) for channel in rgb_string]
                out_of_range = [True for item in rgb if item > 255]
                if True in out_of_range:
                    raise configException.SettingRetrievalException('color',
                        key)
                prop_value = qt.QColor(rgb[0], rgb[1], rgb[2])
            except (TypeError, ValueError):
                raise configException.SettingRetrievalException('color', key)

        except configException.ConfigFileIOException, inst:
            print inst.error_message
        except configException.SettingRetrievalException, inst:
            print inst.error_message

        return prop_value


    def readLoggerFont(self):
        """
        Reads a font property from the config file.

        Fonts are stored as lists of strings. This method takes such
        lists and, after some processing convert them into a qt.QFont
        instance. If the conversion cannot be done a None object is
        returned.

        :Parameter key: the key being read
        """

        # the property and its default value
        key = 'Logger/font'
        full_key = '%s/%s' % (self.base_key, key)
        prop_value = Config.confDef[key]

        try:
            # Read the entry
            (entry, is_ok) = self.readEntry(full_key)
            if not is_ok:
                raise configException.ConfigFileIOException(full_key)

            # Convert the entry into the required value
            font = qt.QFont()
            if font.fromString(entry):
                prop_value = font
            else:
                raise configException.SettingRetrievalException('font')

        except configException.SettingRetrievalException, inst:
            print inst.error_message
        except configException.ConfigFileIOException, inst:
            print inst.error_message

        return prop_value


    def writeProperty(self, subkey, value):
        """
        Write an entry to the configuration file.

        :Parameters:

        - `subkey`: the name of the property we want to set.
        - `value`: the value we want to assign to the property
        """

        key = '%s/%s' % (self.base_key, subkey)

        # First, the value is properly formatted. Geometry, color and
        # font settings are stored as strings with a sequence look
        if isinstance(value, list):
            # The list is converted to a QString. The braquets are removed.
            # Note that Python lists use ', ' (comma+blank) as separator so
            # str(a_list) will always look like "[e1, e2, ...]".
            prop_value = qt.QString(str(value)[1:-1])
        elif isinstance(value, qt.QFont):
            prop_value = value.toString()
        elif isinstance(value, qt.QBrush):
            prop_value = value.color()
            self.writeProperty(subkey, prop_value)
            return
        elif isinstance(value, qt.QColor):
            red = str(value.red())
            green = str(value.green())
            blue = str(value.blue())
            prop_value = qt.QString('%s,%s,%s' % (red, green, blue))
        else:
            # qt.QString instances and integers needn't be formatted
            prop_value = value

        # Second, the property is written to the config file
        try:
            if not self.writeEntry(key, prop_value):
                raise configException.ConfigFileIOException, \
                    '%s=%s' % (key, value)
        except configException.ConfigFileIOException, inst:
            print inst.error_message


