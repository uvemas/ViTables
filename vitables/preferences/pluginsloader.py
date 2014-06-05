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
"""

__docformat__ = 'restructuredtext'

import pkg_resources
import logging

from PyQt4 import QtGui

translate = QtGui.QApplication.translate

PLUGIN_GROUP = 'vitables.plugins'


class PluginsLoader(object):
    """Plugins loader class.

    The class loads enabled plugins and their translations and stores
    info about them.

    """

    def __init__(self, enabled_plugins):
        """Assign default values to members.
        """

        self._logger = logging.getLogger(__name__)
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
                self._logger.error('Failed to install {0} plugin '
                                   'translator'.format(module_name))
                self._logger.error(e)

    def _disable_not_loaded(self):
        self.enabled_plugins = list(self.loaded_plugins.keys())

    def loadAll(self):
        """Find plugins in the system and crete instances of enabled ones."""
        self._logger.debug('Enabled plugins: {0}'.format(
            str(self.enabled_plugins)))
        for entrypoint in pkg_resources.iter_entry_points(PLUGIN_GROUP):
            plugin_class = entrypoint.load()
            self._logger.debug('Found plugin: {0}'.format(
                entrypoint.module_name))
            self.all_plugins[plugin_class.UID] = {
                'UID': plugin_class.UID, 'name': plugin_class.NAME,
                'comment': plugin_class.COMMENT}
            if plugin_class.UID in self.enabled_plugins:
                self._logger.debug('Loading plugin: {0}'.format(
                    entrypoint.name))
                self._add_plugin_translator(entrypoint.module_name,
                                            plugin_class)
                self.loaded_plugins[plugin_class.UID] = plugin_class()
        self._disable_not_loaded()
