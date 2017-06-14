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

"""The plugins loader module.

For information about the pkg_resources module see
http://setuptools.readthedocs.io/en/latest/pkg_resources.html
"""

__docformat__ = 'restructuredtext'

import pkg_resources
import logging
import traceback

from qtpy import QtGui
from qtpy import QtWidgets

translate = QtWidgets.QApplication.translate

PLUGIN_GROUP = 'vitables.plugins'

log = logging.getLogger(__name__)


def _add_plugin_translator(module_name, plugin_class):
    """Try to load plugin translator."""

    app = QtWidgets.QApplication.instance()
    if hasattr(plugin_class, 'translator'):
        try:
            app.installTranslator(plugin_class.translator)
        except Exception as e:
            log.error('Failed to install {0} plugin '
                      'translator'.format(module_name))
            log.error(e)


def _load_entrypoint(entrypoint):
    """Try to load an entry point."""

    plugin_class = None
    try:
        plugin_class = entrypoint.load()
    except Exception as e:
        log.error('Failed to load plugin: {0}'.format(
            entrypoint.module_name))
        log.error(e)
        log.info(traceback.format_exc())
    return plugin_class


def _create_instance(plugin_class):
    """Try to create an instance of the given plugin class."""

    instance = None
    try:
        instance = plugin_class()
    except Exception as e:
        log.error('Failed to create plugin instance')
        log.error(e)
        log.info(traceback.format_exc())
    return instance


class PluginsLoader(object):
    """Plugins loader class.

    The class loads enabled plugins and their translations and stores
    info about them.

    """

    def __init__(self, enabled_plugins):
        """Assign default values to members.
        """

        # list of UID of enabled plugins, stored in configuration
        self.enabled_plugins = enabled_plugins
        # dictionary that contains all available plugins
        self.all_plugins = {}
        # instances of loaded plugins
        self.loaded_plugins = {}

    def _disable_not_loaded(self):
        self.enabled_plugins = list(self.loaded_plugins.keys())

    def loadAll(self):
        """Find plugins in the system and create instances of enabled ones."""

        for entrypoint in pkg_resources.iter_entry_points(PLUGIN_GROUP):
            plugin_class = _load_entrypoint(entrypoint)
            if plugin_class is None:
                continue
            self.all_plugins[plugin_class.UID] = {
                'UID': plugin_class.UID, 'name': plugin_class.NAME,
                'comment': plugin_class.COMMENT}
            if plugin_class.UID in self.enabled_plugins:
                _add_plugin_translator(entrypoint.module_name,
                                       plugin_class)
                instance = _create_instance(plugin_class)
                if instance is not None:
                    self.loaded_plugins[plugin_class.UID] = instance
        self._disable_not_loaded()
