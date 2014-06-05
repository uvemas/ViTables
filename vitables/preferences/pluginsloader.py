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
import pkg_resources
import logging

from PyQt4 import QtGui

import vitables.utils

translate = QtGui.QApplication.translate

PLUGIN_GROUP = 'vitables.plugins'


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

        self.logger = logging.getLogger(__name__)
        # list of UID of enabled plugins, stored in configuration
        self.enabled_plugins = enabled_plugins
        # dictionary that contains all available plugins
        self.all_plugins = {}
        # instances of loaded plugins
        self.loaded_plugins = {}

    def _add_plugin_translator(self, module_name, plugin_class):
        """Try to load plugin translator."""
        app = QtGui.QApplication.instance()
        if hasattr(plugin_class, 'translator'):
            try:
                app.installTranslator(plugin_class.translator)
            except Exception as e:
                self.logger.error('Failed to install {0} plugin '
                                  'translator'.format(module_name))
                self.logger.error(e)

    def loadAll(self):
        """Find plugins in the system and crete instances of enabled ones."""
        for entrypoint in pkg_resources.iter_entry_points(PLUGIN_GROUP):
            plugin_class = entrypoint.load()
            self.all_plugins[plugin_class.UID] = {
                'UID': plugin_class.UID, 'name': plugin_class.NAME,
                'comment': plugin_class.COMMENT}
            if plugin_class.UID in self.enabled_plugins:
                self._add_plugin_translator(entrypoint.module_name,
                                            plugin_class)
                self.loaded_plugins[plugin_class.UID] = plugin_class()
