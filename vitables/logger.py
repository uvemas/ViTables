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

"""This module provides a console (named Logger) to ``ViTables``.

Warning and error messages delivered to users by the application are
displayed in this console. Also some messages about the result of the
operations requested by users are shown in the console. This is a read-only
console, its main purpose is to feed users with important information
regarding its working session (so it is called Logger). Users can't enter
commands in the Logger.

    :Parameter parent: the parent widget of the Logger
"""

__docformat__ = 'restructuredtext'

from PyQt4 import QtCore
from PyQt4 import QtGui


import vitables.utils

translate = QtGui.QApplication.translate


class Logger(QtGui.QTextEdit):
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
        self.setWhatsThis(translate('Logger',
            """<qt>
            <h3>The Logger</h3>
            This is the screen region where info about the currently
            selected item is displayed. It also logs the result of all
            operations requested by the user.
            <p>Also execution errors and exceptions are logged in the
            console.
            </qt>""",
            'WhatsThis help for the logger'))

        self.setStyleSheet("background-color: #ffffff")

        # The frame especification
        self.frame_style = {'shape': self.frameShape(),
            'shadow': self.frameShadow(),
            'lwidth': self.lineWidth(),
            'foreground': self.palette().color(QtGui.QPalette.Active,
                QtGui.QPalette.WindowText)}

        # Connect signals to slots
        self.customContextMenuRequested.connect(self.createCustomContextMenu)


    def write(self, text):
        """
        Catch the messages sent to the standard output and the standard error.

        The caught messages are displayed in the `Logger` using this method.

        The implementation is done via QTextEdit.append method because
        this method adds the text at the end of the console so, even if
        the user clicks somewhere in the console or there is selected
        text, the printed text will not mess the console.

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
        # Warning! Append() doesn't change the cursor position
        # Because we want to reset the current color **at the end** of
        # the console in order to give the proper color to new messages
        # we must update the cursor position **before** the current
        # color is reset
        self.moveCursor(QtGui.QTextCursor.EndOfLine)
        self.setTextColor(current_color)


    def flush(self):
        """
        Stopgap function to allow use of this class with logging.StreamHandler.
        """
        pass


    def createCustomContextMenu(self, pos):
        """
        Popup the context logger menu.

        :Parameter pos: the local position at which the menu will popup
        """

        vtapp = vitables.utils.getVTApp()
        # Make the menu
        edit_menu = QtGui.QMenu(self)
        # QtGui.Qpalette.Window constant is 10
        edit_menu.setStyleSheet(u"background-color: {0}".format(10))

        self.copy_action = QtGui.QAction(
            translate('Logger', "&Copy", 'Logger menu entry'), self,
            shortcut=QtGui.QKeySequence.Copy, triggered=vtapp.gui.makeCopy,
            statusTip=translate('Logger', 'Copy selected text to clipboard',
                'Status bar text for the logger context menu -> Copy action'))
        edit_menu.addAction(self.copy_action)

        self.clear_action = QtGui.QAction(
            translate('Logger', "Cl&ear All", 'Logger menu entry'), self,
            triggered=self.clear,
            statusTip=translate('Logger', 'Empty the Logger',
                'Status bar text for the logger context menu -> Clear action'))
        edit_menu.addAction(self.clear_action)
        edit_menu.addSeparator()

        self.select_action = QtGui.QAction(
            translate('Logger', "Select &All", 'Logger menu entry'), self,
            triggered=self.selectAll,
            statusTip=translate('Logger', 'Select the whole Logger contents',
                'Status bar text for the logger context menu -> Select All'))
        edit_menu.addAction(self.select_action)

        edit_menu.aboutToShow.connect(self.updateEditMenu)
        edit_menu.popup(self.mapToGlobal(pos))


    def updateEditMenu(self):
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
        self.setFrameStyle(QtGui.QFrame.Panel|QtGui.QFrame.Plain)
        pal = self.palette()
        pal.setColor(QtGui.QPalette.Active, QtGui.QPalette.WindowText,
            QtCore.Qt.darkBlue)
        QtGui.QTextEdit.focusInEvent(self, event)


    def focusOutEvent(self, event):
        """Specialised handler for focus events.

        Repaint differently the `Logger` frame when it looses the keyboard
        focus so that users can realize easily about this focus change.

        :Parameter event: the event being processed
        """

        self.setLineWidth(self.frame_style['lwidth'])
        self.setFrameShape(self.frame_style['shape'])
        self.setFrameShadow(self.frame_style['shadow'])
        pal = self.palette()
        pal.setColor(QtGui.QPalette.Active, QtGui.QPalette.WindowText,
            self.frame_style['foreground'])
        QtGui.QTextEdit.focusOutEvent(self, event)

if __name__ == '__main__':
    import sys
    APP = QtGui.QApplication(sys.argv)
    LOGGER = Logger()
    LOGGER.show()
    # Redirect standard output and standard error to the Logger instance
    sys.stdout = LOGGER
    sys.stderr = LOGGER
    print('Hola mundo!')
    print('\nError: El viatger del crepuscle')
    print('\nWarning: Adolf Piquer')
    print('Adeu!')
    APP.exec_()
