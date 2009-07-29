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

import pkgutil
import imp
import inspect

class PluginsMgr(object):
    """Plugins manager class.

    Every module|package under the plugins directory is a plugin. At the
    moment packages can contain module plugins only at top level because
    the plugins manager doesn't iterate recursively over the package looking
    for plugins.
    """

    def __init__(self):
        """Dynamically load and instantiate the available plugins."""

        from vitables.plugins import __path__ as plugins_path
        self.registered_plugins = {}

        # Plugins can live in plain modules or packages
        modules = ()
        packages = ()
        for loader, name, ispkg in pkgutil.iter_modules(plugins_path):
            # Separate plugins living in modules from those living in packages
            if name in ['pluginsManager']:
                continue
            if not ispkg:
                modules = modules + (name,)
            else:
                packages = packages + (name,)

        self.loadModulePlugins(modules, plugins_path)
        self.loadPackagePlugins(packages, plugins_path)


    def loadModulePlugins(self, modules, plugins_path):
        """Load plugins stored in plain modules.

        :Parameters:
            - modules: tuple with the plugins names
            - plugins_path: string with the plugins path
        """

        # Load plugins stored in plain modules
        for name in modules:
            try:
                file_obj, filepath, desc = imp.find_module(name, plugins_path)
                if file_obj is None:
                    continue
                module = imp.load_module(name, file_obj, filepath, desc)
            except ImportError:
                print "Error: module %s cannot be loaded" % name
            finally:
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

            class_name = getattr(module, 'plugin_class', None)
            if class_name:
                cls = getattr(module, class_name)
                instance = cls()

                # Register plugin
                self.registered_plugins[class_name] = instance



    def loadPackagePlugins(self, packages, plugins_path):
        """Load plugins stored in packages.

        :Parameters:
            - modules: tuple with the plugins names
            - plugins_path: string with the plugins path
        """

        # Load plugins stored in packages
        for pkg_name in packages:
            modules = ()
            new_path = [plugins_path[0] + pkg_name]
            for loader, name, ispkg in pkgutil.iter_modules(new_path):
                modules = modules + (name,)
            self.loadModulePlugins(modules, new_path)

