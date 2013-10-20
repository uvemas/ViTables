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
import collections
import functools

from vitables import utils as vtutils

from PyQt4 import QtGui
from PyQt4 import QtCore


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


def getDBsTreeModel():
    """Small wrapper to hide that vtapp.gui object contains dbs_tree_model.
    
    :return: the DBs tree model
    """
    return getVTGui().dbs_tree_model


def getVTGui():
    """Small wrapper to hide the fact that vtapp object contains gui.

    :return: main window object
    """
    return vtutils.getVTApp().gui


def addToMenuBar(menu):
    """Add menu to the menu bar into one before last position.

    Basically insert a menu before Help menu.

    :parameter menu: QMenu object

    :return: None
    """
    
    vtgui = getVTGui()
    menu_bar = vtgui.menuBar()
    last_action = menu_bar.actions()[-1]
    menu_bar.insertMenu(last_action, menu)


def insertInMenu(menu, entries, uid):
    """Insert entries to the given menu before the action named uid.

    The function accept a QAction/QMenu or an iterable. The entries will
    be added before the action whose name is uid.

    :Parameters:
    
    - `menu`: the menu or context menu being updated
    - `entries`: QAction/Qmenu object or a list of such objects
    - `uid`: indicates the insertion position for the new entries

    :return: None
    """

    if not isinstance(entries, collections.Iterable):
        entries = [entries]

    if isinstance(entries[0], QtGui.QAction):
        menu.insertEntry = menu.insertAction
    elif isinstance(entries[0], QtGui.QMenu):
        menu.insertEntry = menu.insertMenu

    for item in menu.actions():
        if item.objectName() == uid:
            for a in entries:
                menu.insertEntry(item, a)


def addToMenu(menu, entries):
    """Add entries at the end of the given menu.

    The function accept a QAction/QMenu or an iterable. Entries will be
    preceded with a separator and added at the end of the menu.

    :Parameters:
    
    - `menu`: the menu or context menu being updated
    - `entries`: QAction/QMenu object or a list of such objects

    :return: None
    """

    if not isinstance(entries, collections.Iterable):
        entries = [entries]

    if isinstance(entries[0], QtGui.QAction):
        menu.addEntry = menu.addAction
    elif isinstance(entries[0], QtGui.QMenu):
        menu.addEntry = menu.addMenu

    menu.addSeparator()
    for a in entries:
        menu.addEntry(a)


def addToLeafContextMenu(actions):
    """Add entries at the end of the leaf context menu.

    The function accept a QAction/QMenu or an iterable. Entries will be
    preceded with a separator and added at the end of the menu.

    :parameter actions: QAction/QMenu object or a list of such objects

    :return: None
    """

    context_menu = getVTGui().leaf_node_cm
    addToMenu(context_menu, actions)


def addToGroupContextMenu(actions):
    """Add entries at the end of the group context menu.

    The function accept a QAction/QMenu or an iterable. Entries will be
    preceded with a separator and added at the end of the menu.

    :parameter actions: QAction/QMenu object or a list of such objects

    :return: None
    """

    context_menu = getVTGui().group_node_cm
    addToMenu(context_menu, actions)


def getSelectedLeaf():
    """Get selected database object.

    :return: pytables object
    """

    current = getVTGui().dbs_tree_view.currentIndex()
    leaf = getVTGui().dbs_tree_model.nodeFromIndex(current).node
    return leaf


def long_action(message=None):
    """Decorator that changes the cursor to the wait cursor.

    Used with functions that take some time finish. The provided
    message is displayed in the status bar while the function is
    running (the status bar is cleaned afterwards). If the message is
    not provided then the status bar is not updated.

    :parameter message: message to be displayed in the status bar
    while the function is running

    """
    def _long_action(f):
        @functools.wraps(f)
        def __long_action(*args, **kwargs):
            status_bar = getVTGui().statusBar()
            if message is not None:
                status_bar.showMessage(message)
            QtGui.QApplication.setOverrideCursor(
                QtGui.QCursor(QtCore.Qt.WaitCursor))
            try:
                res = f(*args, **kwargs)
            finally:
                QtGui.QApplication.restoreOverrideCursor()
                if message is not None:
                    status_bar.clearMessage()
            return res
        return __long_action
    return _long_action
