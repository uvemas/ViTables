#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
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

"""This module provides a console (named Logger) to ``ViTables``.

Warning and error messages delivered to users by the application are
displayed in this console. Also some messages about the result of the
operations requested by users are shown in the console. This is a read-only
console, its main purpose is to feed users with important information
regarding its working session (so it is called Logger). Users can't enter
commands in the Logger.

    :Parameter parent: the parent widget of the Logger
"""

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

import vitables.utils

__docformat__ = 'restructuredtext'

translate = QtWidgets.QApplication.translate


class Logger(QtWidgets.QTextEdit):
    """
    Console that receives all informational application messages.

    All messages delivered by application to user are displayed in the
    Logger. This messages include the status of user requested
    operations, the result of this operations, and also error messages.
    This is possible because the class reimplement the write() method,
    so it can be used to catch both, ``sys.stdout`` and ``sys.stderr``, just by
    redirecting them to an instance of this class.
    """

    def __init__(self, parent=None):
        """Create the Logger widget and configure it.
        """

        super(Logger, self).__init__(parent)
        self.setAcceptRichText(True)
        self.setReadOnly(1)
        self.setMinimumHeight(50)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setWhatsThis(
            translate(
                'Logger',
                """<qt>
                <h3>The Logger</h3>
                This screen region is a read-only console that logs the result
                of operations requested by the user.
                <p>Also execution errors and exceptions are logged in this
                console.</qt>""",
                'WhatsThis help for the logger'))

        self.setStyleSheet("background-color: #ffffff")

        # The frame especification
        self.frame_style = {'shape': self.frameShape(),
                            'shadow': self.frameShadow(),
                            'lwidth': self.lineWidth()}

        # The context menu
        self.context_menu = self.setupContextMenu()

        # Connect signals to slots
        self.customContextMenuRequested.connect(self.popupCustomContextMenu)

    def write(self, text):
        """
        Catch the messages sent to the standard output and the standard error.

        The caught messages are displayed in the `Logger` using this method.

        The implementation is done via QTextEdit.append() method because it
        adds a new paragraph at the end of the console content so even if
        the user clicks somewhere in the console or there is selected text, the
        new text will not mess the console.

        :Parameter text: the text being written
        """

        current_color = self.textColor()
        if text in ['\n', '\r\n']:
            return
        if text.startswith('\nError: '):
            self.setTextColor(QtGui.QColor('red'))
        elif text.startswith('\nWarning: '):
            self.setTextColor(QtGui.QColor(243, 137, 8))
        self.append(text)
        # Reset the text color
        self.setTextColor(current_color)

    def flush(self):
        """
        Stopgap function to allow use of this class with logging.StreamHandler.
        """
        pass

    def setupContextMenu(self):
        """Create a customised context menu."""

        # Make the menu
        edit_menu = QtWidgets.QMenu(self)
        edit_menu.setObjectName('logger_context_menu')

        # QtGui.Qpalette.Window constant is 10
        edit_menu.setStyleSheet("background-color: {0}".format(10))

        self.copy_action = QtWidgets.QAction(
            translate('Logger', "&Copy", 'Logger menu entry'), self,
            shortcut=QtGui.QKeySequence.Copy, triggered=self.parent().makeCopy,
            statusTip=translate('Logger', 'Copy selected text to clipboard',
                                'Status bar text for the logger context menu ->'
                                ' Copy action'))
        self.copy_action.setObjectName('logger_copy_action')
        edit_menu.addAction(self.copy_action)

        self.clear_action = QtWidgets.QAction(
            translate('Logger', "Cl&ear All", 'Logger menu entry'), self,
            triggered=self.clear,
            statusTip=translate('Logger', 'Empty the Logger',
                                'Status bar text for the logger context menu ->'
                                ' Clear action'))
        self.clear_action.setObjectName('logger_clear_action')
        edit_menu.addAction(self.clear_action)
        edit_menu.addSeparator()

        self.select_action = QtWidgets.QAction(
            translate('Logger', "Select &All", 'Logger menu entry'), self,
            triggered=self.selectAll,
            statusTip=translate('Logger', 'Select the whole Logger contents',
                                'Status bar text for the logger context menu ->'
                                ' Select All'))
        self.select_action.setObjectName('logger_select_action')
        edit_menu.addAction(self.select_action)

        edit_menu.aboutToShow.connect(self.updateContextMenu)
        return edit_menu

    def popupCustomContextMenu(self, pos):
        """
        Popup the context logger menu.

        :Parameter pos: the local position at which the menu will popup
        """
        self.context_menu.popup(self.mapToGlobal(pos))

    def updateContextMenu(self):
        """Update items availability when the menu is about to be shown."""

        # Copy is enabled when there is some selected text
        cursor = self.textCursor()
        self.copy_action.setEnabled(cursor.hasSelection())

        # Clear All and Select All are enabled when there is some text
        has_content = not self.document().isEmpty()
        self.clear_action.setEnabled(has_content)
        self.select_action.setEnabled(has_content)

    def focusInEvent(self, event):
        """Specialised handler for focus events.

        Repaint differently the `Logger` frame when it gets the keyboard focus
        so that users can realize easily about this focus change.

        :Parameter event: the event being processed
        """

        self.setLineWidth(2)
        self.setFrameShape(QtWidgets.QFrame.Panel)
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        QtWidgets.QTextEdit.focusInEvent(self, event)

    def focusOutEvent(self, event):
        """Specialised handler for focus events.

        Repaint differently the `Logger` frame when it looses the keyboard
        focus so that users can realize easily about this focus change.

        :Parameter event: the event being processed
        """

        self.setLineWidth(self.frame_style['lwidth'])
        self.setFrameShape(self.frame_style['shape'])
        self.setFrameShadow(self.frame_style['shadow'])
        QtWidgets.QTextEdit.focusOutEvent(self, event)
