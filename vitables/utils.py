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
#       $Id: utils.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the resources module.

Functions:

* getHomeDir()
* createIcons()
* getIcons()
* customizeWidgetButtons(widget, icons=None)
* addRow(label, text, parent)
* makeLineEdit(text, parent, read_write = False, frame = False)
* formatArrayContent(content)
* formatObjectContent(content)
* formatStringContent(content)
* formatExceptionInfo()
* getLicense()
* forwardPath(path)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import sys
import os
import traceback

import numpy
import tables.exceptions

import qt

import vitables.vtSite

ICONS_DICT = {}

#
# Widget related functions
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
    return home


def createIcons():
    """
    Create icons for different components of the GUI.

    The method creates sets of icons for the popup menus and the
    toolbar. It also creates icons for the QListViewItems of the
    object tree and for the windows displaying leaves.
    """

    icons_directory = '%s/icons' % vitables.vtSite.DATADIR

    large_icons = [
        # Icons for toolbars
        'fileclose', 'filenew', 'fileopen', 'fileopen_popup', 'filesaveas', 'exit',
        'editcopy', 'editcut', 'editdelete','editpaste', 'usersguide',
        # Icons for tree pane items
        'file_ro', 'file_rw', 'dbfilters', 'folder', 'folder_open']
        
    small_icons = [
        # Icons for menu items
        'fileclose', 'filenew', 'fileopen', 'filesaveas', 'exit',
        'editcut', 'editcopy','editdelete','editpaste', 'info', 'folder_new',
        'new_filter',
        'appearance',
        'usersguide',
        # Icons for tree pane items
        'unimplemented',
        'array', 'carray', 'earray', 'object',
        'vlarray', 'vlstring','table',
        # Icons for node views
        'zoom',
        # Icons for buttons
        'cancel', 'ok']

    all_icons = [
        'fileclose', 'filenew', 'fileopen', 'fileopen_popup', 'file_ro', 'file_rw',
        'filesaveas', 'exit',
        'editcut', 'editcopy', 'editdelete','editpaste', 'info', 'folder_new',
        'new_filter', 'appearance', 'usersguide',
        'dbfilters', 'folder', 'folder_open', 'table',  'array','carray',
        'earray', 'vlarray', 'vlstring','object', 'unimplemented',
        'zoom',
        'cancel', 'ok']

    for name in all_icons:
        iconset = qt.QIconSet()
        if name in large_icons:
            iconset.setIconSize(qt.QIconSet.Large, qt.QSize(22, 22))
            file_name = 'big_icons/%s.png' % name
            file_path = '%s/%s' % (icons_directory, file_name)
            pixmap = qt.QPixmap()
            pixmap.load(file_path)
            iconset.setPixmap(pixmap, qt.QIconSet.Large, qt.QIconSet.Normal,
                qt.QIconSet.On)
        if name in small_icons:
            file_name = 'small_icons/%s.png' % name
            file_path = '%s/%s' % (icons_directory, file_name)
            pixmap = qt.QPixmap()
            pixmap.load(file_path)
            iconset.setPixmap(pixmap, qt.QIconSet.Small, qt.QIconSet.Normal,
                qt.QIconSet.On)
        ICONS_DICT[name] = iconset

    # Add an empty iconSet for the Default button of some dialogs
    ICONS_DICT[''] = qt.QIconSet()

    # Application icon
    pixmap = qt.QPixmap()
    pixmap.load('%s/vitables_wm.png' % icons_directory)
    ICONS_DICT['vitables_wm'] = pixmap


def getIcons():
    """Return the icons dictionary."""

    if not ICONS_DICT:
        createIcons()

    return ICONS_DICT


def customizeWidgetButtons(widget, icons=None):
    """
    Customize the widget style.

    QFileDialog.getOpenFileName and other statics methods of making
    dialogs don't give access to the dialog buttons, so don't allow to
    customize them. As a workaround, dialogs are created via
    constructors and passed to this function, that traverses the dialog
    widget looking for its buttons. Found buttons are customized by
    adding to them the appropriate icon.
    The function can be aplied to any kind of widget, not only dialogs.

    :Parameters:

        - `widget`: the widget being customized.
        - `icons`: the icons dictionary
    """

    # There is a bug in Qt-3.3 that causes that buttons with icon+label
    # display its content left justified instead of center. In most cases
    # this could be circumvented with the customStyle module, but with
    # MacOS X it still gives some problems
    label2icon = {'&OK': 'ok', 'OK': 'ok', 'Aceptar': 'ok',
        'Cancel': 'cancel', '&Cancel': 'cancel', 'Cancelar': 'cancel',
#        'Apply': 'apply', 'Aplicar': 'apply', 
        'Default': '', 'Prefijado': ''}

    font = qt.qApp.font()
    font.setBold(False)

    # Customize the dialog buttons
    for child in widget.children():
        if isinstance(child, qt.QButton):
            button = child # Just for code clarity
            label = button.text().latin1()
            if label in label2icon.keys():
#                iconName = label2Icon[label]
#                button.setIconSet(icons[iconName])
                button.setFont(font)


def addRow(label, text, parent):
    """
    Add a row to a given widget.

    This is a helper method to add rows of labels in a widget. The
    rows look like::

        name: + value + stretchable space

    where ``name:`` and ``value`` are labels. The first one is bold, the
    other is not.

    :Parameters:

        - `label`: the leftmost label of the row
        - `text`: the text for the second label
        - `parent`: the labels parent widget
    """

    row_layout = qt.QHBoxLayout(parent.layout(), 5)
    
    row_layout.addWidget(label)

    value = qt.QLabel(text, parent)
    parent_font = parent.font()
    parent_font.setBold(0)
    value.setFont(parent_font)
    row_layout.addWidget(value)

    row_layout.addStretch(1)


def makeLineEdit(text, parent, read_write = False, frame = False):
    """
    Customised text boxes for Properties dialogs.

    Customised boxes may have or not a frame. If boxes are not editable
    then their background is gray. The method makes sure that the font
    is not bold.

    :Parameters:
    
        - `text`: the text of the text box
        - `parent`: the parent widget of the text box
        - `rw`: whether the widget is editable or not
        - `frame`: whether the widget has a frame or not
    """

    ledit = qt.QLineEdit(text, parent)

    ledit.setReadOnly(not read_write)

    parent_font = parent.font()
    parent_font.setBold(0)
    ledit.setFont(parent_font)

    ledit.setFrame(frame)

    if read_write:
        ledit.setEraseColor(qt.QTextEdit().palette().color(qt.QPalette.Active,
            qt.QColorGroup.Base))
    else:
        ledit.setEraseColor(qt.QTextEdit().palette().color(qt.QPalette.Disabled,
            qt.QColorGroup.Background))

    return ledit


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


#
# tables related functions
#

def formatExceptionInfo(limit=1):
    """
    Format conveniently the catched exceptions.

    Takes the three-element tuple returned by `sys.exc_info()` and transforms
    each element into a more convenient form.

    :Parameter limit: the number of stack trace entries to be printed
    """

    print '\n%s\n' % traceback.format_exc(limit)

#
# Help system related functions
#

def getLicense():
    """The ViTables license in Rich Text format."""

    license_path =  os.path.join(vitables.vtSite.DATADIR, 'LICENSE.html')
    input_file = open(license_path, 'r')
    license_text = input_file.read()
    input_file.close()

    return """%s""" % license_text

#
# Misc
#

def forwardPath(path):
    """Replace backslashes with slashes in a given path."""

    while path.count(chr(92)):
        path = path.replace(chr(92), '/')
    return path

