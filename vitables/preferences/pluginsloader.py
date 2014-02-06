#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

"""The plugins loader module.

Every module under the plugins directory is a plugin.
This module finds, loads, instantiates and registers the available plugins.

There are (at least) 2 approaches for loading the plugins under
the plugins directory:

a) to iterate over a list of module names
b) to iterate over the content of the plugins directory

Syntax of a) is simpler (see below) but b) seems to be more general and
powerful as it can deal with packages too. So *at the moment* I'll use the
approach b). In the future a better defined plugins infrastructure may be used.

FYI, approach a) looks like::

    from vitables.plugins import __all__ as plugins
    for plugin in plugins:
        try:
            module_name = 'vitables.plugins.' + plugin
            __import__(module_name)
            module = sys.modules[module_name]
        except ImportError:
            print "Error: module %s cannot be loaded" % module_name
"""

__docformat__ = 'restructuredtext'

import os
import importlib
import pkgutil
import sys

from PyQt4 import QtGui

import vitables.utils
from vitables.vtsite import PLUGINSDIR
from vitables.plugin_utils import getLogger

LOGGER = getLogger()


translate = QtGui.QApplication.translate


def pluginDesc(mod_path, folder=None):
    """Check if a given module is a plugin and return its description.

    :Parameter mod_path: the import absolute path of the module being tested
    """

    # Import the module
    # This is a little bit convoluted but when doing things in the common way
    # some errors are swallowed by the system for reasons unknown to me and no
    # error is raised
    try:
        imported_module = importlib.import_module(mod_path)
        if type(imported_module) != type(os):
            raise ImportError
    except (SyntaxError, ImportError, IOError, SystemError):
        LOGGER.error("""Failed to load the module {0} which belongs to a plugin
                     .\ntraceback: {1}""".format(mod_path, sys.exc_info()[:2]))
        return False

    # Check if module is a plugin
    try:
        plugin_name = getattr(imported_module, 'plugin_name')
        comment = getattr(imported_module, 'comment')
        pkg_name = mod_path.split('.')[-2]
        mod_name = mod_path.split('.')[-1]
        folder = os.path.join(PLUGINSDIR, pkg_name)
        desc = {'UID': '{0}#@#{1}'.format(plugin_name, comment),
            'mod_name': mod_name,
            'mod_path': mod_path,
            'folder': folder,}
        return desc
    except AttributeError:
        # then unexpected errors can occur
        return False

    #######################################################
    #
    # WARNING!!! DO NOT DELETE MODULES AFTER CHECKING
    #
    # Deletion has unwanted side effects. For instance,
    # deleting the time_series module results in deleting
    # the tables module!!!
    #
    #######################################################

    # finally:
        # path = '%s.py' % os.path.join(folder, name)
        # modname = inspect.getmodulename(path)
        # del sys.modules[modname]
        # del module


def scanFolder(package_root):
    """Scan a package looking for plugins.

    This is a non recursive method. It scans only the top level of
    the package.

    :Parameter package_root: the top level folder of the package being scanned
    """

    pkg_plugins = {}
    folder = os.path.join(PLUGINSDIR, package_root)
    if not os.path.exists(folder):
        LOGGER.error('Failed to find a plugin in folder {folder}:'
                     'Folder does not exist'.format(folder))
    else:
        for module_finder, name, ispkg in pkgutil.iter_modules([folder]):
            if not ispkg:
                module_path = '.'.join(['vitables', 'plugins', package_root,
                                        name])
                desc = pluginDesc(module_path)
                if desc:
                    pkg_plugins[desc['UID']] = desc
    return pkg_plugins


class PluginsLoader(object):
    """Plugins loader class.

    Every module|package under the plugins directory is a plugin. At the
    moment packages can contain module plugins only at top level because
    the plugins manager doesn't iterate recursively over the package looking
    for plugins.

    :Parameter enabled_plugins: a list with the UIDs of the enabled plugins
    """

    def __init__(self, enabled_plugins):
        """Dynamically load and instantiate the available plugins.
        """

        self.enabled_plugins = enabled_plugins[:]
        self.all_plugins = {}
        self.loaded_plugins = {}

        # Update plugins information: available plugins, disabled plugins
        self.register()


    def register(self):
        """Update the list of available plugins.

        This method MUST be called every time that the plugins
        configuration changes.
        """

        # Traverse the plugins folder looking for plugins
        self.all_plugins = {}
        for loader, name, ispkg in pkgutil.iter_modules([PLUGINSDIR]):
            if not ispkg:
                desc = pluginDesc(name)
                if desc:
                    self.all_plugins[desc['UID']] = desc
            else:
                pkg_plugins = scanFolder(name)
                self.all_plugins.update(pkg_plugins)



    def loadAll(self):
        """Try to load the enabled plugins.
        """

        if self.enabled_plugins == []:
            return
        for UID in self.enabled_plugins:
            self.load(UID)


    def load(self, UID):
        """Load a given plugin.

        :Parameter UID: the UID of the plugin being loaded
        """

        # Load the module where the plugin lives
        try:
            plugin = self.all_plugins[UID]
            mod_path = plugin['mod_path']
            mod_name = '.'.split(mod_path)[-1]
            imported_module = importlib.import_module(mod_path)
        except (ImportError, IOError, SystemError):
            self.untrack(UID)
            LOGGER.error("\nError: plugin {0} cannot be loaded.".
                         format(mod_name))
            return
        except KeyError:
            LOGGER.error('\nError:  plugin {0} can not be found'.
                         format(mod_name))
            return

        # Retrieve the plugin class
        try:
            class_name = getattr(imported_module, 'plugin_class')
            cls = getattr(imported_module, class_name)
        except AttributeError:
            self.untrack(UID)
            LOGGER.error("\nError: module {0} is not a valid plugin.".
                         format(mod_name))
            return

        # Load the plugin
        try:
            instance = cls()

            # Register plugin
            # In some cases keeping a reference to instance is a must
            # (for example, the time_series plugin)
            self.loaded_plugins[UID] = instance
        except (KeyError, ValueError):
            self.untrack(UID)
            LOGGER.error("\nError: plugin {0} cannot be loaded.".
                         format(mod_name))
            vitables.utils.formatExceptionInfo()
            return


    def untrack(self, UID):
        """Remove a plugin from the lists of available/enabled plugins.

        Plugins that cannot be loaded should be removed using this method.

        :Parameter UID: the UID of the plugin being removed
        """

        try:
            del self.all_plugins[UID]
        except KeyError:
            pass

        try:
            self.enabled_plugins.remove(UID)
        except IndexError:
            pass

