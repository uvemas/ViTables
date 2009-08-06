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

"""
Here is defined the utilities module. It contains functions that perform
tasks that are required at several parts of the application.
"""

__docformat__ = 'restructuredtext'

import sys
import os
import traceback
import sets
import time
import locale

import numpy

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import vitables.vtWidgets.renameDlg as renameDlg
from vitables.vtSite import *


ICONS_DICT = {}
HB_ICONS_DICT = {}
DEFAULT_LOCALE = locale.getdefaultlocale()[1]


def toUnicode(thing):
    """Convert a byte string into a unicode string using the default locale.
    """

    if isinstance(thing, str):
        # thing is a byte string, e.g. an attribute whose type is numpy.string_
        try:
            return unicode(thing, DEFAULT_LOCALE)
        except TypeError:
            return unicode(thing)
    else:
        # thing can be:
        # - a PyQt object, namely a QString or
        # - a numpy array, eg. a multidimensional attribute 
        #   like in examples/misc/MDobjects.h5
        # - a numpy scalar object, e.g. an attribute whose
        #   type is numpy.int32
        # - a pure Python object e.g. a sequence
        return unicode(thing)


def getVTApp():
    """Get a reference to the application instance.

    This is useful namely for plugins.
    """

    vtapp = None
    for widget in qApp.topLevelWidgets():
        if widget.objectName() == u'VTApp':
            vtapp = widget
            break

    return vtapp

#
# Icons related functions
#

def createIcons(large_icons, small_icons, icons_dict):
    """
    Create icons for different components of the GUI.

    The method creates sets of icons for the popup menus and the
    toolbar. It also creates icons for the tree of databases view
    and for the windows displaying leaves.

    :Parameters:

    - `large_icons`: the list of names of icons with size 22x22
    - `small_icons`: the list of names of icons with size 16x16
    - `icons_dict`: the icons dictionary to be updated
    """

    all_icons = large_icons.union(small_icons)

    for name in all_icons:
        icon = QIcon()
        if name in large_icons:
            pixmap = QPixmap(os.path.join(ICONDIR,'big_icons','%s.png') % name)
            pixmap.scaled(QSize(22, 22), Qt.KeepAspectRatio)
            icon.addPixmap(pixmap, QIcon.Normal, QIcon.On)
        if name in small_icons:
            pixmap = QPixmap(os.path.join(ICONDIR,'small_icons','%s.png') % name)
            icon.addPixmap(pixmap, QIcon.Normal, QIcon.On)
        icons_dict[name] = icon

    # Add an empty iconSet for the Default button of some dialogs
    icons_dict[''] = QIcon()

    # Application icon
    icons_dict['vitables_wm'] = QIcon(os.path.join(ICONDIR,'vitables_wm.png'))


def getIcons():
    """Return the icons dictionary to be used by the main window."""

    if not ICONS_DICT:
        large_icons = sets.Set([
            # Icons for toolbars
            'fileclose', 'filenew', 'fileopen', 'fileopen_popup', 
            'filesaveas', 'exit', 
            'editcopy', 'editcut', 'editdelete','editpaste', 'usersguide', 
            'new_filter', 'delete_filters', 
            # Icons for tree pane items
            'file_ro', 'file_rw', 'dbfilters', 'folder', 'folder_open'])

        small_icons = sets.Set([
            # Icons for menu items
            'fileclose', 'filenew', 'fileopen', 'filesaveas', 'exit', 
            'editcut', 'editcopy','editdelete','editpaste', 'info', 
            'folder_new', 
            'new_filter', 'delete_filters',
            'configure', 
            'appearance', 
            'usersguide', 
            # Icons for tree pane items
            'unimplemented', 
            'array', 'carray', 'earray', 'object', 
            'vlarray','table', 'vlstring', 
            # Icons for node views
            'zoom', 
            # Icons for buttons
            'cancel', 'ok'])

        createIcons(large_icons, small_icons, ICONS_DICT)

    return ICONS_DICT


def getHBIcons():
    """Return the icons dictionary to be used by the Help Browser."""

    if not HB_ICONS_DICT:
        large_icons = sets.Set([
        # Icons for toolbar
        'gohome', 'player_back', 'player_play', 'reload_page',
        'bookmark', 'bookmark_add', 'viewmag+', 'viewmag-', 'history_clear'])

        small_icons = sets.Set([
        # Icons for menu items
        'fileopen', 'exit',
        'viewmag+', 'viewmag-',
        'gohome', 'player_back', 'player_play', 'reload_page',
        'bookmark', 'bookmark_add',
        # Icons for buttons
        'ok', 'cancel', 'remove'])

        createIcons(large_icons, small_icons, HB_ICONS_DICT)

    return HB_ICONS_DICT

#
# QAction related functions
#

def createAction(parent, text, shortcut=None, slot=None, icon=None, tip=None,
                 checkable=False):
    """Create an action that will be added to a menu.

    This is a helper function which reduce the amount of typing needed
    for creating actions.

    :Parameters:

    - `parent`: the action parent
    - `text`: the action text
    - `shortcut`: the action shortcut
    -`slot`: the slot where the triggered SIGNAL will be connected
    - `icon`: the action icon
    - `tip`: the action status tip
    - `checkable`: True if the action is checkable
    """

    action = QAction(parent)
    action.setText(text)
    if icon is not None:
        action.setIcon(icon)
    if shortcut is not None:
        action.setShortcut(shortcut)
    if tip is not None:
#            action.setToolTip(tip)
        action.setStatusTip(tip)
    if checkable:
        action.setCheckable(True)
    if slot is not None:
        parent.connect(action, SIGNAL("triggered()"), slot)
    return action


def addActions(target, actions, actions_dict):
    """Add a list of actions to a menu or a toolbar.

    This is a helper function which make easier to add actions to a
    menu or a toolbar. Separators and submenus are also handled by this
    method.

    :Parameters:

    - `target`: the menu or toolbar where actions will be added
    - `actions`: the sequence of actions to be added
    """

    for action in actions:
        if action is None:
            target.addSeparator()
        elif isinstance(action, QMenu):
            target.addMenu(action)
        else:
            target.addAction(actions_dict[action])


def formatArrayContent(content):
    """
    Nicely format the contents of a table widget cell.

    Used when the cell contains a numpy array.
    """
    return numpy.array2string(content, separator=',')


def formatObjectContent(content):
    """
    Nicely format the contents of a table widget cell.

    Used in VLArrays with ``object`` pseudo atoms.

    Reading a VLArray with ``object`` pseudo atom returns a list of
    Python objects. This method formats that objects as unicode strings.
    str(content) will return an ``ASCII`` string so it can be converted
    into a unicode string via ``unicode(str(content), 'latin-1')``.
    This will fail only if content is a unicode string with some ordinal
    not in ``range(128)`` (raising a UnicodeEncodeError) but no problem
    because in that case content is already a unicode string and will be
    returned as is. So this method always returns the read object as a
    unicode string.
    """

    try:
        text = unicode(str(content), 'latin-1')
    except UnicodeEncodeError:
        text = content
    return text


def formatStringContent(content):
    """
    Nicely format the contents of a table widget cell.

    Used in VLArrays with ``vlstring`` or ``vlunicode`` pseudo atoms.
    If the pseudo atom is ``vlstring`` the method return a string. If
    the pseudo atom is ``vlunicode`` then a unicode string is returned.
    """

    return content


def formatTimeContent(content):
    """
    Nicely format the contents of a table widget cell.

    Used when:

    - the content atom is TimeAtom
    - content belongs to a time serie created via scikits.timeseries module
      and stored in the _dates column of a TimeSeriesTable table
    """

    return time.ctime(content)


def formatExceptionInfo(limit=1):
    """
    Format conveniently the catched exceptions.

    Takes the three-element tuple returned by `sys.exc_info()` and transforms
    each element into a more convenient form.

    :Parameter limit: the number of stack trace entries to be printed
    """

    print '\n%s\n' % traceback.format_exc(limit)

#
# Path related functions
#

def getHomeDir():
    """
    Get the user's home directory.

    How the directory is obtained depends on the platform. The returned
    path is used in QFileDialog calls.
    """

    if sys.platform.startswith('win'):
        home = os.getenv('HOMEDRIVE') + os.getenv('HOMEPATH')
        home = forwardPath(home)
    else:
        home = os.getenv('HOME')
    return QString(home)


def forwardPath(path):
    """Replace backslashes with slashes in a given path."""

    while path.count(chr(92)):
        path = path.replace(chr(92), '/')
    return path


def getFinalName(nodename, sibling, pattern, info):
    """Return the node name to be used when editing a node.

    Some node editing operations may raise naming issues because the
    name wanted for the edited node is already being used by a sibling
    node. These operations are:

    - paste
    - drop
    - rename
    - group creation

    If such naming issue arises, a dialog is displayed, and the user is
    required to decide what to do: choose a new name for the node being
    edited, overwrite the node which is currently using the troubled name
    or cancel the node editing.

    :Parameters:

    - `nodename`: the troubled name
    - `sibling`: a sequence with the sibling nodenames of the edited node
    - `pattern`: a regular expression pattern the nodename must match
    - `info`: the information to be displayed in the dialog
    """

    overwrite = False
    # Bad nodename condition
    nodename_in_sibling = nodename in sibling
    # If repeated, ask for a new nodename
    while nodename_in_sibling:
        dialog = renameDlg.RenameDlg(nodename, pattern, info)
        if dialog.exec_():
            nodename = dialog.action['new_name']
            overwrite = dialog.action['overwrite']
            del dialog
            if overwrite == True:
                break
            # Update the bad nodename condition
            nodename_in_sibling = nodename in sibling
        else:
            del dialog
            return None, None
    return nodename, overwrite


def customLineEdit(parent):
    """A customized QLineEdit suitable for the Properties dialog.

    The widget has no frame, is read-only and has a 'transparent'
    background.

    :Parameter parent: the parent widge of the QLineEdit
    """

    ledit = QLineEdit(parent)
    ledit.setFrame(False)
    ledit.setReadOnly(True)
    palette = ledit.palette()
    bg_color = palette.color(QPalette.Window)
    palette.setColor(QPalette.Base, bg_color)
    return ledit


def getLicense():
    """The ViTables license in Rich Text format."""

    input_file = QFile(":/LICENSE.html")
    input_file.open(QIODevice.ReadOnly)
    stream = QTextStream(input_file)
    license_text = stream.readAll()
    input_file.close()

    return license_text
