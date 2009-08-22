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

"""The plugins manager module.

Every module (but this one) under the plugins directory is a plugin.
This module finds, loads, instantiates and registers the available plugins.

There are (at least) 2 approaches for loading the plugins under
the plugins directory:

a) to iterate over a list of module names
b) to iterate over the content of the plugins directory

Syntax of a) is simpler (see below) but b) seems to be more general and
powerful as it can deal with packages too. So *at them moment* I'll use the
approach b). In the future a better defined plugins infrastructure may be used.

FYI, approach a) looks like:

from vitables.plugins import __all__ as plugins
plugins.remove('pluginsManager')
for plugin in plugins:
    try:
        module_name = 'vitables.plugins.' + plugin
        __import__(module_name)
        module = sys.modules[module_name]
    except ImportError:
        print "Error: module %s cannot be loaded" % module_name
"""

__docformat__ = 'restructuredtext'

import sys
import os
import pkgutil
import imp
import inspect

import vitables.plugins
from vitables.vtSite import PLUGINSDIR

class PluginsMgr(object):
    """Plugins manager class.

    Every module|package under the plugins directory is a plugin. At the
    moment packages can contain module plugins only at top level because
    the plugins manager doesn't iterate recursively over the package looking
    for plugins.
    """

    def __init__(self, plugins_paths, enabled_plugins):
        """Dynamically load and instantiate the available plugins.

        :Parameters:

        - plugins_paths: a QStringList with the paths where plugins live
        - enabled_plugins: a QStringList with the UIDs of the enabled plugins
        """

        # Move from PyQt QStringLists to python lists
        self.plugins_paths = [unicode(item) for item in plugins_paths]
        self.enabled_plugins = [unicode(item) for item in enabled_plugins]

        # Ensure that plugins distributed along with ViTables are
        # always available
        if PLUGINSDIR not in self.plugins_paths:
            self.plugins_paths.append(PLUGINSDIR)

        # Make sure that other plugins (if any) are available
        for path in self.plugins_paths:
            if os.path.isabs(path) and (path not in sys.path):
                sys.path= [path] + sys.path

        # Some useful stuff
        self.all_plugins = []
        self.disabled_plugins = []

        # Update plugins information: available plugins, disabled plugins
        self.updatePluginsInfo()

        # Try to load the enabled plugins
        self.loaded_plugins = {}
        if self.enabled_plugins == []:
            return
        for plugin in self.enabled_plugins:
            self.loadPlugin(plugin)


    def scanFolder(self, folder):
        """Scan a package looking for plugins.

        This is a non recursive method. It scans only the top level of
        the package.

        :Parameters:
            - folder: the folder being scanned
        """

        pkg_plugins = []
        for loader, name, ispkg in pkgutil.iter_modules([folder]):
            if not ispkg and self.isPlugin(folder, name):
                pkg_plugins.append('%s#@#%s' % (folder, name))
        return pkg_plugins


    def isPlugin(self, folder, name):
        """Check if a given module is a plugin.

        :Parameters:
            - folder: the folder where the module being tested lives
            - name: the filename of the module being tested
        """

        # Import the module
        try:
            finding_failed = True
            file_obj, filepath, desc = imp.find_module(name, [folder])
            finding_failed = False
            module = imp.load_module(name, file_obj, filepath, desc)
        except ImportError:
            return False
        finally:
            if not finding_failed:
                file_obj.close()

        # Check if module is a plugin
        try:
            class_name = getattr(module, 'plugin_class')
            return class_name
        except AttributeError:
            return False
        finally:
            path = '%s.py' % os.path.join(folder, name)
            modname = inspect.getmodulename(path)

            #######################################################
            #
            # WARNING!!! DO NOT DELETE MODULES AFTER CHECKING
            #
            # Deletion has unwanted side effects. For instance,
            # deleting the time_series module results in deleting
            # the tables module!!!
            #
            #######################################################

            # del sys.modules[modname]
            # del module


    def updatePluginsInfo(self):
        """Update info regarding plugins.

        This method MUST be called every time that:

        - the list of plugins paths changes
        - the list of enabled plugins changes
        """

        self.all_plugins = []
        for folder in self.plugins_paths:
            for loader, name, ispkg in pkgutil.iter_modules([folder]):
                if not ispkg and self.isPlugin(folder, name):
                    self.all_plugins.append('%s#@#%s' % (folder, name))
                else:
                    pkg_plugins = self.scanFolder(os.path.join(folder, name))
                    self.all_plugins = self.all_plugins + pkg_plugins

        self.disabled_plugins = [plugin for plugin in self.all_plugins \
            if plugin not in self.enabled_plugins]


    def loadPlugin(self, plugin):
        """Load a given plugin.

        :Parameters:
            - plugin: th UID of the plugin being loaded
        """

        try:
            finding_failed = True
            (folder, name) = plugin.split('#@#')
            file_obj, filepath, desc = imp.find_module(name, [folder])
            finding_failed = False
            module = imp.load_module(name, file_obj, filepath, desc)
        except ImportError:
            #vitables.utils.formatExceptionInfo()
            if finding_failed:
                print """\nError: plugin %s cannot be found.""" % name
            else:
                print """\nError: plugin %s cannot be loaded.""" % name
            return
        finally:
            if not finding_failed:
                file_obj.close()

        # Instantiate plugin classes
        #module_classes = [cls for (name, cls) in \
        #    inspect.getmembers(module, inspect.isclass)
        #    if inspect.getmodule(cls) == module]
        #for cls in module_classes:
        #    if getattr(cls, 'is_plugin', None):
        #        instance = cls()
        #        # Register plugin
        #        self.registered_plugins[class_name] = instance

        try:
            class_name = getattr(module, 'plugin_class')
            cls = getattr(module, class_name)
            instance = cls()

            # Register plugin
            # In some cases keeping a reference to instance is a must
            # (for example, the time_series plugin)
            self.loaded_plugins[plugin] = instance
        except AttributteError:
                print """\nError: module %s is not a plugin.""" % name
