#!/usr/bin/env python2
# -*- coding: utf-8 -*-

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

"""Different functions that facilitate plugin writing.

The main purpose is to hide application implementation details from
plugin writers.
"""

__docformat__ = 'restructuredtext'

import logging

from vitables import utils as vtutils

def getLogger(plugin_name=None):
    """Get logger object.

    This function is needed just to standardize logger names and
    ensure that all log objects belong to vitables which was properly
    configured.

    :parameter plugin_name: the name that will be used in log output
    to identify the source

    :return: logger object
    """
    logger_name = 'vitables'
    if plugin_name is not None:
        logger_name += '.plugin.' + plugin_name
    logger = logging.getLogger(logger_name)
    return logger

def getVTGui():
    """Small wrapper to hide the fact that vtapp object contains gui.

    :return: main window object
    """
    return vtutils.getVTApp().gui

def addToMainMenu(submenu):
    """Add submenu to the main menu bar into one before last position.

    Basically insert a submenu before Help menu.

    :parameter submenu: QMenu object

    :return: None
    """
    vtgui = getVTGui()
    main_menu = vtgui.menuBar()
    last_action = main_menu.actions()[-1]
    main_menu.insertMenu(last_action, submenu)
