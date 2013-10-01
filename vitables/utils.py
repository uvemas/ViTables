#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
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

"""
This is the utilities module. It contains functions that perform
tasks that are required at several parts of the application.
"""

__docformat__ = 'restructuredtext'

import sys
import os
import traceback
import locale

import numpy

from PyQt4 import QtCore
from PyQt4 import QtGui

import vitables.vtwidgets.renamedlg as renamedlg
from vitables.vtsite import ICONDIR, DOCDIR


ICONS_DICT = {}
HB_ICONS_DICT = {}
DEFAULT_ENCODING = locale.getdefaultlocale()[1]


def toUnicode(thing):
    """Convert byte strings into unicode strings using the default locale.

    Conversion to unicode is required when showing data in dialogs and
    tables. The User Attributes of the node Properties dialog requires
    special care because it can show data with a wide variety of types.
    """

    if isinstance(thing, str):
        # thing is a byte string, e.g. an attribute whose type is numpy.string_
        try:
            return unicode(thing, DEFAULT_ENCODING)
        except TypeError:
            return unicode(thing)
    else:
        # thing can be:
        # - a PyQt object or
        # - a numpy array, eg. a multidimensional attribute
        #   like in examples/misc/MDobjects.h5
        # - a numpy scalar object, e.g. an attribute whose
        #   type is numpy.int32
        # - a pure Python object e.g. a sequence
        return unicode(thing)


def getVTApp():
    """Get a reference to the `VTApp` instance.

    This is useful namely for plugins.
    """

    vtapp = None
    for widget in QtGui.qApp.topLevelWidgets():
        if widget.objectName() == u'VTGUI':
            vtapp = widget.vtapp
            break

    return vtapp


def getFileSelector(parent, caption, dfilter, filepath='', settings=None):
    """Raise a customised file selector dialog.

    :Parameters:

    - `parent`: the parent widget
    - `caption`: the dialog caption
    - `dfilter`: filters used to display files and folders
    - `filepath`: the filepath initially selected
    - `settings`: dictionary with keys `label` (Accept button text),
        `history` (file selector history) , `accept_mode` and `file_mode`
    """

    file_selector = QtGui.QFileDialog(parent, caption, '', dfilter)
    # Misc. setup
    file_selector.setDirectory(settings['history'][-1])
    file_selector.setAcceptMode(settings['accept_mode'])
    if settings['accept_mode'] == QtGui.QFileDialog.AcceptSave:
        file_selector.setConfirmOverwrite(False)
    file_selector.setFileMode(settings['file_mode'])
    file_selector.setHistory(settings['history'])
    if filepath:
        file_selector.selectFile(filepath)
    if settings['label'] != '':
        file_selector.setLabelText(QtGui.QFileDialog.Accept,
            settings['label'])

    # Uncomment next line if you want native dialogs. Removing the comment
    # comes at the price of an annoying KDE warning in your console. See the
    # thread "A dire warning message" (July, 2011) in the pyQt4 mailing list
    # for details.
    #file_selector.setOption(QtGui.QFileDialog.DontUseNativeDialog)
    return file_selector


def getFilepath(parent, caption, dfilter, filepath='', settings=None):
    """Raise a file selector dialog and get a filepath.

    :Parameters:

    - `parent`: the parent widget
    - `caption`: the dialog caption
    - `dfilter`: filters used to display files and folders
    - `filepath`: the filepath initially selected
    - `settings`: dictionary with keys `label` (Accept button text),
        `history` (file selector history) , `accept_mode` and `file_mode`
    """

    working_dir = None
    file_selector = \
        getFileSelector(parent, caption, dfilter, filepath, settings)

    # Execute the dialog
    try:
        if file_selector.exec_():  # OK clicked
            filepath = file_selector.selectedFiles()[0]
            # Make sure filepath contains no backslashes
            filepath = QtCore.QDir.fromNativeSeparators(filepath)
            # Update the working directory
            working_dir = file_selector.directory().canonicalPath()
        else:  # Cancel clicked
            filepath = working_dir = ''
    finally:
        del file_selector
    return filepath, working_dir

def checkFileExtension(self, filepath):
    """
    Check the filename extension of a given file.

    If the filename has no extension this method adds `.h5`
    extension to it. This is useful when a file is being created or
    saved.

    :Parameter filepath: the full path of the file.

    :Returns: the filepath with the proper extension.
    """

    if not re.search('\.(.+)$', os.path.basename(filepath)):
        ext = '.h5'
        filepath = filepath + ext
    return filepath


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
        icon = QtGui.QIcon()
        if name in large_icons:
            pixmap = QtGui.QPixmap(\
                os.path.join(ICONDIR, '22x22',u'{0}.png').format(name))
            pixmap.scaled(QtCore.QSize(22, 22), QtCore.Qt.KeepAspectRatio)
            icon.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.On)
        if name in small_icons:
            pixmap = QtGui.QPixmap(\
                os.path.join(ICONDIR,'16x16', u'{0}.png').format(name))
            icon.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.On)
        icons_dict[name] = icon

    # Add an empty iconSet for the Default button of some dialogs
    icons_dict[''] = QtGui.QIcon()

    # Application icon
    icons_dict['vitables_wm'] = QtGui.QIcon(\
        os.path.join(ICONDIR,'vitables_wm.png'))


def getIcons():
    """Return the icons dictionary to be used by the main window."""

    if not ICONS_DICT:
        large_icons = frozenset([
            # Icons for toolbars
            'document-close', 'document-new', 'document-open',
            'document-save-as', 'application-exit', 'folder-new',
            'edit-copy', 'edit-cut', 'edit-delete','edit-paste',
            'help-contents',
            'view-filter', 'delete_filters',
            # Icons for tree pane items
            'file_ro', 'file_rw', 'dbfilters', 'folder',
            'document-open-folder'])

        small_icons = frozenset([
            # Icons for menu items
            'document-close', 'document-new', 'document-open',
            'document-save-as', 'document-open-recent', 'application-exit',
            'edit-cut', 'edit-copy','edit-delete','edit-paste',
            'edit-rename',
            'folder-new',
            'view-filter', 'delete_filters',
            'configure',
            'help-about', 'help-contents',
            # Icons for tree pane items
            'image-missing', 'object', 'vlstring',
            'array', 'link_array', 'carray', 'link_carray',
            'earray', 'link_earray', 'vlarray','link_vlarray',
            'table', 'link_table',
            # Icons for node views
            'zoom-in',
            # Icons for buttons
            'dialog-cancel', 'dialog-ok'])

        createIcons(large_icons, small_icons, ICONS_DICT)

    return ICONS_DICT


def getHBIcons():
    """Return the icons dictionary to be used by the `Help Browser`."""

    if not HB_ICONS_DICT:
        large_icons = frozenset([
        # Icons for toolbar
        'go-first-view', 'go-previous-view', 'go-next-view', 'view-refresh',
        'bookmarks', 'bookmark_add', 'zoom-in', 'zoom-out',
        'edit-clear-history'])

        small_icons = frozenset([
        # Icons for menu items
        'document-open', 'application-exit',
        'zoom-in', 'zoom-out',
        'go-first-view', 'go-previous-view', 'go-next-view', 'view-refresh',
        'bookmarks', 'bookmark_add',
        # Icons for buttons
        'dialog-ok', 'dialog-cancel', 'list-remove'])

        createIcons(large_icons, small_icons, HB_ICONS_DICT)

    return HB_ICONS_DICT


def addActions(target, actions, actions_dict):
    """Add a list of QActions to a menu or a toolbar.

    This is a helper function which make easier to add QActions to a
    menu or a toolbar. Separators and submenus are also handled by this
    method.

    :Parameters:

    - `target`: the menu or toolbar where actions will be added
    - `actions`: a sequence of keywords used to get actions from a mapping
    - `actions_dict`: a mapping of actions

    """

    for action in actions:
        if action is None:
            target.addSeparator()
        elif isinstance(action, QtGui.QMenu):
            target.addMenu(action)
        else:
            target.addAction(actions_dict[action])


def formatArrayContent(content):
    """
    Nicely format the contents of a view (table widget) cell.

    Used when the cell contains a ``numpy`` array.

    :Parameter content: the ``numpy`` array contained in the view cell
    """

    if isinstance(content, numpy.string_):
        try:
            return content.decode(DEFAULT_ENCODING)
        except UnicodeDecodeError:
            pass
   
    elif isinstance(content, numpy.ndarray):
        if content.dtype.char == 'S':
            sep = ', '
            try:
                unicode_content = [('%s' % col).decode(DEFAULT_ENCODING)
                                for col in content]
                return '[%s]' % sep.join(unicode_content)
            except UnicodeDecodeError:
                pass
    ret = numpy.array2string(content, separator=',')
    return ret


def formatObjectContent(content):
    """
    Nicely format the contents of a view (table widget) cell.

    Used in `VLArrays` with `object` pseudo atoms.

    Reading a `VLArray` with `object` pseudo atom returns a list of
    Python objects. This method formats that objects as unicode strings.
    str(content) will return an `ASCII` string so it can be converted
    into a unicode string via `unicode(str(content), 'latin-1')`.
    This will fail only if content is a unicode string with some ordinal
    not in `range(128)` (raising a UnicodeEncodeError) but no problem
    because in that case content is already a unicode string and will be
    returned as is. So this method always returns the read object as a
    unicode string.

    :Parameter content: the Python list contained in the view cell
    """

    try:
        text = unicode(str(content), 'latin-1')
    except UnicodeEncodeError:
        text = content
    return text


def formatStringContent(content):
    """
    Nicely format the contents of a view (table widget) cell.

    Used in `VLArrays` with `vlstring` or `vlunicode` pseudo atoms.
    If the pseudo atom is `vlstring` the method return a string. If
    the pseudo atom is `vlunicode` then a unicode string is returned.

    :Parameter content: the Python list contained in the view cell
    """

    return content


def formatExceptionInfo(limit=1):
    """
    Format conveniently the catched exceptions.

    Takes the three-element tuple returned by ``sys.exc_info()`` and transforms
    each element into a more convenient form.

    :Parameter limit: the number of stack trace entries to be printed
    """

    print(u'\n{0}\n'.format(traceback.format_exc(limit)))

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
    return home


def forwardPath(path):
    """Replace backslashes with slashes in a given path.

    :Parameter path: the path being transformed
    """

    while path.count(chr(92)):
        path = path.replace(chr(92), '/')
    return path


def questionBox(title='', text='', info='', detail='', buttons_def=''):
    """The value returned by a question message box with customised buttons.

    :Parameters:

    - `title`: the window title
    - `text`: the primary text
    - `info`: additional informative text
    - `detail`: a detailed text
    - `buttons_def`: mapping with buttons definitions

    """

    qmbox = QtGui.QMessageBox()
    qmbox.setIcon(QtGui.QMessageBox.Question)
    qmbox.setWindowTitle(title)
    qmbox.setText(text)
    if info:
        qmbox.setInformativeText(info)
    if detail:
        qmbox.setDetailedText(detail)
    qmbox.setDefaultButton(QtGui.QMessageBox.NoButton)

    buttons = {}
    for name, (text, role) in buttons_def.items():
        buttons[name] = qmbox.addButton(text, role)

    qmbox.exec_()

    # Find out which button has been returned
    for name in buttons.keys():
        if buttons[name] == qmbox.clickedButton():
            return name
    return


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
        dialog = renamedlg.RenameDlg(nodename, pattern, info)
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


def getLicense():
    """The ``ViTables`` license in Rich Text format."""

    input_file = QtCore.QFile(os.path.join(DOCDIR, 'LICENSE.html'))
    input_file.open(QtCore.QIODevice.ReadOnly)
    stream = QtCore.QTextStream(input_file)
    license_text = stream.readAll()
    input_file.close()

    return license_text
